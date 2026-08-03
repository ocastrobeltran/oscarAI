import os
import json
import urllib.parse
from typing import List, Dict, Any, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# Storage & Search operations
from app.storage import create_knowledge_item, create_task
from app.search import sync_knowledge_items_to_qdrant

def get_integrations_status() -> Dict[str, Any]:
    github_token = os.getenv("GITHUB_TOKEN", "").strip()
    devops_token = os.getenv("AZURE_DEVOPS_TOKEN", "").strip()
    outlook_secret = (os.getenv("AZURE_CLIENT_SECRET") or os.getenv("OUTLOOK_CLIENT_SECRET", "")).strip()
    teams_webhook = os.getenv("TEAMS_WEBHOOK_URL", "").strip()
    
    return {
        "status": "ok",
        "connectors": {
            "github": {
                "configured": bool(github_token),
                "mode": "live" if github_token else "demo/mock",
                "default_repo": "legger/platform-l3721"
            },
            "azure_devops": {
                "configured": bool(devops_token),
                "mode": "live" if devops_token else "demo/mock",
                "default_organization": "legger-org",
                "default_project": "L3721-Colsubsidio"
            },
            "outlook": {
                "configured": bool(outlook_secret),
                "mode": "live (Microsoft Graph API)" if outlook_secret else "demo/mock",
                "tenant_id": os.getenv("AZURE_TENANT_ID") or os.getenv("OUTLOOK_TENANT_ID", "default-tenant")
            },
            "teams": {
                "configured": bool(teams_webhook or outlook_secret),
                "mode": "live (Adaptive Cards)" if (teams_webhook or outlook_secret) else "demo/mock"
            }
        }
    }

class MicrosoftGraphClient:
    @staticmethod
    def get_access_token() -> Optional[str]:
        tenant_id = os.getenv("AZURE_TENANT_ID") or os.getenv("OUTLOOK_TENANT_ID")
        client_id = os.getenv("AZURE_CLIENT_ID") or os.getenv("OUTLOOK_CLIENT_ID")
        client_secret = os.getenv("AZURE_CLIENT_SECRET") or os.getenv("OUTLOOK_CLIENT_SECRET")

        if not tenant_id or not client_id or not client_secret:
            return None

        url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        data = urllib.parse.urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials"
        }).encode("utf-8")

        req = Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
        try:
            with urlopen(req, timeout=12) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res.get("access_token")
        except Exception as exc:
            print(f"Warning: Microsoft Graph OAuth token request failed: {exc}")
            return None

    @classmethod
    def fetch_user_messages(cls, user_id: str = "me", limit: int = 10) -> List[Dict[str, Any]]:
        token = cls.get_access_token()
        if not token:
            return []

        url = f"https://graph.microsoft.com/v1.0/users/{user_id}/messages?$top={limit}&$select=id,subject,from,bodyPreview,receivedDateTime"
        req = Request(url, headers={"Authorization": f"Bearer {token}"}, method="GET")
        try:
            with urlopen(req, timeout=12) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res.get("value", [])
        except Exception as exc:
            print(f"Warning: Microsoft Graph fetch_user_messages failed: {exc}")
            return []

    @classmethod
    def fetch_user_calendar(cls, user_id: str = "me", limit: int = 10) -> List[Dict[str, Any]]:
        token = cls.get_access_token()
        if not token:
            return []

        url = f"https://graph.microsoft.com/v1.0/users/{user_id}/events?$top={limit}&$select=id,subject,start,end,location,organizer"
        req = Request(url, headers={"Authorization": f"Bearer {token}"}, method="GET")
        try:
            with urlopen(req, timeout=12) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res.get("value", [])
        except Exception as exc:
            print(f"Warning: Microsoft Graph fetch_user_calendar failed: {exc}")
            return []

class TeamsConnector:
    @staticmethod
    def send_notification(title: str, text: str, urgency: str = "normal", webhook_url: Optional[str] = None) -> Dict[str, Any]:
        url = webhook_url or os.getenv("TEAMS_WEBHOOK_URL")
        
        theme_color = "0076D7"  # Default Microsoft Blue
        if urgency == "high":
            theme_color = "FF0000"  # Urgent Red
        elif urgency == "warning":
            theme_color = "FF9900"  # Warning Amber
        elif urgency == "success":
            theme_color = "10B981"  # Emerald Green

        card_payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": theme_color,
            "summary": title,
            "sections": [{
                "activityTitle": f"🤖 Oscar AI Alert: {title}",
                "activitySubtitle": f"Prioridad: {urgency.upper()}",
                "text": text,
                "markdown": True
            }],
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "Abrir Dashboard de Oscar AI",
                    "targets": [{"os": "default", "uri": os.getenv("APP_URL", "http://localhost:8080/")}]
                }
            ]
        }

        if not url:
            print(f"[Teams Connector Mock Log] {title}: {text}")
            return {
                "status": "simulated_sent",
                "webhook_configured": False,
                "title": title,
                "text": text,
                "card": card_payload
            }

        req = Request(url, data=json.dumps(card_payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(req, timeout=10) as resp:
                res_body = resp.read().decode("utf-8")
                return {"status": "sent", "response": res_body, "title": title}
        except Exception as exc:
            print(f"Warning: Teams Webhook dispatch failed: {exc}")
            return {"status": "failed", "error": str(exc)}

class GitHubConnector:
    @staticmethod
    def fetch_issues(repo: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
        auth_token = token or os.getenv("GITHUB_TOKEN", "").strip()
        if not auth_token:
            return [
                {
                    "number": 101,
                    "title": "[L3721] Error de autenticación en login SSO",
                    "state": "open",
                    "body": "El token JWT no está refrescando adecuadamente al expirar los 15 minutos en el ambiente de QA.",
                    "html_url": f"https://github.com/{repo}/issues/101",
                    "assignee": "Oscar Pérez"
                },
                {
                    "number": 102,
                    "title": "[L3833] Optimización de consultas en base de datos PostgreSQL",
                    "state": "closed",
                    "body": "Se agregaron índices en la tabla documents y audit_events para reducir latencia a menos de 50ms.",
                    "html_url": f"https://github.com/{repo}/issues/102",
                    "assignee": "Laura Yexela"
                }
            ]

        url = f"https://api.github.com/repos/{repo}/issues?state=all"
        req = Request(url, method="GET")
        req.add_header("Authorization", f"token {auth_token}")
        req.add_header("User-Agent", "Oscar-AI")
        req.add_header("Accept", "application/vnd.github.v3+json")

        with urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content)

    @classmethod
    def sync_repo_to_knowledge(cls, repo: str, project_id: int) -> Dict[str, Any]:
        issues = cls.fetch_issues(repo)
        synced_items = []
        for issue in issues:
            title = f"GitHub Issue #{issue['number']}: {issue['title']}"
            body = f"Estado: {issue['state']}\nAsignado a: {issue.get('assignee') or 'Sin asignar'}\nURL: {issue.get('html_url')}\n\nDetalle:\n{issue.get('body') or ''}"
            item = create_knowledge_item(
                project_id=project_id,
                title=title,
                content=body,
                category="github_issue",
                source_url=issue.get("html_url")
            )
            synced_items.append(item)

        return {
            "repository": repo,
            "synced_count": len(synced_items),
            "items": synced_items
        }

class AzureDevOpsConnector:
    @staticmethod
    def fetch_work_items(organization: str, project: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
        auth_token = token or os.getenv("AZURE_DEVOPS_TOKEN", "").strip()
        if not auth_token:
            return [
                {
                    "id": 4501,
                    "title": "[L3721] Implementación de módulo de actas de reunión",
                    "type": "User Story",
                    "state": "Active",
                    "description": "Permitir al PM ingresar minutas y extraer compromisos automáticamente.",
                    "assigned_to": "Oscar Castro"
                },
                {
                    "id": 4502,
                    "title": "[L3755] Corrección de estilos CSS en Safari",
                    "type": "Bug",
                    "state": "Resolved",
                    "description": "El flexbox layout no centraba los botones en dispositivos iOS 17.",
                    "assigned_to": "Laura Yexela"
                }
            ]

        return []

    @classmethod
    def sync_project_to_knowledge(cls, organization: str, project: str, project_id: int) -> Dict[str, Any]:
        work_items = cls.fetch_work_items(organization, project)
        synced_items = []
        for wi in work_items:
            title = f"Azure DevOps #{wi['id']} ({wi['type']}): {wi['title']}"
            content = f"Estado: {wi['state']}\nAsignado a: {wi.get('assigned_to')}\n\nDescripción:\n{wi.get('description') or ''}"
            item = create_knowledge_item(
                project_id=project_id,
                title=title,
                content=content,
                category="azure_devops",
                source_url=f"https://dev.azure.com/{organization}/{project}/_workitems/edit/{wi['id']}"
            )
            synced_items.append(item)

        return {
            "organization": organization,
            "project": project,
            "synced_count": len(synced_items),
            "items": synced_items
        }

class OutlookConnector:
    @staticmethod
    def ingest_email(project_id: int, subject: str, sender: str, body: str, date: Optional[str] = None) -> Dict[str, Any]:
        title = f"Correo: {subject.strip()}"
        content = f"De: {sender.strip()}\nFecha: {date or 'Reciente'}\n\nContenido:\n{body.strip()}"
        
        item = create_knowledge_item(
            project_id=project_id,
            title=title,
            content=content,
            category="email",
            source_url=f"mailto:{sender.strip()}"
        )

        # Trigger proactive Teams notification if email contains critical keywords
        lower_body = body.lower()
        if any(kw in lower_body for kw in ["urgente", "aprobado", "incidencia", "bug", "retraso", "prioridad"]):
            TeamsConnector.send_notification(
                title=f"Correo Relevante Detectado: {subject}",
                text=f"**Remitente:** {sender}\n\n**Extracto:** {body[:250]}...",
                urgency="high"
            )

        return item
