import os
import uvicorn

from app.storage import init_postgres_schema
from app.search import (
    ensure_qdrant_collection,
    sync_meetings_to_qdrant,
    sync_documents_to_qdrant,
    sync_knowledge_items_to_qdrant,
    sync_memory_entries_to_qdrant,
)
from app.api import app

def bootstrap():
    print("Bootstrapping database schema...")
    init_postgres_schema()
    
    print("Ensuring Qdrant collections...")
    ensure_qdrant_collection("meetings")
    ensure_qdrant_collection("documents")
    ensure_qdrant_collection("knowledge_items")
    ensure_qdrant_collection("memory_entries")
    
    print("Syncing database records to Qdrant...")
    try:
        sync_meetings_to_qdrant()
    except Exception as exc:
        print(f"Warning: Meeting sync to Qdrant failed: {exc}")
        
    try:
        sync_documents_to_qdrant()
    except Exception as exc:
        print(f"Warning: Document sync to Qdrant failed: {exc}")

    try:
        sync_knowledge_items_to_qdrant()
    except Exception as exc:
        print(f"Warning: KnowledgeItems sync to Qdrant failed: {exc}")

    try:
        sync_memory_entries_to_qdrant()
    except Exception as exc:
        print(f"Warning: MemoryEntries sync to Qdrant failed: {exc}")

import threading

def main():
    port = int(os.getenv("APP_PORT", "8080"))
    print("Starting background bootstrap thread...")
    t = threading.Thread(target=bootstrap, daemon=True)
    t.start()
    print(f"Oscar AI app starting with FastAPI on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
