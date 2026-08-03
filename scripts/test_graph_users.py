import os
import json
import urllib.request
import urllib.parse

def test_graph_users():
    print("=== TESTING MICROSOFT GRAPH USERS & MESSAGES LISTING ===")
    tenant_id = os.getenv("AZURE_TENANT_ID", "")
    client_id = os.getenv("AZURE_CLIENT_ID", "")
    client_secret = os.getenv("AZURE_CLIENT_SECRET", "")

    # 1. Get Token
    url_token = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }).encode("utf-8")

    req_token = urllib.request.Request(url_token, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")

    try:
        with urllib.request.urlopen(req_token) as resp:
            token = json.loads(resp.read().decode("utf-8")).get("access_token")
            print("[OK] Token obtained!")
    except Exception as exc:
        print("[ERROR] Token failed:", exc)
        return

    # 2. List Users in Tenant
    url_users = "https://graph.microsoft.com/v1.0/users?$select=id,displayName,userPrincipalName,mail"
    req_users = urllib.request.Request(url_users, headers={"Authorization": f"Bearer {token}"})

    try:
        with urllib.request.urlopen(req_users) as resp_users:
            users_data = json.loads(resp_users.read().decode("utf-8"))
            print("\n[OK] Users in Microsoft Graph Tenant:")
            for u in users_data.get("value", []):
                print(f"  - Name: {u.get('displayName')} | UPN: {u.get('userPrincipalName')} | Mail: {u.get('mail')}")
    except Exception as exc:
        print("[ERROR] Listing users failed:", exc)

if __name__ == "__main__":
    test_graph_users()
