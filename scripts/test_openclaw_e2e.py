import os
import json
import urllib.request

BASE_URL = "http://127.0.0.1:8080"

def log_step(step_num, title):
    print(f"\n==========================================")
    print(f"[STEP {step_num}] {title}")
    print(f"==========================================")

def http_get(path):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def http_post(path, data):
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json", "X-Agent-ID": "openclaw-runner"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    print("=== STARTING OPENCLAW AUTONOMOUS E2E TOOL PIPELINE EXECUTION TEST ===")

    # Step 1: Validate OpenAPI schema and OpenClaw manifest
    log_step(1, "Validating /openapi.json & openclaw.yaml Manifest Alignment")
    openapi_data = http_get("/openapi.json")
    print("[OK] OpenAPI 3.1.0 Title:", openapi_data.get("info", {}).get("title"))
    print("[OK] OpenAPI Total Endpoints:", len(openapi_data.get("paths", {})))

    with open("openclaw.yaml", "r", encoding="utf-8") as f:
        yaml_content = f.read()
    tool_names = [line.split("name:")[1].strip() for line in yaml_content.splitlines() if "name:" in line and not line.strip().startswith("#")]
    print("[OK] OpenClaw Manifest Tools Registered:", len(tool_names), "| Tools:", tool_names[:5])

    # Step 2: Register new project via create_project tool
    log_step(2, "OpenClaw Tool Call: create_project (L3835 - Autogermana Portal)")
    import time
    proj_code = f"L3835-{int(time.time()) % 1000}"
    proj_res = http_post("/api/v1/projects", {
        "code": proj_code,
        "name": "Autogermana Portal Redesign & QA",
        "client_id": 1
    })
    project_id = proj_res["id"]
    print("[OK] Created Project ID:", project_id, "| Code:", proj_res["code"], "| Name:", proj_res["name"])

    # Step 3: Ingest project specifications via ingest_document tool
    log_step(3, "OpenClaw Tool Call: ingest_document (L3835 Technical Manual)")
    doc_res = http_post("/api/v1/documents/ingest", {
        "project_id": project_id,
        "title": "Manual de Integracion Autogermana L3835",
        "content": "El proyecto L3835 comprende el redisenio del portal corporativo para Autogermana. Se exige integracion con pasarela de pagos PSE y tarjeta de credito mediante TLS 1.3. La fase de QA sera liderada por Oscar Castro con pruebas automatizadas en Playwright.",
        "chunk_size": 250,
        "chunk_overlap": 30
    })
    print("[OK] Document Ingested ID:", doc_res["document"]["id"], "| Total Chunks:", doc_res["total_chunks"])

    # Step 4: Sync GitHub Issues via sync_github_issues tool
    log_step(4, "OpenClaw Tool Call: sync_github_issues (legger/platform-l3721)")
    gh_res = http_post("/api/v1/integrations/github/sync", {
        "project_id": project_id,
        "repo": "legger/platform-l3721"
    })
    print("[OK] GitHub Issues Synced:", gh_res["synced_count"])

    # Step 5: Ingest Client Approval Email via ingest_email tool
    log_step(5, "OpenClaw Tool Call: ingest_email (Outlook Client Email)")
    email_res = http_post("/api/v1/integrations/outlook/ingest", {
        "project_id": project_id,
        "subject": "Aprobacion Kickoff Autogermana L3835",
        "sender": "gerencia@autogermana.com.co",
        "body": "Confirmamos el inicio del proyecto L3835 segun la propuesta tecnica presentada por Oscar Castro.",
        "date": "2026-07-27"
    })
    print("[OK] Outlook Email Ingested:", email_res["item"]["title"])

    # Step 6: Multi-collection RAG search & agent synthesis
    log_step(6, "OpenClaw Tool Call: search_knowledge & run_agent Synthesis")
    search_res = http_get("/api/v1/search?q=Autogermana&type=all")
    print("[OK] Multi-Collection Vector Hits Found:", len(search_res.get("items", [])))

    agent_res = http_post("/api/v1/agents/pm-agent/run", {
        "prompt": "cual es el estado y acuerdos del proyecto Autogermana L3835?"
    })
    print("[OK] Agent Synthesized Answer:\n", agent_res["answer"])

    # Step 7: Verify Audit Events in PostgreSQL
    log_step(7, "Verifying PostgreSQL audit_events logging")
    audit_res = http_get("/api/v1/audit-events?limit=10")
    print("[OK] Audit Log Recorded Events:", len(audit_res.get("items", [])))
    for event in audit_res.get("items", [])[:5]:
        print(f"   - Event #{event['id']}: {event['method']} {event['endpoint']} => Status {event['status_code']} (Agent: {event['agent_id']})")

    print("\n=== OPENCLAW AUTONOMOUS E2E TOOL PIPELINE TEST COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
