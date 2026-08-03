import os
import json
import urllib.request
import urllib.parse

def test_ms_graph_auth():
    print("=== TESTING MICROSOFT GRAPH OAUTH2 TOKEN RETRIEVAL ===")
    tenant_id = os.getenv("AZURE_TENANT_ID", "")
    client_id = os.getenv("AZURE_CLIENT_ID", "")
    client_secret = os.getenv("AZURE_CLIENT_SECRET", "")

    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")

    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            token = res.get("access_token")
            print("[OK] Microsoft Graph Token Received Successfully!")
            print("[OK] Token Type:", res.get("token_type"))
            print("[OK] Expires In:", res.get("expires_in"), "seconds")
            print("[OK] Token Sample:", token[:50] + "...")
            return token
    except Exception as exc:
        print("[ERROR] Microsoft Graph Token Retrieval Failed:", str(exc))
        return None

if __name__ == "__main__":
    test_ms_graph_auth()
