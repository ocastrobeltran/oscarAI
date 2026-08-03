import json
import urllib.request

BASE_URL = "http://127.0.0.1:8080"

def main():
    print("=== TESTING MICROSOFT 365 (OUTLOOK & TEAMS) INTEGRATION ===")

    # 1. Test Status
    req_status = urllib.request.Request(f"{BASE_URL}/api/v1/integrations/status")
    with urllib.request.urlopen(req_status) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print("[OK] Integration Status:", res["connectors"]["outlook"])
        print("[OK] Teams Connector:", res["connectors"]["teams"])

    # 2. Test Teams Alert Endpoint
    teams_payload = json.dumps({
        "title": "[ALERTA HITO L3721] Aprobación de Alcance por Colsubsidio",
        "text": "**Proyecto:** Colsubsidio CIAM (L3721)\n\n**Estado:** Se aprobó la especificación técnica de OAuth2 PKCE.\n\n*Notificación proactiva enviada por Oscar AI*",
        "urgency": "high"
    }).encode("utf-8")

    req_teams = urllib.request.Request(
        f"{BASE_URL}/api/v1/integrations/teams/alert",
        data=teams_payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req_teams) as resp_teams:
        res_teams = json.loads(resp_teams.read().decode("utf-8"))
        print("\n[OK] Teams Alert Dispatch Status:", res_teams.get("status"))

    # 3. Test Email Ingestion with Proactive Trigger
    email_payload = json.dumps({
        "project_id": 1,
        "subject": "URGENTE: Aprobación de entrega de sprint L3721",
        "sender": "gerencia@colsubsidio.com",
        "body": "Confirmamos la aprobación de los entregables del sprint L3721. Proceder con el despliegue en producción.",
        "date": "2026-07-30"
    }).encode("utf-8")

    req_email = urllib.request.Request(
        f"{BASE_URL}/api/v1/integrations/outlook/ingest",
        data=email_payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req_email) as resp_email:
        res_email = json.loads(resp_email.read().decode("utf-8"))
        print("\n[OK] Outlook Ingestion & Proactive Trigger Result:", res_email["status"])
        print("  - Item ID:", res_email["item"]["id"])
        print("  - Item Title:", res_email["item"]["title"])

    print("\n=== MICROSOFT 365 & TEAMS INTEGRATION TEST COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
