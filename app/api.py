import os
import socket
from typing import List, Optional
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException, Query, status, Response, Request, Depends, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Storage operations
from app.storage import (
    postgres_health,
    fetch_clients, get_client, create_client, update_client, delete_client,
    fetch_projects, get_project, create_project, update_project, delete_project,
    fetch_meetings, get_meeting, create_meeting, update_meeting, delete_meeting,
    fetch_documents, get_document, create_document, update_document, delete_document,
    fetch_tasks, get_task, create_task, update_task, delete_task,
    fetch_knowledge_items, get_knowledge_item, create_knowledge_item, update_knowledge_item, delete_knowledge_item,
    fetch_memory_entries, get_memory_entry, create_memory_entry, update_memory_entry, delete_memory_entry,
    create_audit_event, fetch_audit_events
)

# Search operations
from app.search import (
    qdrant_health,
    search_meetings,
    search_documents,
    search_knowledge_items,
    search_memory_entries
)

def env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))

def tcp_check(host: str, port: int, timeout: float = 1.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, "ok"
    except OSError as exc:
        return False, str(exc)

def dependency_status():
    postgres_ok, postgres_detail = postgres_health()
    redis_ok, redis_detail = tcp_check(
        os.getenv("REDIS_HOST", "redis"),
        env_int("REDIS_PORT", 6379),
    )
    qdrant_ok, qdrant_detail = qdrant_health()

    return {
        "postgres": {
            "ok": postgres_ok,
            "host": os.getenv("POSTGRES_HOST", "postgres"),
            "port": env_int("POSTGRES_PORT", 5432),
            "detail": postgres_detail,
        },
        "redis": {
            "ok": redis_ok,
            "host": os.getenv("REDIS_HOST", "redis"),
            "port": env_int("REDIS_PORT", 6379),
            "detail": redis_detail,
        },
        "qdrant": {
            "ok": qdrant_ok,
            "host": os.getenv("QDRANT_HOST", "qdrant"),
            "port": env_int("QDRANT_PORT", 6333),
            "detail": qdrant_detail if isinstance(qdrant_detail, str) else ("ok" if qdrant_ok else "error"),
        },
    }

# --- PYDANTIC SCHEMAS ---

class ClientCreate(BaseModel):
    code: str = Field(..., example="CL-002")
    name: str = Field(..., example="Acme Corp")

class ProjectCreate(BaseModel):
    client_id: Optional[int] = Field(None, example=1)
    code: str = Field(..., example="PROJ-002")
    name: str = Field(..., example="Acme Refactor")
    status: str = Field("planned", example="planned")

class MeetingCreate(BaseModel):
    project_id: int = Field(..., example=1)
    title: str = Field(..., example="Sprint Planning")
    summary: str = Field(..., example="Discussed sprint goals and tasks.")
    meeting_date: Optional[str] = Field(None, example="2026-07-27T10:00:00Z")

class DocumentCreate(BaseModel):
    project_id: int = Field(..., example=1)
    title: str = Field(..., example="API Guidelines")
    content: str = Field(..., example="Coding and REST API standards.")
    file_path: Optional[str] = Field(None, example="docs/api.md")

class DocumentIngestRequest(BaseModel):
    project_id: int = Field(..., example=1)
    title: str = Field(..., example="System Architecture Manual")
    content: str = Field(..., example="Full text content of system architecture...")
    file_path: Optional[str] = Field(None, example="docs/architecture.md")
    chunk_size: Optional[int] = Field(500, example=500)
    chunk_overlap: Optional[int] = Field(50, example=50)

class TaskCreate(BaseModel):
    project_id: int = Field(..., example=1)
    title: str = Field(..., example="Implement OpenClaw runner")
    description: Optional[str] = Field(None, example="Connect tools and execute prompts")
    assigned_agent_id: Optional[str] = Field(None, example="docs-agent")
    status: str = Field("pending", example="pending")

class KnowledgeItemCreate(BaseModel):
    project_id: int = Field(..., example=1)
    title: str = Field(..., example="Decision ADR-001")
    content: str = Field(..., example="Use FastAPI and Qdrant for RAG memory.")
    category: str = Field("architecture", example="architecture")
    source_url: Optional[str] = Field(None, example="https://docs.oscar.ai/adr-001")

class MemoryEntryCreate(BaseModel):
    project_id: int = Field(..., example=1)
    content: str = Field(..., example="User asked about project status.")
    session_id: str = Field("default", example="session-001")
    role: str = Field("user", example="user")

class GitHubSyncRequest(BaseModel):
    project_id: int = Field(..., example=1)
    repo: str = Field("legger/platform-l3721", example="legger/platform-l3721")

class AzureDevOpsSyncRequest(BaseModel):
    project_id: int = Field(..., example=1)
    organization: str = Field("legger-org", example="legger-org")
    project_name: str = Field("L3721-Colsubsidio", example="L3721-Colsubsidio")

class OutlookIngestRequest(BaseModel):
    project_id: int = Field(..., example=1)
    subject: str = Field(..., example="Avances del proyecto L3721")
    sender: str = Field(..., example="cliente@colsubsidio.com")
    body: str = Field(..., example="Confirmamos aprobación de la entrega de la fase 1.")
    date: Optional[str] = Field(None, example="2026-07-27")

class AgentRunRequest(BaseModel):
    prompt: Optional[str] = Field(None, example="cuáles son los lineamientos de arquitectura?")
    query: Optional[str] = Field(None, example="cuáles son los lineamientos de arquitectura?")

# --- AGENT REGISTRY ---

REGISTERED_AGENTS = {
    "docs-agent": {
        "id": "docs-agent",
        "name": "Documentation & Knowledge Agent",
        "description": "Agente especializado en responder consultas contextuales, recuperar actas de reuniones y buscar guías de arquitectura.",
        "tools": ["search_knowledge", "list_documents", "list_meetings", "list_projects", "list_knowledge_items"],
        "status": "active"
    },
    "pm-agent": {
        "id": "pm-agent",
        "name": "Project Management Agent",
        "description": "Agente especializado en seguimiento de proyectos, clientes y estados de trabajo.",
        "tools": ["list_projects", "list_clients", "list_meetings", "list_tasks"],
        "status": "active"
    },
    "qa-agent": {
        "id": "qa-agent",
        "name": "QA & Compliance Agent",
        "description": "Agente especializado en auditoría y verificación de requisitos de calidad.",
        "tools": ["search_knowledge", "list_documents", "list_knowledge_items"],
        "status": "active"
    }
}

# --- FASTAPI APP ---

app = FastAPI(
    title=os.getenv("APP_NAME", "Oscar AI"),
    version="1.0.0",
    description="API REST para el backend de Oscar AI, que gestiona clientes, proyectos, reuniones, documentos, búsqueda semántica y ejecución de agentes.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Middleware
cors_origins_raw = os.getenv("CORS_ORIGINS", "*").strip()
cors_origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key & Audit Middleware
@app.middleware("http")
async def audit_and_auth_middleware(request: Request, call_next):
    path = request.url.path
    
    # 1. API Key Authentication Check (if API_KEY env variable is set)
    configured_key = os.getenv("API_KEY", "").strip()
    if configured_key and request.method != "OPTIONS":
        if path not in {"/", "/health", "/docs", "/redoc", "/openapi.json", "/api/v1/openapi.json"}:
            api_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
            if not api_key:
                auth_header = request.headers.get("Authorization") or request.headers.get("authorization") or ""
                if auth_header.startswith("Bearer "):
                    api_key = auth_header[7:].strip()
            
            if api_key != configured_key:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "INVALID_API_KEY"}
                )

    # 2. Process Request
    response = await call_next(request)

    # 3. Log Audit Event in PostgreSQL
    if path not in {"/docs", "/redoc", "/openapi.json", "/api/v1/openapi.json", "/favicon.ico"}:
        client_ip = request.client.host if request.client else None
        agent_id = request.headers.get("X-Agent-ID") or request.headers.get("x-agent-id")
        try:
            create_audit_event(
                endpoint=path,
                method=request.method,
                status_code=response.status_code,
                agent_id=agent_id,
                ip_address=client_ip
            )
        except Exception:
            pass

    return response

# Compatibility route for /api/v1/openapi.json
@app.get("/api/v1/openapi.json", include_in_schema=False)
def get_v1_openapi():
    return app.openapi()

# --- HEALTH & ROOT ENDPOINTS ---

@app.get("/health", summary="Verificar estado de salud")
def get_health():
    dependencies = dependency_status()
    healthy = all(item["ok"] for item in dependencies.values())
    status_code = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if healthy else "degraded",
            "service": os.getenv("APP_NAME", "Oscar AI"),
            "dependencies": dependencies,
        }
    )

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")

@app.get("/", summary="Dashboard Web Frontend", include_in_schema=False)
@app.get("/dashboard", summary="Dashboard Web Frontend", include_in_schema=False)
def get_dashboard_root():
    index_path = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(status_code=404, content={"detail": "DASHBOARD_NOT_FOUND"})

@app.get("/openclaw.yaml", summary="Manifiesto OpenClaw", include_in_schema=False)
def get_openclaw_manifest():
    manifest_path = os.path.join(os.path.dirname(BASE_DIR), "openclaw.yaml")
    if not os.path.exists(manifest_path):
        manifest_path = os.path.join(BASE_DIR, "openclaw.yaml")
    if os.path.exists(manifest_path):
        return FileResponse(manifest_path, media_type="text/yaml")
    return JSONResponse(status_code=404, content={"detail": "MANIFEST_NOT_FOUND"})

@app.get("/api/v1", summary="Información de API v1")
def get_v1_root():
    return {
        "name": os.getenv("APP_NAME", "Oscar AI"),
        "version": "v1",
        "docs": "/docs",
        "health": "/health",
    }

# --- CLIENTS ENDPOINTS ---

@app.get("/api/v1/clients", summary="Listar clientes")
@app.get("/clients", include_in_schema=False)
def list_clients_endpoint():
    try:
        return {"items": fetch_clients()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.get("/api/v1/clients/{client_id}", summary="Detalle de cliente")
@app.get("/clients/{client_id}", include_in_schema=False)
def get_client_endpoint(client_id: int):
    try:
        item = get_client(client_id)
        if not item:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return item
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.post("/api/v1/clients", status_code=201, summary="Crear cliente")
@app.post("/clients", status_code=201, include_in_schema=False)
def create_client_endpoint(payload: ClientCreate):
    try:
        return create_client(payload.code.strip(), payload.name.strip())
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.put("/api/v1/clients/{client_id}", summary="Actualizar cliente")
@app.put("/clients/{client_id}", include_in_schema=False)
def update_client_endpoint(client_id: int, payload: ClientCreate):
    try:
        updated = update_client(client_id, payload.code.strip(), payload.name.strip())
        if not updated:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return get_client(client_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.delete("/api/v1/clients/{client_id}", status_code=204, summary="Eliminar cliente")
@app.delete("/clients/{client_id}", status_code=204, include_in_schema=False)
def delete_client_endpoint(client_id: int):
    try:
        deleted = delete_client(client_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return Response(status_code=204)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

# --- PROJECTS ENDPOINTS ---

@app.get("/api/v1/projects", summary="Listar proyectos")
@app.get("/projects", include_in_schema=False)
def list_projects_endpoint():
    try:
        return {"items": fetch_projects()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.get("/api/v1/projects/{project_id}", summary="Detalle de proyecto")
@app.get("/projects/{project_id}", include_in_schema=False)
def get_project_endpoint(project_id: int):
    try:
        item = get_project(project_id)
        if not item:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return item
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.post("/api/v1/projects", status_code=201, summary="Crear proyecto")
@app.post("/projects", status_code=201, include_in_schema=False)
def create_project_endpoint(payload: ProjectCreate):
    try:
        return create_project(payload.client_id, payload.code.strip(), payload.name.strip(), payload.status.strip())
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.put("/api/v1/projects/{project_id}", summary="Actualizar proyecto")
@app.put("/projects/{project_id}", include_in_schema=False)
def update_project_endpoint(project_id: int, payload: ProjectCreate):
    try:
        updated = update_project(project_id, payload.client_id, payload.code.strip(), payload.name.strip(), payload.status.strip())
        if not updated:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return get_project(project_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.delete("/api/v1/projects/{project_id}", status_code=204, summary="Eliminar proyecto")
@app.delete("/projects/{project_id}", status_code=204, include_in_schema=False)
def delete_project_endpoint(project_id: int):
    try:
        deleted = delete_project(project_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return Response(status_code=204)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

# --- MEETINGS ENDPOINTS ---

@app.get("/api/v1/meetings", summary="Listar reuniones")
@app.get("/meetings", include_in_schema=False)
def list_meetings_endpoint():
    try:
        return {"items": fetch_meetings()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.get("/api/v1/meetings/{meeting_id}", summary="Detalle de reunión")
@app.get("/meetings/{meeting_id}", include_in_schema=False)
def get_meeting_endpoint(meeting_id: int):
    try:
        item = get_meeting(meeting_id)
        if not item:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return item
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.post("/api/v1/meetings", status_code=201, summary="Crear reunión")
@app.post("/meetings", status_code=201, include_in_schema=False)
def create_meeting_endpoint(payload: MeetingCreate):
    try:
        return create_meeting(payload.project_id, payload.title.strip(), payload.summary.strip(), payload.meeting_date)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.put("/api/v1/meetings/{meeting_id}", summary="Actualizar reunión")
@app.put("/meetings/{meeting_id}", include_in_schema=False)
def update_meeting_endpoint(meeting_id: int, payload: MeetingCreate):
    try:
        updated = update_meeting(meeting_id, payload.project_id, payload.title.strip(), payload.summary.strip(), payload.meeting_date)
        if not updated:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return get_meeting(meeting_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.delete("/api/v1/meetings/{meeting_id}", status_code=204, summary="Eliminar reunión")
@app.delete("/meetings/{meeting_id}", status_code=204, include_in_schema=False)
def delete_meeting_endpoint(meeting_id: int):
    try:
        deleted = delete_meeting(meeting_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return Response(status_code=204)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

# --- DOCUMENTS ENDPOINTS ---

@app.get("/api/v1/documents", summary="Listar documentos")
@app.get("/documents", include_in_schema=False)
def list_documents_endpoint():
    try:
        return {"items": fetch_documents()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.get("/api/v1/documents/{document_id}", summary="Detalle de documento")
@app.get("/documents/{document_id}", include_in_schema=False)
def get_document_endpoint(document_id: int):
    try:
        item = get_document(document_id)
        if not item:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return item
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.post("/api/v1/documents", status_code=201, summary="Crear documento")
@app.post("/documents", status_code=201, include_in_schema=False)
def create_document_endpoint(payload: DocumentCreate):
    try:
        return create_document(payload.project_id, payload.title.strip(), payload.content.strip(), payload.file_path)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.put("/api/v1/documents/{document_id}", summary="Actualizar documento")
@app.put("/documents/{document_id}", include_in_schema=False)
def update_document_endpoint(document_id: int, payload: DocumentCreate):
    try:
        updated = update_document(document_id, payload.project_id, payload.title.strip(), payload.content.strip(), payload.file_path)
        if not updated:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return get_document(document_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.delete("/api/v1/documents/{document_id}", status_code=204, summary="Eliminar documento")
@app.delete("/documents/{document_id}", status_code=204, include_in_schema=False)
def delete_document_endpoint(document_id: int):
    try:
        deleted = delete_document(document_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return Response(status_code=204)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.post("/api/v1/documents/ingest", status_code=201, summary="Ingestar y segmentar documento pesado")
@app.post("/documents/ingest", status_code=201, include_in_schema=False)
def ingest_document_endpoint(payload: DocumentIngestRequest):
    try:
        doc = create_document(
            payload.project_id,
            payload.title.strip(),
            payload.content.strip(),
            payload.file_path
        )
        from app.chunking import chunk_text
        from app.search import sync_documents_to_qdrant
        c_size = payload.chunk_size or 500
        c_overlap = payload.chunk_overlap or 50
        chunks = chunk_text(doc["content"], chunk_size=c_size, chunk_overlap=c_overlap)
        
        try:
            sync_documents_to_qdrant(doc_id=doc["id"])
        except Exception as sync_exc:
            print(f"Warning: sync_documents_to_qdrant failed: {sync_exc}")

        return {
            "document": doc,
            "chunk_size": c_size,
            "chunk_overlap": c_overlap,
            "total_chunks": len(chunks),
            "chunks_sample": chunks[:3]
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"INGESTION_FAILED: {exc}")

def extract_file_text(filename: str, content_bytes: bytes) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        try:
            import io
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content_bytes))
            text = ""
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
            if text.strip():
                return text.strip()
        except Exception as exc:
            print(f"Warning: pypdf extraction failed ({exc}), falling back to text decode.")
    
    return content_bytes.decode("utf-8", errors="ignore")

@app.post("/api/v1/documents/upload", status_code=201, summary="Subir y vectorizar archivo directo (PDF, MD, TXT, JSON)")
@app.post("/documents/upload", status_code=201, include_in_schema=False)
async def upload_document_endpoint(
    file: UploadFile = File(...),
    project_id: int = Form(...),
    chunk_size: Optional[int] = Form(500),
    chunk_overlap: Optional[int] = Form(50)
):
    try:
        content_bytes = await file.read()
        filename = file.filename or "uploaded_document.txt"
        extracted_text = extract_file_text(filename, content_bytes)
        
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="FILE_EMPTY_OR_UNREADABLE")

        doc_title = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").title()
        
        doc = create_document(
            project_id=project_id,
            title=doc_title,
            content=extracted_text.strip(),
            file_path=filename
        )
        
        from app.chunking import chunk_text
        from app.search import sync_documents_to_qdrant
        
        c_size = chunk_size or 500
        c_overlap = chunk_overlap or 50
        chunks = chunk_text(doc["content"], chunk_size=c_size, chunk_overlap=c_overlap)
        
        try:
            sync_documents_to_qdrant(doc_id=doc["id"])
        except Exception as sync_exc:
            print(f"Warning: sync_documents_to_qdrant failed on upload: {sync_exc}")

        return {
            "status": "uploaded_and_vectorized",
            "document": doc,
            "filename": filename,
            "file_size": len(content_bytes),
            "chunk_size": c_size,
            "chunk_overlap": c_overlap,
            "total_chunks": len(chunks),
            "chunks_sample": chunks[:3]
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"FILE_UPLOAD_FAILED: {exc}")

@app.post("/api/v1/documents/analyze-image", status_code=201, summary="Analizar e indexar imagen técnica con Gemini Vision")
@app.post("/documents/analyze-image", status_code=201, include_in_schema=False)
async def analyze_image_endpoint(
    file: UploadFile = File(...),
    project_id: int = Form(...),
    title: Optional[str] = Form(None),
    prompt: Optional[str] = Form(None)
):
    try:
        from app.vision import analyze_image_with_gemini
        from app.chunking import chunk_text
        from app.search import sync_documents_to_qdrant

        content_bytes = await file.read()
        filename = file.filename or "image_analysis.png"
        
        mime_type = "image/png"
        if filename.lower().endswith((".jpg", ".jpeg")):
            mime_type = "image/jpeg"
        elif filename.lower().endswith(".webp"):
            mime_type = "image/webp"

        analysis_text = analyze_image_with_gemini(content_bytes, mime_type=mime_type, prompt_custom=prompt)

        doc_title = title.strip() if title and title.strip() else f"Análisis Visual: {os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title()}"

        doc_content = f"# {doc_title}\n\n**Archivo de Origen:** `{filename}`\n\n## Análisis Técnico (Gemini Vision)\n\n{analysis_text}"

        doc = create_document(
            project_id=project_id,
            title=doc_title,
            content=doc_content,
            file_path=filename
        )

        chunks = chunk_text(doc["content"], chunk_size=500, chunk_overlap=50)

        try:
            sync_documents_to_qdrant(doc_id=doc["id"])
        except Exception as sync_exc:
            print(f"Warning: sync_documents_to_qdrant failed on image analysis: {sync_exc}")

        return {
            "status": "image_analyzed_and_vectorized",
            "document": doc,
            "filename": filename,
            "analysis": analysis_text,
            "total_chunks": len(chunks)
        }
    except HTTPException:
        raise
    except Exception as exc:
        print(f"IMAGE_ANALYSIS_FAILED error: {exc}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=503, detail=f"IMAGE_ANALYSIS_FAILED: {exc}")

# --- TASKS ENDPOINTS ---

@app.get("/api/v1/tasks", summary="Listar tareas")
@app.get("/tasks", include_in_schema=False)
def list_tasks_endpoint():
    try:
        return {"items": fetch_tasks()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.get("/api/v1/tasks/{task_id}", summary="Detalle de tarea")
@app.get("/tasks/{task_id}", include_in_schema=False)
def get_task_endpoint(task_id: int):
    try:
        item = get_task(task_id)
        if not item:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return item
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.post("/api/v1/tasks", status_code=201, summary="Crear tarea")
@app.post("/tasks", status_code=201, include_in_schema=False)
def create_task_endpoint(payload: TaskCreate):
    try:
        return create_task(payload.project_id, payload.title.strip(), payload.description, payload.assigned_agent_id, payload.status.strip())
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.put("/api/v1/tasks/{task_id}", summary="Actualizar tarea")
@app.put("/tasks/{task_id}", include_in_schema=False)
def update_task_endpoint(task_id: int, payload: TaskCreate):
    try:
        updated = update_task(task_id, payload.project_id, payload.title.strip(), payload.description, payload.assigned_agent_id, payload.status.strip())
        if not updated:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return get_task(task_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.delete("/api/v1/tasks/{task_id}", status_code=204, summary="Eliminar tarea")
@app.delete("/tasks/{task_id}", status_code=204, include_in_schema=False)
def delete_task_endpoint(task_id: int):
    try:
        deleted = delete_task(task_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return Response(status_code=204)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

# --- KNOWLEDGE ITEMS ENDPOINTS ---

@app.get("/api/v1/knowledge-items", summary="Listar artículos de base de conocimiento")
@app.get("/knowledge-items", include_in_schema=False)
def list_knowledge_items_endpoint():
    try:
        return {"items": fetch_knowledge_items()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.get("/api/v1/knowledge-items/{item_id}", summary="Detalle de artículo de conocimiento")
@app.get("/knowledge-items/{item_id}", include_in_schema=False)
def get_knowledge_item_endpoint(item_id: int):
    try:
        item = get_knowledge_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return item
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.post("/api/v1/knowledge-items", status_code=201, summary="Crear artículo de conocimiento")
@app.post("/knowledge-items", status_code=201, include_in_schema=False)
def create_knowledge_item_endpoint(payload: KnowledgeItemCreate):
    try:
        return create_knowledge_item(payload.project_id, payload.title.strip(), payload.content.strip(), payload.category.strip(), payload.source_url)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.put("/api/v1/knowledge-items/{item_id}", summary="Actualizar artículo de conocimiento")
@app.put("/knowledge-items/{item_id}", include_in_schema=False)
def update_knowledge_item_endpoint(item_id: int, payload: KnowledgeItemCreate):
    try:
        updated = update_knowledge_item(item_id, payload.project_id, payload.title.strip(), payload.content.strip(), payload.category.strip(), payload.source_url)
        if not updated:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return get_knowledge_item(item_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.delete("/api/v1/knowledge-items/{item_id}", status_code=204, summary="Eliminar artículo de conocimiento")
@app.delete("/knowledge-items/{item_id}", status_code=204, include_in_schema=False)
def delete_knowledge_item_endpoint(item_id: int):
    try:
        deleted = delete_knowledge_item(item_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return Response(status_code=204)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

# --- MEMORY ENTRIES ENDPOINTS ---

@app.get("/api/v1/memory-entries", summary="Listar entradas de memoria episódica")
@app.get("/memory-entries", include_in_schema=False)
def list_memory_entries_endpoint():
    try:
        return {"items": fetch_memory_entries()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.get("/api/v1/memory-entries/{entry_id}", summary="Detalle de entrada de memoria")
@app.get("/memory-entries/{entry_id}", include_in_schema=False)
def get_memory_entry_endpoint(entry_id: int):
    try:
        item = get_memory_entry(entry_id)
        if not item:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return item
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.post("/api/v1/memory-entries", status_code=201, summary="Crear entrada de memoria")
@app.post("/memory-entries", status_code=201, include_in_schema=False)
def create_memory_entry_endpoint(payload: MemoryEntryCreate):
    try:
        return create_memory_entry(payload.project_id, payload.content.strip(), payload.session_id.strip(), payload.role.strip())
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.put("/api/v1/memory-entries/{entry_id}", summary="Actualizar entrada de memoria")
@app.put("/memory-entries/{entry_id}", include_in_schema=False)
def update_memory_entry_endpoint(entry_id: int, payload: MemoryEntryCreate):
    try:
        updated = update_memory_entry(entry_id, payload.project_id, payload.content.strip(), payload.session_id.strip(), payload.role.strip())
        if not updated:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return get_memory_entry(entry_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

@app.delete("/api/v1/memory-entries/{entry_id}", status_code=204, summary="Eliminar entrada de memoria")
@app.delete("/memory-entries/{entry_id}", status_code=204, include_in_schema=False)
def delete_memory_entry_endpoint(entry_id: int):
    try:
        deleted = delete_memory_entry(entry_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return Response(status_code=204)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

# --- SEARCH ENDPOINTS ---

@app.get("/api/v1/search", summary="Búsqueda semántica")
@app.get("/search", include_in_schema=False)
def search_endpoint(
    q: str = Query(..., description="Término o frase a buscar semánticamente"),
    type: str = Query("all", description="Tipo de colección: meetings, documents, knowledge_items, memory_entries o all")
):
    query_text = q.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Missing q parameter")
    
    search_type = type.strip().lower()
    try:
        if search_type == "meetings":
            results = search_meetings(query_text)
        elif search_type == "documents":
            results = search_documents(query_text)
        elif search_type == "knowledge_items":
            results = search_knowledge_items(query_text)
        elif search_type == "memory_entries":
            results = search_memory_entries(query_text)
        else: # all
            results = []
            for func in [search_knowledge_items, search_documents, search_meetings, search_memory_entries]:
                try:
                    results.extend(func(query_text))
                except Exception:
                    pass
            results.sort(key=lambda x: x.get("score", 0.0), reverse=True)

        return {
            "query": query_text,
            "type": search_type,
            "items": results
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"SEARCH_UNAVAILABLE: {exc}")

# --- AGENTS ENDPOINTS ---

@app.get("/api/v1/agents", summary="Listar agentes disponibles")
@app.get("/agents", include_in_schema=False)
def list_agents_endpoint():
    return {"items": list(REGISTERED_AGENTS.values())}

@app.get("/api/v1/agents/{agent_id}", summary="Detalle de agente")
@app.get("/agents/{agent_id}", include_in_schema=False)
def get_agent_endpoint(agent_id: str):
    if agent_id not in REGISTERED_AGENTS:
        raise HTTPException(status_code=404, detail="AGENT_NOT_FOUND")
    return REGISTERED_AGENTS[agent_id]

@app.post("/api/v1/agents/{agent_id}/run", summary="Ejecutar agente")
@app.post("/agents/{agent_id}/run", include_in_schema=False)
def run_agent_endpoint(agent_id: str, payload: AgentRunRequest):
    if agent_id not in REGISTERED_AGENTS:
        raise HTTPException(status_code=404, detail="AGENT_NOT_FOUND")

    agent = REGISTERED_AGENTS[agent_id]
    prompt = (payload.prompt or payload.query or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Field prompt or query is required")

    sources = []
    
    # Check if prompt refers to Outlook, emails, or Teams
    lower_p = prompt.lower()
    if any(k in lower_p for k in ["correo", "email", "outlook", "mensaje", "teams"]):
        try:
            from app.integrations import MicrosoftGraphClient
            msgs = MicrosoftGraphClient.fetch_user_messages(limit=5)
            for msg in msgs:
                sender_addr = msg.get("from", {}).get("emailAddress", {}).get("address", "Remitente Desconocido")
                sources.append({
                    "score": 0.96,
                    "knowledge_item": {
                        "title": f"Correo Outlook Live: {msg.get('subject') or 'Sin Asunto'}",
                        "content": f"De: {sender_addr}\nFecha: {msg.get('receivedDateTime')}\n\nVista previa:\n{msg.get('bodyPreview') or ''}"
                    }
                })
        except Exception as exc:
            print(f"Warning: Live Graph API search skipped ({exc})")

    for func in [search_knowledge_items, search_documents, search_meetings, search_memory_entries]:
        try:
            sources.extend(func(prompt))
        except Exception:
            pass
    sources.sort(key=lambda x: x.get("score", 0.0), reverse=True)

    from app.search import synthesize_agent_response, is_communication_request
    answer = synthesize_agent_response(prompt, agent["name"], sources)

    saved_to_kb = False
    kb_item_id = None
    kb_title = None

    if is_communication_request(prompt):
        try:
            import re
            from app.storage import find_or_create_project_by_code, create_knowledge_item, fetch_projects
            from app.search import sync_knowledge_items_to_qdrant

            # Extract project code like L3835 or L3721
            match = re.search(r'\b[L|l]\d{4}\b', prompt)
            if match:
                project_code = match.group(0).upper()
                project_id = find_or_create_project_by_code(project_code)
            else:
                projects = fetch_projects()
                project_id = projects[0]["id"] if projects else 1
                project_code = "L3835"

            # Extract Subject title if present in answer
            subject_title = f"[Correo/Mensaje Generado] {project_code}"
            for line in answer.splitlines():
                if line.lower().startswith("asunto:"):
                    subject_title = f"[Correo Generado] {project_code}: {line[7:].strip()}"
                    break

            kb_item = create_knowledge_item(
                project_id=project_id,
                title=subject_title,
                content=answer,
                category="generado_comunicacion",
                source_url=f"oscarai://agent/{agent_id}/generated_message"
            )
            if kb_item and "id" in kb_item:
                kb_item_id = kb_item["id"]
                kb_title = kb_item["title"]
                saved_to_kb = True
                try:
                    sync_knowledge_items_to_qdrant(item_id=kb_item_id)
                except Exception as sync_exc:
                    print(f"Warning: Qdrant sync for generated message failed: {sync_exc}")

        except Exception as kb_exc:
            print(f"Warning: Auto-saving generated message to knowledge base failed: {kb_exc}")

    return {
        "agent": agent["id"],
        "agent_name": agent["name"],
        "prompt": prompt,
        "answer": answer,
        "sources": sources,
        "saved_to_kb": saved_to_kb,
        "kb_item_id": kb_item_id,
        "kb_title": kb_title
    }

# --- AUDIT EVENTS ENDPOINTS ---

@app.get("/api/v1/audit-events", summary="Listar registros de auditoría")
@app.get("/audit-events", include_in_schema=False)
def list_audit_events_endpoint(limit: int = Query(50, ge=1, le=500)):
    try:
        return {"items": fetch_audit_events(limit=limit)}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc}")

# --- INTEGRATIONS ENDPOINTS ---

from app.integrations import (
    get_integrations_status,
    GitHubConnector,
    AzureDevOpsConnector,
    OutlookConnector
)

@app.get("/api/v1/integrations/status", summary="Estado de conectores de integración")
@app.get("/integrations/status", include_in_schema=False)
def get_integrations_status_endpoint():
    return get_integrations_status()

@app.post("/api/v1/integrations/github/sync", status_code=200, summary="Sincronizar issues de GitHub")
@app.post("/integrations/github/sync", status_code=200, include_in_schema=False)
def sync_github_endpoint(payload: GitHubSyncRequest):
    try:
        return GitHubConnector.sync_repo_to_knowledge(payload.repo.strip(), payload.project_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"GITHUB_SYNC_FAILED: {exc}")

@app.post("/api/v1/integrations/azure-devops/sync", status_code=200, summary="Sincronizar Work Items de Azure DevOps")
@app.post("/integrations/azure-devops/sync", status_code=200, include_in_schema=False)
def sync_azure_devops_endpoint(payload: AzureDevOpsSyncRequest):
    try:
        return AzureDevOpsConnector.sync_project_to_knowledge(payload.organization.strip(), payload.project_name.strip(), payload.project_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"AZURE_DEVOPS_SYNC_FAILED: {exc}")

@app.post("/api/v1/integrations/outlook/ingest", status_code=201, summary="Ingestar correo electrónico de Outlook")
@app.post("/integrations/outlook/ingest", status_code=201, include_in_schema=False)
def ingest_outlook_endpoint(payload: OutlookIngestRequest):
    try:
        item = OutlookConnector.ingest_email(
            project_id=payload.project_id,
            subject=payload.subject.strip(),
            sender=payload.sender.strip(),
            body=payload.body.strip(),
            date=payload.date
        )
        return {"status": "ingested", "item": item}
    except Exception as exc:
        print(f"OUTLOOK_INGEST_FAILED error: {exc}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=503, detail=f"OUTLOOK_INGEST_FAILED: {exc}")

class TeamsAlertRequest(BaseModel):
    title: str = Field(..., description="Título de la alerta")
    text: str = Field(..., description="Detalle o resumen de la alerta en Markdown")
    urgency: Optional[str] = Field("normal", description="Nivel de urgencia: normal, high, warning, success")
    webhook_url: Optional[str] = Field(None, description="URL del Webhook de Teams (opcional)")

@app.post("/api/v1/integrations/teams/alert", status_code=200, summary="Enviar alerta proactiva a Microsoft Teams")
@app.post("/integrations/teams/alert", status_code=200, include_in_schema=False)
def send_teams_alert_endpoint(payload: TeamsAlertRequest):
    try:
        from app.integrations import TeamsConnector
        return TeamsConnector.send_notification(
            title=payload.title.strip(),
            text=payload.text.strip(),
            urgency=payload.urgency or "normal",
            webhook_url=payload.webhook_url
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"TEAMS_ALERT_FAILED: {exc}")

@app.post("/api/v1/integrations/chatgpt/import", status_code=201, summary="Importar e indexar conversaciones de ChatGPT")
@app.post("/integrations/chatgpt/import", status_code=201, include_in_schema=False)
async def import_chatgpt_endpoint(
    file: UploadFile = File(...),
    project_id: int = Form(...)
):
    try:
        from app.chatgpt_importer import parse_chatgpt_export
        from app.search import sync_knowledge_items_to_qdrant

        content_bytes = await file.read()
        filename = file.filename or "conversations.json"
        
        threads = parse_chatgpt_export(content_bytes, filename)
        if not threads:
            raise HTTPException(status_code=400, detail="NO_VALID_CHATGPT_THREADS_FOUND")

        created_items = []
        for thread in threads:
            item = create_knowledge_item(
                project_id=project_id,
                title=thread["title"],
                category="chatgpt_export",
                content=thread["content"],
                source_url=f"chatgpt://import/{filename}"
            )
            created_items.append(item)

        try:
            sync_knowledge_items_to_qdrant()
        except Exception as sync_exc:
            print(f"Warning: sync_knowledge_items_to_qdrant failed on chatgpt import: {sync_exc}")

        return {
            "status": "imported_and_vectorized",
            "total_imported": len(created_items),
            "filename": filename,
            "items": created_items[:5]
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"CHATGPT_IMPORT_FAILED: {exc}")

# --- WEB DASHBOARD FRONTEND MOUNT ---

if os.path.exists(WEB_DIR):
    app.mount("/", StaticFiles(directory=WEB_DIR), name="static_web")


