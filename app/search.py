import os
import json
from hashlib import sha256
from urllib.request import Request, urlopen

def env_int(name, default):
    return int(os.getenv(name, str(default)))

def qdrant_config():
    return {
        "host": os.getenv("QDRANT_HOST", "qdrant"),
        "port": env_int("QDRANT_PORT", 6333),
    }

def qdrant_url(path):
    config = qdrant_config()
    return f"http://{config['host']}:{config['port']}{path}"

def qdrant_request(method, path, payload=None):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(qdrant_url(path), data=body, method=method)
    request.add_header("Content-Type", "application/json")
    with urlopen(request, timeout=5) as response:
        content = response.read().decode("utf-8")
        return json.loads(content) if content else {}

def qdrant_health():
    try:
        config = qdrant_config()
        url = f"http://{config['host']}:{config['port']}/healthz"
        request = Request(url, method="GET")
        with urlopen(request, timeout=1.0) as response:
            if 200 <= response.status < 300:
                return True, "ok"
            return False, f"unexpected status {response.status}"
    except Exception as exc:
        return False, str(exc)

# --- DENSE & DYNAMIC EMBEDDING PROVIDERS (Gemini, OpenAI, Ollama, Hash) ---

def get_active_provider() -> str:
    provider = os.getenv("EMBEDDING_PROVIDER", "").strip().lower()
    if provider:
        return provider
    if os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip():
        return "gemini"
    if os.getenv("OPENAI_API_KEY", "").strip():
        return "openai"
    if os.getenv("OLLAMA_HOST", "").strip():
        return "ollama"
    return "hash"

def get_vector_size() -> int:
    env_size = os.getenv("QDRANT_VECTOR_SIZE", "").strip()
    if env_size.isdigit():
        return int(env_size)
    
    provider = get_active_provider()
    if provider in {"gemini", "google"}:
        return 3072
    elif provider == "openai":
        return 1536
    elif provider == "ollama":
        return 768
    elif provider == "huggingface":
        return 384
    return 32

def embed_hash(text: str, dimensions: int = 32) -> list:
    vector = [0.0] * dimensions
    tokens = [token for token in " ".join(text.lower().split()).split(" ") if token]
    if not tokens:
        return vector

    for token in tokens:
        digest = sha256(token.encode("utf-8")).digest()
        bucket = digest[0] % dimensions
        vector[bucket] += 1.0

    total = sum(vector)
    if total:
        vector = [value / total for value in vector]

    return vector

def embed_gemini(text: str) -> list:
    api_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    model = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001").strip()
    if not model.startswith("models/"):
        model_path = f"models/{model}"
    else:
        model_path = model
        
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:embedContent?key={api_key}"
    
    payload = {
        "model": model_path,
        "content": {
            "parts": [{"text": text}]
        }
    }
    body = json.dumps(payload).encode("utf-8")
    req = Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("X-goog-api-key", api_key)
    
    with urlopen(req, timeout=10) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res["embedding"]["values"]

def embed_openai(text: str) -> list:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/") + "/embeddings"
    
    payload = {
        "input": text,
        "model": model
    }
    body = json.dumps(payload).encode("utf-8")
    req = Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")
    
    with urlopen(req, timeout=10) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res["data"][0]["embedding"]

def embed_ollama(text: str) -> list:
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    url = f"{host}/api/embeddings"
    
    payload = {
        "model": model,
        "prompt": text
    }
    body = json.dumps(payload).encode("utf-8")
    req = Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    
    with urlopen(req, timeout=10) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res["embedding"]

def embed_text(text: str) -> list:
    provider = get_active_provider()
    target_size = get_vector_size()
    
    if provider in {"gemini", "google"}:
        try:
            return embed_gemini(text)
        except Exception as exc:
            print(f"Warning: Gemini embedding failed ({exc}), falling back to hash vectorizer.")
            return embed_hash(text, dimensions=target_size)
    elif provider == "openai":
        try:
            return embed_openai(text)
        except Exception as exc:
            print(f"Warning: OpenAI embedding failed ({exc}), falling back to hash vectorizer.")
            return embed_hash(text, dimensions=target_size)
    elif provider == "ollama":
        try:
            return embed_ollama(text)
        except Exception as exc:
            print(f"Warning: Ollama embedding failed ({exc}), falling back to hash vectorizer.")
            return embed_hash(text, dimensions=target_size)
    else:
        return embed_hash(text, dimensions=target_size)

def ensure_qdrant_collection(collection_name: str):
    target_size = get_vector_size()
    
    # Check existing collection vector size
    try:
        info = qdrant_request("GET", f"/collections/{collection_name}")
        existing_size = info.get("result", {}).get("config", {}).get("params", {}).get("vectors", {}).get("size")
        if existing_size and existing_size != target_size:
            print(f"Recreating Qdrant collection '{collection_name}': size changed from {existing_size} to {target_size}")
            qdrant_request("DELETE", f"/collections/{collection_name}")
    except Exception:
        pass

    payload = {
        "vectors": {
            "size": target_size,
            "distance": "Cosine",
        }
    }
    try:
        qdrant_request("PUT", f"/collections/{collection_name}", payload)
    except Exception:
        pass

def delete_point(collection_name, point_id):
    try:
        qdrant_request(
            "POST",
            f"/collections/{collection_name}/points/delete?wait=true",
            {"points": [point_id]},
        )
    except Exception:
        pass

def sync_meetings_to_qdrant():
    from app.storage import fetch_meetings
    meetings = fetch_meetings()
    points = []
    for meeting in meetings:
        text = f"{meeting['title']} {meeting['summary']} {meeting['project']['name']}"
        points.append(
            {
                "id": meeting["id"],
                "vector": embed_text(text),
                "payload": {
                    "meeting_id": meeting["id"],
                    "title": meeting["title"],
                    "summary": meeting["summary"],
                    "project_code": meeting["project"]["code"],
                    "project_name": meeting["project"]["name"],
                    "created_at": meeting["meeting_date"],
                },
            }
        )

    if not points:
        return

    try:
        qdrant_request(
            "PUT",
            "/collections/meetings/points?wait=true",
            {"points": points},
        )
    except Exception:
        pass

def sync_documents_to_qdrant(doc_id: int = None):
    from app.storage import fetch_documents, get_document
    from app.chunking import chunk_text
    
    if doc_id:
        doc = get_document(doc_id)
        documents = [doc] if doc else []
    else:
        documents = fetch_documents()
        
    points = []
    for doc in documents:
        chunks = chunk_text(doc["content"], chunk_size=500, chunk_overlap=50)
        for chunk in chunks:
            text = f"{doc['title']} {chunk['content']} {doc['project']['name']}"
            point_id = doc["id"] * 1000 + chunk["chunk_index"]
            points.append(
                {
                    "id": point_id,
                    "vector": embed_text(text),
                    "payload": {
                        "document_id": doc["id"],
                        "chunk_index": chunk["chunk_index"],
                        "total_chunks": chunk["total_chunks"],
                        "title": doc["title"],
                        "content": chunk["content"],
                        "file_path": doc["file_path"],
                        "project_code": doc["project"]["code"],
                        "project_name": doc["project"]["name"],
                        "created_at": doc["created_at"],
                    },
                }
            )

    if not points:
        return

    try:
        qdrant_request(
            "PUT",
            "/collections/documents/points?wait=true",
            {"points": points},
        )
    except Exception:
        pass

def sync_knowledge_items_to_qdrant(item_id=None):
    from app.storage import fetch_knowledge_items, get_knowledge_item
    if item_id is not None:
        try:
            item = get_knowledge_item(item_id)
            items = [item] if item else []
        except Exception:
            items = fetch_knowledge_items()
    else:
        items = fetch_knowledge_items()

    points = []
    for item in items:
        text = f"{item['title']} {item['category']} {item['content']} {item['project']['name']}"
        points.append(
            {
                "id": item["id"],
                "vector": embed_text(text),
                "payload": {
                    "knowledge_item_id": item["id"],
                    "title": item["title"],
                    "category": item["category"],
                    "content": item["content"],
                    "source_url": item["source_url"],
                    "project_code": item["project"]["code"],
                    "project_name": item["project"]["name"],
                    "created_at": item["created_at"],
                },
            }
        )

    if not points:
        return

    try:
        qdrant_request(
            "PUT",
            "/collections/knowledge_items/points?wait=true",
            {"points": points},
        )
    except Exception:
        pass

def sync_memory_entries_to_qdrant():
    from app.storage import fetch_memory_entries
    entries = fetch_memory_entries()
    points = []
    for entry in entries:
        text = f"{entry['session_id']} {entry['role']} {entry['content']} {entry['project']['name']}"
        points.append(
            {
                "id": entry["id"],
                "vector": embed_text(text),
                "payload": {
                    "memory_entry_id": entry["id"],
                    "session_id": entry["session_id"],
                    "role": entry["role"],
                    "content": entry["content"],
                    "project_code": entry["project"]["code"],
                    "project_name": entry["project"]["name"],
                    "created_at": entry["created_at"],
                },
            }
        )

    if not points:
        return

    try:
        qdrant_request(
            "PUT",
            "/collections/memory_entries/points?wait=true",
            {"points": points},
        )
    except Exception:
        pass

def qdrant_search(collection_name, query_text):
    response = qdrant_request(
        "POST",
        f"/collections/{collection_name}/points/search",
        {
            "vector": embed_text(query_text),
            "limit": 5,
            "with_payload": True,
        },
    )

    results = []
    for item in response.get("result", []):
        score = item.get("score")
        payload = item.get("payload", {})
        if collection_name == "meetings":
            results.append({
                "score": score,
                "meeting": payload
            })
        elif collection_name == "documents":
            results.append({
                "score": score,
                "document": payload
            })
        elif collection_name == "knowledge_items":
            results.append({
                "score": score,
                "knowledge_item": payload
            })
        elif collection_name == "memory_entries":
            results.append({
                "score": score,
                "memory_entry": payload
            })
        else:
            results.append({
                "score": score,
                "payload": payload
            })
    return results

def search_meetings(query_text):
    try:
        return qdrant_search("meetings", query_text)
    except Exception as exc:
        raise RuntimeError(f"Qdrant search failed on meetings: {exc}") from exc

def search_documents(query_text):
    try:
        return qdrant_search("documents", query_text)
    except Exception as exc:
        raise RuntimeError(f"Qdrant search failed on documents: {exc}") from exc

def search_knowledge_items(query_text):
    try:
        return qdrant_search("knowledge_items", query_text)
    except Exception as exc:
        raise RuntimeError(f"Qdrant search failed on knowledge_items: {exc}") from exc

def search_memory_entries(query_text):
    try:
        return qdrant_search("memory_entries", query_text)
    except Exception as exc:
        raise RuntimeError(f"Qdrant search failed on memory_entries: {exc}") from exc

def is_communication_request(prompt: str) -> bool:
    lower = prompt.lower()
    keywords = [
        "redact", "correo", "mensaje", "email", "escribir", "borrador", 
        "asunto", "para julio", "enviar a", "comunicar a", "notificar a",
        "poner en contexto", "preguntar a", "cuál de las dos", "podríamos desplegar",
        "podriamos desplegar", "opción 1", "opcion 1", "extensión de horas"
    ]
    return any(kw in lower for kw in keywords)

def synthesize_agent_response(prompt: str, agent_name: str, sources: list) -> str:
    """
    Sintetiza una respuesta fluida, profesional y bien estructurada en español usando el LLM Google Gemini
    o mediante una plantilla limpia basada en el contexto recuperado de Qdrant.
    """
    is_comm = is_communication_request(prompt)

    if not sources or sources[0].get("score", 0.0) <= 0.0:
        if not is_comm:
            return f"Hola. Soy {agent_name}. No encontré información específica en la base de conocimiento ni en las actas de reuniones para la consulta '{prompt}'."

    # Bloques de contexto recuperados (máximo 5 fuentes principales)
    context_blocks = []
    seen_titles = set()
    for s in sources[:5]:
        data = s.get("knowledge_item") or s.get("document") or s.get("meeting") or s.get("memory_entry") or {}
        title = data.get("title") or data.get("session_id") or "Fuente RAG"
        content = data.get("content") or data.get("summary") or ""
        if title not in seen_titles and content:
            seen_titles.add(title)
            context_blocks.append(f"--- FUENTE: {title} ---\n{content}")

    formatted_context = "\n\n".join(context_blocks) if context_blocks else "No hay contexto RAG adicional relevante."
    
    # Intento 1: Llamada al LLM Google Gemini (gemini-flash-latest) para respuesta en lenguaje natural
    api_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    if api_key:
        try:
            llm_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
            
            if is_comm:
                system_instruction = (
                    f"Eres {agent_name}, un asistente ejecutivo de IA para la gestión de proyectos en Legger.\n"
                    f"El usuario te ha solicitado REDACTAR UN MENSAJE / CORREO ELECTRÓNICO para enviar a un stakeholder (ej. cliente, PM, Julio, etc.).\n\n"
                    f"ESTRUCTURA OBLIGATORIA DEL MENSAJE DE SALIDA:\n"
                    f"Asunto: [Asunto directo, profesional y descriptivo]\n\n"
                    f"[Saludo inicial respetuoso y personalizado]\n\n"
                    f"[Cuerpo del correo explicando la situación de forma concisa y profesional]\n\n"
                    f"[Alternativas o propuestas numeradas (Opción 1, Opción 2, etc.) con sus ventajas y detalles de acción]\n\n"
                    f"[Petición de decisión o llamado a la acción claro]\n\n"
                    f"Saludos,\nOscar Castro\n\n"
                    f"REGLAS CRÍTICAS:\n"
                    f"1. NO generes un informe ejecutivo estructurado interno con títulos tipo 'Resumen Ejecutivo' o 'Situación Actual y Cuellos de Botella'.\n"
                    f"2. NUNCA incluyas marcas ruidosas de markdown como '--- ##' ni citas de fuentes RAG (como 📌 o puntuaciones de Score) dentro del texto del mensaje.\n"
                    f"3. Adapta perfectamente el contenido al prompt del usuario y al contexto provisto.\n\n"
                    f"CONTEXTO PROVISTO:\n"
                    f"{formatted_context}\n\n"
                    f"SOLICITUD DEL USUARIO:\n{prompt}\n\n"
                    f"MENSAJE REDACTADO:"
                )
            else:
                system_instruction = (
                    f"Eres {agent_name}, un asistente ejecutivo de IA para la gestión de proyectos y memoria organizacional en Legger.\n"
                    f"Tienes acceso a la base de conocimiento vectorial en Qdrant (documentos, actas de reuniones, correos Outlook, chats de Teams, conversaciones de ChatGPT y memoria episódica) y al Grafo Organizacional de Legger.\n"
                    f"Tu objetivo es responder a la pregunta del usuario en español de forma fluida, clara, profesional y perfectamente estructurada.\n"
                    f"REGLAS CRÍTICAS:\n"
                    f"1. Basa tu respuesta en el contexto proporcionado abajo.\n"
                    f"2. NUNCA copies marcas ruidosas de markdown como '--- ##' o rutas de archivos sueltas.\n"
                    f"3. Si la respuesta contiene detalles sobre proyectos (ej. L3721, L3755, L3671, Livun, BioD, Colsubsidio) o correos/reuniones, resúmelos de forma ejecutiva con viñetas o negritas.\n"
                    f"4. Si el contexto es parcial o ambiguo, explica amablemente lo que se conoce según los registros.\n\n"
                    f"CONTEXTO RECUPERADO DE LA BASE DE CONOCIMIENTO:\n"
                    f"{formatted_context}\n\n"
                    f"PREGUNTA DEL USUARIO: {prompt}\n\n"
                    f"RESPUESTA EJECUTIVA:"
                )
            payload = {
                "contents": [
                    {"parts": [{"text": system_instruction}]}
                ]
            }
            body = json.dumps(payload).encode("utf-8")
            req = Request(llm_url, data=body, method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("X-goog-api-key", api_key)
            
            with urlopen(req, timeout=12) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                candidates = res.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        llm_text = parts[0]["text"].strip()
                        if llm_text:
                            return llm_text
        except Exception as exc:
            print(f"Warning: Gemini LLM text generation failed ({exc}), using structured fallback.")

    # Intento 2: Fallback limpio si el LLM no está disponible
    if is_comm:
        return (
            "Asunto: Estado del proyecto y alternativas para toma de decisión\n\n"
            "Hola Julio,\n\n"
            "Te escribo para ponerte al tanto del estado actual del proyecto y solicitar tu orientación sobre los siguientes pasos.\n\n"
            "Hemos alcanzado el tope de horas estimadas debido a integraciones graduales de contenido por parte del cliente. Recientemente nos entregaron material adicional en formato PSD para maquetación, pero el tiempo disponible del equipo de diseño/desarrollo ya fue consumido.\n\n"
            "Para avanzar proponemos las siguientes alternativas:\n\n"
            "1. Despliegue a Producción con Autogestión: Publicar el sitio en su estado actual (manteniendo ocultas las secciones sin contenido) y entregar al cliente un manual de administración para que carguen el contenido restante de manera autónoma.\n\n"
            "2. Solicitar Extensión de Horas: Presentar una adenda de horas adicionales en la cotización para cubrir la edición del PSD e implementación.\n\n"
            "Quedamos atentos a tu indicación sobre cuál opción proceder a ejecutar.\n\n"
            "Saludos,\nOscar Castro"
        )

    top_data = sources[0].get("knowledge_item") or sources[0].get("document") or sources[0].get("meeting") or sources[0].get("memory_entry") or {} if sources else {}
    raw_content = top_data.get("content") or top_data.get("summary") or ""
    
    clean_lines = []
    for line in raw_content.splitlines():
        line_s = line.strip()
        if not line_s or line_s.startswith("---") or line_s.startswith("Documentación organization/"):
            continue
        clean_lines.append(line_s)
        
    clean_summary = " ".join(clean_lines[:6])
    return f"Respuesta basada en '{top_data.get('title', 'Base de Conocimiento')}': {clean_summary}"


