import os
import json
import urllib.request

BASE_URL = "http://127.0.0.1:8080"

def main():
    print("=== TESTING CHATGPT EXPORT IMPORTER ENDPOINT (/api/v1/integrations/chatgpt/import) ===")

    # 1. Create a sample conversations.json representing a ChatGPT export
    sample_conversations = [
        {
            "title": "Arquitectura de Microservicios para Colsubsidio CIAM",
            "create_time": 1774500000,
            "mapping": {
                "node_1": {
                    "message": {
                        "author": {"role": "user"},
                        "content": {"parts": ["¿Cuál es la mejor estrategia de autenticación OAuth2 para Colsubsidio CIAM?"]}
                    }
                },
                "node_2": {
                    "message": {
                        "author": {"role": "assistant"},
                        "content": {"parts": ["La mejor estrategia recomendada para Colsubsidio CIAM es implementar PKCE (Proof Key for Code Exchange) con Azure AD B2C y tokens JWT firmados con RS256."]}
                    }
                }
            }
        },
        {
            "title": "Configuración de Asistentes Virtuales BioD",
            "create_time": 1774510000,
            "mapping": {
                "node_1": {
                    "message": {
                        "author": {"role": "user"},
                        "content": {"parts": ["¿Cómo integramos los asistentes virtuales de BioD con Qdrant?"]}
                    }
                },
                "node_2": {
                    "message": {
                        "author": {"role": "assistant"},
                        "content": {"parts": ["Para conectar BioD con Qdrant, configuramos la colección 'biod_memory' utilizando Gemini 3072-dimensional dense embeddings para búsqueda en milisegundos."]}
                    }
                }
            }
        }
    ]

    test_file_path = "test_conversations.json"
    with open(test_file_path, "w", encoding="utf-8") as f:
        json.dump(sample_conversations, f, ensure_ascii=False, indent=2)

    # 2. Upload and import via multipart/form-data POST
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    with open(test_file_path, "rb") as f:
        file_bytes = f.read()

    body = []
    body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"project_id\"\r\n\r\n1\r\n".encode("utf-8"))
    body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{test_file_path}\"\r\nContent-Type: application/json\r\n\r\n".encode("utf-8"))
    body.append(file_bytes)
    body.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    payload_bytes = b"".join(body)

    url = f"{BASE_URL}/api/v1/integrations/chatgpt/import"
    req = urllib.request.Request(
        url,
        data=payload_bytes,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "X-Agent-ID": "test-chatgpt-importer"
        },
        method="POST"
    )

    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print("[OK] Import Status:", res["status"])
        print("[OK] Total ChatGPT Threads Imported & Vectorized:", res["total_imported"])
        for item in res.get("items", []):
            print("  - Title:", item["title"])

    # Clean up test file
    if os.path.exists(test_file_path):
        os.remove(test_file_path)

    # 3. Test RAG Agent retrieval of imported ChatGPT threads
    print("\n--- Testing RAG retrieval of imported ChatGPT conversations ---")
    query_payload = json.dumps({"prompt": "¿Qué estrategia de autenticación se recomendó para Colsubsidio CIAM?"}).encode("utf-8")
    req_rag = urllib.request.Request(
        f"{BASE_URL}/api/v1/agents/docs-agent/run",
        data=query_payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req_rag) as resp_rag:
        res_rag = json.loads(resp_rag.read().decode("utf-8"))
        print("\n--- Gemini LLM Answer ---\n", res_rag["answer"])

    print("\n=== CHATGPT EXPORT IMPORTER TEST COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
