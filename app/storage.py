import os
import pg8000.dbapi

def env_int(name, default):
    return int(os.getenv(name, str(default)))

def postgres_config():
    return {
        "host": os.getenv("POSTGRES_HOST", "postgres"),
        "port": env_int("POSTGRES_PORT", 5432),
        "database": os.getenv("POSTGRES_DB", "oscar_ai"),
        "user": os.getenv("POSTGRES_USER", "oscar_ai"),
        "password": os.getenv("POSTGRES_PASSWORD", "change-me"),
    }

def postgres_connect():
    config = postgres_config()
    return pg8000.dbapi.connect(
        host=config["host"],
        port=config["port"],
        database=config["database"],
        user=config["user"],
        password=config["password"],
        timeout=2,
    )

def postgres_health():
    try:
        with postgres_connect() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            finally:
                cursor.close()
        return True, "ok"
    except Exception as exc:
        return False, str(exc)

def init_postgres_schema():
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS clients (
                    id SERIAL PRIMARY KEY,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id SERIAL PRIMARY KEY,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'planned',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                ALTER TABLE projects
                ADD COLUMN IF NOT EXISTS client_id INTEGER REFERENCES clients(id)
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS meetings (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER NOT NULL REFERENCES projects(id),
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    meeting_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER NOT NULL REFERENCES projects(id),
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    file_path TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER NOT NULL REFERENCES projects(id),
                    assigned_agent_id TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER NOT NULL REFERENCES projects(id),
                    title TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'general',
                    content TEXT NOT NULL,
                    source_url TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER NOT NULL REFERENCES projects(id),
                    session_id TEXT NOT NULL DEFAULT 'default',
                    role TEXT NOT NULL DEFAULT 'user',
                    content TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    id SERIAL PRIMARY KEY,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    agent_id TEXT,
                    ip_address TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )

            cursor.execute("SELECT COUNT(*) FROM clients")
            client_count = cursor.fetchone()[0]
            if client_count == 0:
                cursor.execute(
                    """
                    INSERT INTO clients (code, name)
                    VALUES (%s, %s)
                    RETURNING id
                    """,
                    ("CL-001", "Oscar AI Client"),
                )
                client_id = cursor.fetchone()[0]
            else:
                cursor.execute("SELECT id FROM clients ORDER BY id ASC LIMIT 1")
                client_id = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM projects")
            project_count = cursor.fetchone()[0]
            if project_count == 0:
                cursor.execute(
                    """
                    INSERT INTO projects (client_id, code, name, status)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (client_id, "OSCAR-001", "Oscar AI Platform", "planned"),
                )
                project_id = cursor.fetchone()[0]
            else:
                cursor.execute("SELECT id FROM projects ORDER BY id ASC LIMIT 1")
                project_id = cursor.fetchone()[0]
                cursor.execute(
                    """
                    UPDATE projects
                    SET client_id = COALESCE(client_id, %s)
                    """,
                    (client_id,),
                )

            cursor.execute("SELECT COUNT(*) FROM meetings")
            meeting_count = cursor.fetchone()[0]
            if meeting_count == 0:
                cursor.execute(
                    """
                    INSERT INTO meetings (project_id, title, summary)
                    VALUES (%s, %s, %s)
                    """,
                    (project_id, "Project kickoff", "Initial meeting created by the app bootstrap process."),
                )

            cursor.execute("SELECT COUNT(*) FROM documents")
            document_count = cursor.fetchone()[0]
            if document_count == 0:
                cursor.execute(
                    """
                    INSERT INTO documents (project_id, title, content)
                    VALUES (%s, %s, %s)
                    """,
                    (project_id, "Project architecture guidelines", "This document describes the architectural decisions for Oscar AI, including containerization, vector search with Qdrant, and Postgres storage."),
                )

            cursor.execute("SELECT COUNT(*) FROM tasks")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    """
                    INSERT INTO tasks (project_id, assigned_agent_id, title, description, status)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (project_id, "pm-agent", "Configurar integración OpenClaw", "Verificar conectividad de herramientas OpenAPI con OpenClaw", "completed"),
                )

            cursor.execute("SELECT COUNT(*) FROM knowledge_items")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    """
                    INSERT INTO knowledge_items (project_id, title, category, content)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (project_id, "Decisión sobre Vector Store", "architecture", "Se definió Qdrant como base de datos vectorial para recuperación contextual RAG."),
                )

            cursor.execute("SELECT COUNT(*) FROM memory_entries")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    """
                    INSERT INTO memory_entries (project_id, session_id, role, content)
                    VALUES (%s, %s, %s, %s), (%s, %s, %s, %s)
                    """,
                    (
                        project_id, "session-001", "user", "¿Cuál es el estado del proyecto Oscar AI?",
                        project_id, "session-001", "agent", "El proyecto Oscar AI cuenta con arquitectura modular, FastAPI, Qdrant y PostgreSQL en ejecución."
                    ),
                )
        finally:
            cursor.close()
        connection.commit()

# --- CLIENTS CRUD ---

def get_client(client_id):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT id, code, name, created_at
                FROM clients
                WHERE id = %s
                """,
                (client_id,),
            )
            row = cursor.fetchone()
        finally:
            cursor.close()

    if not row:
        return None

    return {
        "id": row[0],
        "code": row[1],
        "name": row[2],
        "created_at": row[3].isoformat(),
    }

def create_client(code, name):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO clients (code, name)
                VALUES (%s, %s)
                RETURNING id
                """,
                (code, name),
            )
            client_id = cursor.fetchone()[0]
        finally:
            cursor.close()
        connection.commit()
    return get_client(client_id)

def update_client(client_id, code, name):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                UPDATE clients
                SET code = %s, name = %s
                WHERE id = %s
                """,
                (code, name, client_id),
            )
            updated_rows = cursor.rowcount
        finally:
            cursor.close()
        connection.commit()
    return updated_rows > 0

def delete_client(client_id):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM clients WHERE id = %s", (client_id,))
            deleted_rows = cursor.rowcount
        finally:
            cursor.close()
        connection.commit()
    return deleted_rows > 0

def fetch_clients():
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT id, code, name, created_at
                FROM clients
                ORDER BY id ASC
                """
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()

    return [
        {
            "id": row[0],
            "code": row[1],
            "name": row[2],
            "created_at": row[3].isoformat(),
        }
        for row in rows
    ]

# --- PROJECTS CRUD ---

def get_project_by_code(code: str):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT p.id, p.code, p.name, p.status, p.created_at, c.code, c.name, p.client_id
                FROM projects p
                LEFT JOIN clients c ON c.id = p.client_id
                WHERE LOWER(p.code) = LOWER(%s)
                """,
                (code.strip(),),
            )
            row = cursor.fetchone()
        finally:
            cursor.close()

    if not row:
        return None

    return {
        "id": row[0],
        "code": row[1],
        "name": row[2],
        "status": row[3],
        "created_at": row[4].isoformat(),
        "client_id": row[7],
        "client": {"code": row[5], "name": row[6]} if row[5] else None,
    }

def find_or_create_project_by_code(code: str, name: str = None) -> int:
    existing = get_project_by_code(code)
    if existing:
        return existing["id"]
    
    clients = fetch_clients()
    client_id = clients[0]["id"] if clients else 1
    project_name = name or f"Proyecto {code.upper()}"
    return create_project(client_id=client_id, code=code.upper(), name=project_name, status="active")

def get_project(project_id):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT p.id, p.code, p.name, p.status, p.created_at, c.code, c.name, p.client_id
                FROM projects p
                LEFT JOIN clients c ON c.id = p.client_id
                WHERE p.id = %s
                """,
                (project_id,),
            )
            row = cursor.fetchone()
        finally:
            cursor.close()

    if not row:
        return None

    return {
        "id": row[0],
        "code": row[1],
        "name": row[2],
        "status": row[3],
        "created_at": row[4].isoformat(),
        "client_id": row[7],
        "client": {"code": row[5], "name": row[6]} if row[5] else None,
    }

def create_project(client_id, code, name, status):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO projects (client_id, code, name, status)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (client_id, code, name, status),
            )
            project_id = cursor.fetchone()[0]
        finally:
            cursor.close()
        connection.commit()
    return get_project(project_id)

def update_project(project_id, client_id, code, name, status):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                UPDATE projects
                SET client_id = %s, code = %s, name = %s, status = %s
                WHERE id = %s
                """,
                (client_id, code, name, status, project_id),
            )
            updated_rows = cursor.rowcount
        finally:
            cursor.close()
        connection.commit()
    return updated_rows > 0

def delete_project(project_id):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT id FROM meetings WHERE project_id = %s", (project_id,))
            meeting_ids = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("SELECT id FROM documents WHERE project_id = %s", (project_id,))
            doc_ids = [row[0] for row in cursor.fetchall()]

            cursor.execute("SELECT id FROM knowledge_items WHERE project_id = %s", (project_id,))
            ki_ids = [row[0] for row in cursor.fetchall()]

            cursor.execute("SELECT id FROM memory_entries WHERE project_id = %s", (project_id,))
            mem_ids = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("DELETE FROM meetings WHERE project_id = %s", (project_id,))
            cursor.execute("DELETE FROM documents WHERE project_id = %s", (project_id,))
            cursor.execute("DELETE FROM tasks WHERE project_id = %s", (project_id,))
            cursor.execute("DELETE FROM knowledge_items WHERE project_id = %s", (project_id,))
            cursor.execute("DELETE FROM memory_entries WHERE project_id = %s", (project_id,))
            cursor.execute("DELETE FROM projects WHERE id = %s", (project_id,))
            deleted_rows = cursor.rowcount
        finally:
            cursor.close()
        connection.commit()
        
    if deleted_rows > 0:
        from app.search import delete_point
        for m_id in meeting_ids:
            try:
                delete_point("meetings", m_id)
            except Exception:
                pass
        for d_id in doc_ids:
            try:
                delete_point("documents", d_id)
            except Exception:
                pass
        for k_id in ki_ids:
            try:
                delete_point("knowledge_items", k_id)
            except Exception:
                pass
        for mem_id in mem_ids:
            try:
                delete_point("memory_entries", mem_id)
            except Exception:
                pass
    return deleted_rows > 0

def fetch_projects():
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT p.id, p.code, p.name, p.status, p.created_at, c.code, c.name
                FROM projects p
                LEFT JOIN clients c ON c.id = p.client_id
                ORDER BY p.id ASC
                """
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()

    return [
        {
            "id": row[0],
            "code": row[1],
            "name": row[2],
            "status": row[3],
            "created_at": row[4].isoformat(),
            "client": {"code": row[5], "name": row[6]} if row[5] else None,
        }
        for row in rows
    ]

# --- MEETINGS CRUD ---

def get_meeting(meeting_id):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT m.id, m.title, m.summary, m.meeting_date, p.id, p.code, p.name
                FROM meetings m
                INNER JOIN projects p ON p.id = m.project_id
                WHERE m.id = %s
                """,
                (meeting_id,),
            )
            row = cursor.fetchone()
        finally:
            cursor.close()

    if not row:
        return None

    return {
        "id": row[0],
        "title": row[1],
        "summary": row[2],
        "meeting_date": row[3].isoformat(),
        "project_id": row[4],
        "project": {"code": row[5], "name": row[6]},
    }

def create_meeting(project_id, title, summary, meeting_date=None):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            if meeting_date:
                cursor.execute(
                    """
                    INSERT INTO meetings (project_id, title, summary, meeting_date)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (project_id, title, summary, meeting_date),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO meetings (project_id, title, summary)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (project_id, title, summary),
                )
            meeting_id = cursor.fetchone()[0]
        finally:
            cursor.close()
        connection.commit()
    from app.search import sync_meetings_to_qdrant
    try:
        sync_meetings_to_qdrant()
    except Exception:
        pass
    return get_meeting(meeting_id)

def update_meeting(meeting_id, project_id, title, summary, meeting_date=None):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            if meeting_date:
                cursor.execute(
                    """
                    UPDATE meetings
                    SET project_id = %s, title = %s, summary = %s, meeting_date = %s
                    WHERE id = %s
                    """,
                    (project_id, title, summary, meeting_date, meeting_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE meetings
                    SET project_id = %s, title = %s, summary = %s
                    WHERE id = %s
                    """,
                    (project_id, title, summary, meeting_id),
                )
            updated_rows = cursor.rowcount
        finally:
            cursor.close()
        connection.commit()
    from app.search import sync_meetings_to_qdrant
    try:
        sync_meetings_to_qdrant()
    except Exception:
        pass
    return updated_rows > 0

def delete_meeting(meeting_id):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM meetings WHERE id = %s", (meeting_id,))
            deleted_rows = cursor.rowcount
        finally:
            cursor.close()
        connection.commit()
    if deleted_rows > 0:
        from app.search import delete_point
        try:
            delete_point("meetings", meeting_id)
        except Exception:
            pass
    return deleted_rows > 0

def fetch_meetings():
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT m.id, m.title, m.summary, m.meeting_date, p.code, p.name
                FROM meetings m
                INNER JOIN projects p ON p.id = m.project_id
                ORDER BY m.id ASC
                """
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()

    return [
        {
            "id": row[0],
            "title": row[1],
            "summary": row[2],
            "meeting_date": row[3].isoformat(),
            "project": {"code": row[4], "name": row[5]},
        }
        for row in rows
    ]

# --- DOCUMENTS CRUD ---

def get_document(document_id):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT d.id, d.title, d.content, d.file_path, d.created_at, p.id, p.code, p.name
                FROM documents d
                INNER JOIN projects p ON p.id = d.project_id
                WHERE d.id = %s
                """,
                (document_id,),
            )
            row = cursor.fetchone()
        finally:
            cursor.close()

    if not row:
        return None

    return {
        "id": row[0],
        "title": row[1],
        "content": row[2],
        "file_path": row[3],
        "created_at": row[4].isoformat(),
        "project_id": row[5],
        "project": {"code": row[6], "name": row[7]},
    }

def create_document(project_id, title, content, file_path=None):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO documents (project_id, title, content, file_path)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (project_id, title, content, file_path),
            )
            document_id = cursor.fetchone()[0]
        finally:
            cursor.close()
        connection.commit()
    from app.search import sync_documents_to_qdrant
    try:
        sync_documents_to_qdrant(doc_id=document_id)
    except Exception:
        pass
    return get_document(document_id)

def update_document(document_id, project_id, title, content, file_path=None):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                UPDATE documents
                SET project_id = %s, title = %s, content = %s, file_path = %s
                WHERE id = %s
                """,
                (project_id, title, content, file_path, document_id),
            )
            updated_rows = cursor.rowcount
        finally:
            cursor.close()
        connection.commit()
    from app.search import sync_documents_to_qdrant
    try:
        sync_documents_to_qdrant()
    except Exception:
        pass
    return updated_rows > 0

def delete_document(document_id):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM documents WHERE id = %s", (document_id,))
            deleted_rows = cursor.rowcount
        finally:
            cursor.close()
        connection.commit()
    if deleted_rows > 0:
        from app.search import delete_point
        try:
            delete_point("documents", document_id)
        except Exception:
            pass
    return deleted_rows > 0

def fetch_documents():
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT d.id, d.title, d.content, d.file_path, d.created_at, p.id, p.code, p.name
                FROM documents d
                INNER JOIN projects p ON p.id = d.project_id
                ORDER BY d.id ASC
                """
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()

    return [
        {
            "id": row[0],
            "title": row[1],
            "content": row[2],
            "file_path": row[3],
            "created_at": row[4].isoformat(),
            "project_id": row[5],
            "project": {"code": row[6], "name": row[7]},
        }
        for row in rows
    ]

# --- TASKS CRUD ---

def get_task(task_id):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT t.id, t.title, t.description, t.status, t.assigned_agent_id, t.created_at, p.id, p.code, p.name
                FROM tasks t
                INNER JOIN projects p ON p.id = t.project_id
                WHERE t.id = %s
                """,
                (task_id,),
            )
            row = cursor.fetchone()
        finally:
            cursor.close()

    if not row:
        return None

    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "status": row[3],
        "assigned_agent_id": row[4],
        "created_at": row[5].isoformat(),
        "project_id": row[6],
        "project": {"code": row[7], "name": row[8]},
    }

def create_task(project_id, title, description=None, assigned_agent_id=None, status="pending"):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO tasks (project_id, title, description, assigned_agent_id, status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (project_id, title, description, assigned_agent_id, status),
            )
            task_id = cursor.fetchone()[0]
        finally:
            cursor.close()
        connection.commit()
    return get_task(task_id)

def update_task(task_id, project_id, title, description=None, assigned_agent_id=None, status="pending"):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                UPDATE tasks
                SET project_id = %s, title = %s, description = %s, assigned_agent_id = %s, status = %s
                WHERE id = %s
                """,
                (project_id, title, description, assigned_agent_id, status, task_id),
            )
            updated_rows = cursor.rowcount
        finally:
            cursor.close()
        connection.commit()
    return updated_rows > 0

def delete_task(task_id):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            deleted_rows = cursor.rowcount
        finally:
            cursor.close()
        connection.commit()
    return deleted_rows > 0

def fetch_tasks():
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT t.id, t.title, t.description, t.status, t.assigned_agent_id, t.created_at, p.id, p.code, p.name
                FROM tasks t
                INNER JOIN projects p ON p.id = t.project_id
                ORDER BY t.id ASC
                """
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()

    return [
        {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "status": row[3],
            "assigned_agent_id": row[4],
            "created_at": row[5].isoformat(),
            "project_id": row[6],
            "project": {"code": row[7], "name": row[8]},
        }
        for row in rows
    ]

# --- KNOWLEDGE ITEMS CRUD ---

def get_knowledge_item(item_id):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT k.id, k.title, k.category, k.content, k.source_url, k.created_at, p.id, p.code, p.name
                FROM knowledge_items k
                INNER JOIN projects p ON p.id = k.project_id
                WHERE k.id = %s
                """,
                (item_id,),
            )
            row = cursor.fetchone()
        finally:
            cursor.close()

    if not row:
        return None

    return {
        "id": row[0],
        "title": row[1],
        "category": row[2],
        "content": row[3],
        "source_url": row[4],
        "created_at": row[5].isoformat(),
        "project_id": row[6],
        "project": {"code": row[7], "name": row[8]},
    }

def create_knowledge_item(project_id, title, content, category="general", source_url=None):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO knowledge_items (project_id, title, content, category, source_url)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (project_id, title, content, category, source_url),
            )
            item_id = cursor.fetchone()[0]
        finally:
            cursor.close()
        connection.commit()
    from app.search import sync_knowledge_items_to_qdrant
    try:
        sync_knowledge_items_to_qdrant(item_id=item_id)
    except Exception:
        pass
    return get_knowledge_item(item_id)

def update_knowledge_item(item_id, project_id, title, content, category="general", source_url=None):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                UPDATE knowledge_items
                SET project_id = %s, title = %s, content = %s, category = %s, source_url = %s
                WHERE id = %s
                """,
                (project_id, title, content, category, source_url, item_id),
            )
            updated_rows = cursor.rowcount
        finally:
            cursor.close()
        connection.commit()
    from app.search import sync_knowledge_items_to_qdrant
    try:
        sync_knowledge_items_to_qdrant()
    except Exception:
        pass
    return updated_rows > 0

def delete_knowledge_item(item_id):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM knowledge_items WHERE id = %s", (item_id,))
            deleted_rows = cursor.rowcount
        finally:
            cursor.close()
        connection.commit()
    if deleted_rows > 0:
        from app.search import delete_point
        try:
            delete_point("knowledge_items", item_id)
        except Exception:
            pass
    return deleted_rows > 0

def fetch_knowledge_items():
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT k.id, k.title, k.category, k.content, k.source_url, k.created_at, p.id, p.code, p.name
                FROM knowledge_items k
                INNER JOIN projects p ON p.id = k.project_id
                ORDER BY k.id ASC
                """
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()

    return [
        {
            "id": row[0],
            "title": row[1],
            "category": row[2],
            "content": row[3],
            "source_url": row[4],
            "created_at": row[5].isoformat(),
            "project_id": row[6],
            "project": {"code": row[7], "name": row[8]},
        }
        for row in rows
    ]

# --- MEMORY ENTRIES CRUD ---

def get_memory_entry(entry_id):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT m.id, m.session_id, m.role, m.content, m.created_at, p.id, p.code, p.name
                FROM memory_entries m
                INNER JOIN projects p ON p.id = m.project_id
                WHERE m.id = %s
                """,
                (entry_id,),
            )
            row = cursor.fetchone()
        finally:
            cursor.close()

    if not row:
        return None

    return {
        "id": row[0],
        "session_id": row[1],
        "role": row[2],
        "content": row[3],
        "created_at": row[4].isoformat(),
        "project_id": row[5],
        "project": {"code": row[6], "name": row[7]},
    }

def create_memory_entry(project_id, content, session_id="default", role="user"):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO memory_entries (project_id, session_id, role, content)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (project_id, session_id, role, content),
            )
            entry_id = cursor.fetchone()[0]
        finally:
            cursor.close()
        connection.commit()
    from app.search import sync_memory_entries_to_qdrant
    try:
        sync_memory_entries_to_qdrant()
    except Exception:
        pass
    return get_memory_entry(entry_id)

def update_memory_entry(entry_id, project_id, content, session_id="default", role="user"):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                UPDATE memory_entries
                SET project_id = %s, session_id = %s, role = %s, content = %s
                WHERE id = %s
                """,
                (project_id, session_id, role, content, entry_id),
            )
            updated_rows = cursor.rowcount
        finally:
            cursor.close()
        connection.commit()
    from app.search import sync_memory_entries_to_qdrant
    try:
        sync_memory_entries_to_qdrant()
    except Exception:
        pass
    return updated_rows > 0

def delete_memory_entry(entry_id):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM memory_entries WHERE id = %s", (entry_id,))
            deleted_rows = cursor.rowcount
        finally:
            cursor.close()
        connection.commit()
    if deleted_rows > 0:
        from app.search import delete_point
        try:
            delete_point("memory_entries", entry_id)
        except Exception:
            pass
    return deleted_rows > 0

def fetch_memory_entries():
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT m.id, m.session_id, m.role, m.content, m.created_at, p.id, p.code, p.name
                FROM memory_entries m
                INNER JOIN projects p ON p.id = m.project_id
                ORDER BY m.id ASC
                """
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()

    return [
        {
            "id": row[0],
            "session_id": row[1],
            "role": row[2],
            "content": row[3],
            "created_at": row[4].isoformat(),
            "project_id": row[5],
            "project": {"code": row[6], "name": row[7]},
        }
        for row in rows
    ]

# --- AUDIT EVENTS ---

def create_audit_event(endpoint: str, method: str, status_code: int, agent_id: str = None, ip_address: str = None):
    try:
        with postgres_connect() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO audit_events (endpoint, method, status_code, agent_id, ip_address)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (endpoint, method, status_code, agent_id, ip_address),
                )
            finally:
                cursor.close()
            connection.commit()
    except Exception as exc:
        print(f"Warning: Failed to create audit event: {exc}")

def fetch_audit_events(limit: int = 50):
    with postgres_connect() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT id, endpoint, method, status_code, agent_id, ip_address, created_at
                FROM audit_events
                ORDER BY id DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()

    return [
        {
            "id": row[0],
            "endpoint": row[1],
            "method": row[2],
            "status_code": row[3],
            "agent_id": row[4],
            "ip_address": row[5],
            "created_at": row[6].isoformat(),
        }
        for row in rows
    ]


