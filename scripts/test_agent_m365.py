import json
import urllib.request

BASE_URL = "http://127.0.0.1:8080"

def main():
    print("=== TESTING AGENT CONSOLE M365 (OUTLOOK & TEAMS) RAG ACCESS ===")
    
    payload = json.dumps({
        "agent": "pm-agent",
        "prompt": "¿Qué correos o notificaciones de Outlook y Teams tenemos registrados sobre la aprobación del sprint L3721?"
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/agents/pm-agent/run",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print("\n[OK] Agent Name:", res.get("agent_name"))
        print("[OK] Total Sources Retrieved:", len(res.get("sources", [])))
        print("\n--- AGENT SYNTHESIZED ANSWER ---")
        print(res.get("answer"))

if __name__ == "__main__":
    main()
