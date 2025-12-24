import os
import httpx
import msal
from fastmcp import FastMCP

mcp = FastMCP("OutlookMCP")

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")  # 若你用 client-credentials
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

# 方案 1：Client Credentials（適合 service / daemon；但 mail 操作通常要搭配應用權限與管理員同意）
SCOPES = ["https://graph.microsoft.com/.default"]

def get_access_token() -> str:
    app = msal.ConfidentialClientApplication(
        client_id=CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=AUTHORITY,
    )
    result = app.acquire_token_for_client(scopes=SCOPES)
    if "access_token" not in result:
        raise RuntimeError(f"Token error: {result.get('error')} {result.get('error_description')}")
    return result["access_token"]

async def graph_request(method: str, url: str, json=None, params=None):
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.request(method, url, headers=headers, json=json, params=params)
        # sendMail 可能回 202 且無 body，屬正常狀態 :contentReference[oaicite:6]{index=6}
        if r.status_code >= 400:
            raise RuntimeError(f"Graph error {r.status_code}: {r.text}")
        if r.text:
            return r.json()
        return {"status_code": r.status_code}

@mcp.tool()
async def outlook_send_mail(to: str, subject: str, body: str, content_type: str = "Text", save_to_sent: bool = True):
    """
    Send an email via Microsoft Graph.
    content_type: "Text" or "HTML"
    """
    url = "https://graph.microsoft.com/v1.0/me/sendMail"
    payload = {
        "message": {
            "subject": subject,
            "body": {"contentType": content_type, "content": body},
            "toRecipients": [{"emailAddress": {"address": to}}],
        },
        "saveToSentItems": save_to_sent,
    }
    return await graph_request("POST", url, json=payload)

@mcp.tool()
async def outlook_list_unread(top: int = 10):
    """
    List unread emails (basic fields).
    """
    url = "https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages"
    params = {
        "$filter": "isRead eq false",
        "$top": str(top),
        "$select": "id,subject,from,receivedDateTime,isRead",
        "$orderby": "receivedDateTime desc",
    }
    return await graph_request("GET", url, params=params)

@mcp.tool()
async def outlook_list_events(days: int = 7, top: int = 20):
    """
    List upcoming calendar events.
    """
    # 簡化：用 calendarView 需要 start/end；你可自行補上以符合你的需求
    # 這裡先示範讀取 events（不同租戶/情境可能需要調整）
    url = "https://graph.microsoft.com/v1.0/me/events"
    params = {"$top": str(top), "$select": "subject,start,end,location", "$orderby": "start/dateTime"}
    return await graph_request("GET", url, params=params)

if __name__ == "__main__":
    # stdio 模式（最常用於本機 host，如 Claude Desktop / 本機 orchestrator）
    mcp.run()
