from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import socket
import struct
from hashlib import sha256
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

import pg8000.dbapi


def env_int(name, default):
    return int(os.getenv(name, str(default)))


def tcp_check(host, port, timeout=1.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, "ok"
    except OSError as exc:
        return False, str(exc)


def http_check(url, timeout=1.0):
    try:
        request = Request(url, method="GET")
        with urlopen(request, timeout=timeout) as response:
            if 200 <= response.status < 300:
                return True, "ok"
            return False, f"unexpected status {response.status}"
    except Exception as exc:
        return False, str(exc)


def qdrant_config():
    return {
        "host": os.getenv("QDRANT_HOST", "qdrant"),
        "port": env_int("QDRANT_PORT", 6333),
        "collection": os.getenv("QDRANT_COLLECTION", "meetings"),
    }


def qdrant_url(path):
    config = qdrant_config()
    return f"http://{config['host']}:{config['port']}{path}"


def qdrant_request(method, path, payload=None):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(qdrant_url(path), data=body, method=method)
    request.add_header("Content-Type", "application/json")
    with urlopen(request, timeout=3) as response:
        content = response.read().decode("utf-8")
        return json.loads(content) if content else {}


def parse_json_body(handler):
    content_length = int(handler.headers.get("Content-Length", "0"))
    raw_body = handler.rfile.read(content_length).decode("utf-8") if content_length else "{}"
    if not raw_body.strip():
        return {}
    return json.loads(raw_body)


def parse_resource_id(path, resource_name):
    for prefix in (f"/{resource_name}/", f"/api/v1/{resource_name}/"):
        if path.startswith(prefix):
            suffix = path[len(prefix):]
            if suffix.isdigit():
                return int(suffix)
    return None


def embed_text(text, dimensions=32):
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
            cursor.execute("DELETE FROM meetings WHERE project_id = %s", (project_id,))
            cursor.execute("DELETE FROM projects WHERE id = %s", (project_id,))
            deleted_rows = cursor.rowcount
        finally:
            cursor.close()
        connection.commit()
    sync_meetings_to_qdrant()
    return deleted_rows > 0


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
    sync_meetings_to_qdrant()
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
    sync_meetings_to_qdrant()
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
    sync_meetings_to_qdrant()
    return deleted_rows > 0


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

                cursor.execute(
                    """
                    INSERT INTO meetings (project_id, title, summary)
                    VALUES (%s, %s, %s)
                    """,
                    (project_id, "Project kickoff", "Initial meeting created by the app bootstrap process."),
                )
            else:
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
                    cursor.execute("SELECT id FROM projects ORDER BY id ASC LIMIT 1")
                    project_id = cursor.fetchone()[0]
                    cursor.execute(
                        """
                        INSERT INTO meetings (project_id, title, summary)
                        VALUES (%s, %s, %s)
                        """,
                        (project_id, "Project kickoff", "Initial meeting created by the app bootstrap process."),
                    )
        finally:
            cursor.close()
        connection.commit()


def ensure_qdrant_collection():
    config = qdrant_config()
    payload = {
        "vectors": {
            "size": 32,
            "distance": "Cosine",
        }
    }
    try:
        qdrant_request("PUT", f"/collections/{config['collection']}", payload)
    except Exception:
        pass


def sync_meetings_to_qdrant():
    config = qdrant_config()
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
            f"/collections/{config['collection']}/points?wait=true",
            {"points": points},
        )
    except Exception:
        pass


def qdrant_search(query_text):
    config = qdrant_config()
    response = qdrant_request(
        "POST",
        f"/collections/{config['collection']}/points/search",
        {
            "vector": embed_text(query_text),
            "limit": 5,
            "with_payload": True,
        },
    )

    return [
        {
            "score": item.get("score"),
            "meeting": item.get("payload", {}),
        }
        for item in response.get("result", [])
    ]


def search_meetings(query_text):
    try:
        return qdrant_search(query_text)
    except Exception as exc:
        raise RuntimeError(f"Qdrant search failed: {exc}") from exc


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


def qdrant_health():
    try:
        return http_check(qdrant_url("/healthz"))
    except Exception:
        return False


def dependency_status():
    postgres_ok, postgres_detail = postgres_health()
    redis_ok, redis_detail = tcp_check(
        os.getenv("REDIS_HOST", "redis"),
        env_int("REDIS_PORT", 6379),
    )
    qdrant_ok, qdrant_detail = http_check(
        f"http://{os.getenv('QDRANT_HOST', 'qdrant')}:{env_int('QDRANT_PORT', 6333)}/healthz"
    )

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
            "detail": qdrant_detail,
        },
    }


class AppHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        if path == "/health":
            dependencies = dependency_status()
            healthy = all(item["ok"] for item in dependencies.values())
            self._send_json(
                200 if healthy else 503,
                {
                    "status": "ok" if healthy else "degraded",
                    "service": os.getenv("APP_NAME", "Oscar AI"),
                    "dependencies": dependencies,
                },
            )
            return

        if path in {"/projects", "/api/v1/projects"}:
            try:
                self._send_json(200, {"items": fetch_projects()})
            except Exception as exc:
                self._send_json(503, {"error": "DATABASE_UNAVAILABLE", "detail": str(exc)})
            return

        if path in {"/clients", "/api/v1/clients"}:
            try:
                self._send_json(200, {"items": fetch_clients()})
            except Exception as exc:
                self._send_json(503, {"error": "DATABASE_UNAVAILABLE", "detail": str(exc)})
            return

        if path in {"/meetings", "/api/v1/meetings"}:
            try:
                self._send_json(200, {"items": fetch_meetings()})
            except Exception as exc:
                self._send_json(503, {"error": "DATABASE_UNAVAILABLE", "detail": str(exc)})
            return

        if path in {"/search", "/api/v1/search"}:
            try:
                query_text = query.get("q", [""])[0].strip()
                if not query_text:
                    self._send_json(400, {"error": "INVALID_QUERY", "detail": "Missing q parameter"})
                    return
                self._send_json(200, {"query": query_text, "items": search_meetings(query_text)})
            except Exception as exc:
                self._send_json(503, {"error": "SEARCH_UNAVAILABLE", "detail": str(exc)})
            return

        if path == "/api/v1":
            self._send_json(
                200,
                {
                    "name": os.getenv("APP_NAME", "Oscar AI"),
                    "version": "v1",
                    "routes": ["/api/v1/clients", "/api/v1/projects", "/api/v1/meetings", "/api/v1/search?q=..."],
                },
            )
            return

        for resource_name, fetcher in (("clients", fetch_clients), ("projects", fetch_projects), ("meetings", fetch_meetings)):
            resource_id = parse_resource_id(path, resource_name)
            if resource_id is not None:
                try:
                    item = next((entry for entry in fetcher() if entry["id"] == resource_id), None)
                    if not item:
                        self._send_json(404, {"error": "NOT_FOUND"})
                        return
                    self._send_json(200, item)
                except Exception as exc:
                    self._send_json(503, {"error": "DATABASE_UNAVAILABLE", "detail": str(exc)})
                return

        self._send_json(
            200,
            {
                "name": os.getenv("APP_NAME", "Oscar AI"),
                "environment": os.getenv("APP_ENV", "local"),
                "message": "Oscar AI app service is running",
                "paths": [
                    "/health",
                    "/",
                    "/clients",
                    "/projects",
                    "/meetings",
                    "/search?q=...",
                    "/api/v1",
                ],
            },
        )

    def log_message(self, format, *args):
        return

    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        try:
            body = parse_json_body(self)
        except Exception as exc:
            self._send_json(400, {"error": "INVALID_JSON", "detail": str(exc)})
            return

        try:
            if path in {"/clients", "/api/v1/clients"}:
                client = create_client(body["code"].strip(), body["name"].strip())
                self._send_json(201, client)
                return

            if path in {"/projects", "/api/v1/projects"}:
                project = create_project(
                    body.get("client_id"),
                    body["code"].strip(),
                    body["name"].strip(),
                    body.get("status", "planned").strip(),
                )
                self._send_json(201, project)
                return

            if path in {"/meetings", "/api/v1/meetings"}:
                meeting = create_meeting(
                    body["project_id"],
                    body["title"].strip(),
                    body["summary"].strip(),
                    body.get("meeting_date"),
                )
                self._send_json(201, meeting)
                return

        except KeyError as exc:
            self._send_json(400, {"error": "MISSING_FIELD", "detail": f"Missing field: {exc.args[0]}"})
            return
        except Exception as exc:
            self._send_json(503, {"error": "DATABASE_UNAVAILABLE", "detail": str(exc)})
            return

        self._send_json(404, {"error": "NOT_FOUND"})

    def do_PUT(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        try:
            body = parse_json_body(self)
        except Exception as exc:
            self._send_json(400, {"error": "INVALID_JSON", "detail": str(exc)})
            return

        try:
            client_id = parse_resource_id(path, "clients")
            if client_id is not None:
                updated = update_client(client_id, body["code"].strip(), body["name"].strip())
                self._send_json(200 if updated else 404, get_client(client_id) if updated else {"error": "NOT_FOUND"})
                return

            project_id = parse_resource_id(path, "projects")
            if project_id is not None:
                updated = update_project(
                    project_id,
                    body.get("client_id"),
                    body["code"].strip(),
                    body["name"].strip(),
                    body.get("status", "planned").strip(),
                )
                self._send_json(200 if updated else 404, get_project(project_id) if updated else {"error": "NOT_FOUND"})
                return

            meeting_id = parse_resource_id(path, "meetings")
            if meeting_id is not None:
                updated = update_meeting(
                    meeting_id,
                    body["project_id"],
                    body["title"].strip(),
                    body["summary"].strip(),
                    body.get("meeting_date"),
                )
                self._send_json(200 if updated else 404, get_meeting(meeting_id) if updated else {"error": "NOT_FOUND"})
                return

        except KeyError as exc:
            self._send_json(400, {"error": "MISSING_FIELD", "detail": f"Missing field: {exc.args[0]}"})
            return
        except Exception as exc:
            self._send_json(503, {"error": "DATABASE_UNAVAILABLE", "detail": str(exc)})
            return

        self._send_json(404, {"error": "NOT_FOUND"})

    def do_DELETE(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        try:
            client_id = parse_resource_id(path, "clients")
            if client_id is not None:
                deleted = delete_client(client_id)
                self._send_json(204 if deleted else 404, {})
                return

            project_id = parse_resource_id(path, "projects")
            if project_id is not None:
                deleted = delete_project(project_id)
                self._send_json(204 if deleted else 404, {})
                return

            meeting_id = parse_resource_id(path, "meetings")
            if meeting_id is not None:
                deleted = delete_meeting(meeting_id)
                self._send_json(204 if deleted else 404, {})
                return
        except Exception as exc:
            self._send_json(503, {"error": "DATABASE_UNAVAILABLE", "detail": str(exc)})
            return

        self._send_json(404, {"error": "NOT_FOUND"})


def main():
    port = int(os.getenv("APP_PORT", "8080"))
    init_postgres_schema()
    ensure_qdrant_collection()
    sync_meetings_to_qdrant()
    server = HTTPServer(("0.0.0.0", port), AppHandler)
    print(f"Oscar AI app listening on {port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
