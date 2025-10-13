import os
import time
from typing import Optional, Dict, Any
from jose import jwt
import httpx


# Env flags and config
ENABLE_N8N = os.getenv("ENABLE_N8N_EMAIL", "false").lower() in ("1", "true", "yes")
N8N_WEBHOOK_URL = os.getenv("N8N_EMAIL_WEBHOOK_URL", "")

ENABLE_FIREBASE = os.getenv("ENABLE_FIREBASE_MESSAGING", "false").lower() in ("1", "true", "yes")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
FIREBASE_CLIENT_EMAIL = os.getenv("FIREBASE_CLIENT_EMAIL", "")
FIREBASE_PRIVATE_KEY = os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n")
FCM_DEFAULT_TOPIC = os.getenv("FCM_DEFAULT_TOPIC", "gramafix")


async def send_n8n_email(event: str, payload: Dict[str, Any]) -> bool:
    if not ENABLE_N8N or not N8N_WEBHOOK_URL:
        return False
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(N8N_WEBHOOK_URL, json={"event": event, "payload": payload})
            return res.status_code in (200, 201, 202)
    except Exception:
        return False


def _firebase_get_oauth_token() -> Optional[str]:
    """Service account JWT assertion to get OAuth2 access token for FCM HTTP v1."""
    if not (FIREBASE_CLIENT_EMAIL and FIREBASE_PRIVATE_KEY):
        return None
    now = int(time.time())
    payload = {
        "iss": FIREBASE_CLIENT_EMAIL,
        "scope": "https://www.googleapis.com/auth/firebase.messaging",
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now,
        "exp": now + 3600,
    }
    assertion = jwt.encode(payload, FIREBASE_PRIVATE_KEY, algorithm="RS256")
    try:
        resp = httpx.post(
            "https://oauth2.googleapis.com/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": assertion,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
    except Exception:
        return None
    return None


async def firebase_send_message(
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None,
    topic: Optional[str] = None,
) -> bool:
    if not ENABLE_FIREBASE or not FIREBASE_PROJECT_ID:
        return False
    token = _firebase_get_oauth_token()
    if not token:
        return False
    message = {
        "message": {
            "notification": {"title": title, "body": body},
            "data": data or {},
        }
    }
    target_topic = topic or FCM_DEFAULT_TOPIC
    if target_topic:
        message["message"]["topic"] = target_topic

    url = f"https://fcm.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/messages:send"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(url, headers=headers, json=message)
            return res.status_code in (200, 201)
    except Exception:
        return False


async def notify_issue_created(issue: Dict[str, Any]):
    # Email via n8n
    await send_n8n_email(
        event="issue_created",
        payload={
            "id": str(issue.get("_id", "")),
            "category": issue.get("category"),
            "description": issue.get("description"),
            "reporter_name": issue.get("reporter_name"),
            "reporter_phone": issue.get("reporter_phone"),
            "gram_panchayat": issue.get("gram_panchayat"),
            "created_at": issue.get("created_at"),
            "images": issue.get("images", []),
        },
    )

    # Push via Firebase FCM
    await firebase_send_message(
        title="New Issue Reported",
        body=f"{issue.get('category')}: {issue.get('description', '')[:60]}",
        data={
            "issue_id": str(issue.get("_id", "")),
            "status": issue.get("status", "Received"),
        },
    )


async def notify_status_updated(issue: Dict[str, Any], status: str, remarks: Optional[str], updated_by: str):
    # Email via n8n
    await send_n8n_email(
        event="issue_status_updated",
        payload={
            "id": str(issue.get("_id", "")),
            "category": issue.get("category"),
            "description": issue.get("description"),
            "gram_panchayat": issue.get("gram_panchayat"),
            "new_status": status,
            "remarks": remarks,
            "updated_by": updated_by,
            "updated_at": time.time(),
        },
    )

    # Push via Firebase FCM
    await firebase_send_message(
        title="Issue Status Updated",
        body=f"Status: {status} | {issue.get('category')}",
        data={
            "issue_id": str(issue.get("_id", "")),
            "status": status,
        },
    )
