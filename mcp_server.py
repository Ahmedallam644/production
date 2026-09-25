import os
import sys
import time
import threading
import argparse
import requests
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from notifier import send_headless_notification, send_telegram, log
import inbox_manager

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Load environment
ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(ENV_PATH)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip().replace("'", "").replace('"', "")

# =====================================================================
# BACKGROUND TELEGRAM LISTENER (Ahmed's phone -> Gemini Spark Inbox)
# =====================================================================

def telegram_poller():
    """Listens for messages from Ahmed's phone and queues them for Spark."""
    if not TOKEN:
        log("[!] Telegram Bot Token missing. Poller disabled.")
        return

    log("[*] Telegram listener active: waiting for messages from Ahmed's phone...")
    offset = None

    while True:
        try:
            params = {"timeout": 20}
            if offset:
                params["offset"] = offset

            r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", params=params, timeout=25)
            data = r.json()
            updates = data.get("result", [])

            for update in updates:
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id", ""))
                user_text = msg.get("text", "").strip()

                if not user_text:
                    continue

                # Security: Only accept from authorized user
                if ALLOWED_CHAT_ID and chat_id != ALLOWED_CHAT_ID:
                    continue

                log(f"[Phone -> Spark]: '{user_text}' from Ahmed")
                inbox_manager.add_user_message("Ahmed", user_text)

                # Send quick confirmation back to Telegram
                confirm_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                confirm_payload = {
                    "chat_id": chat_id,
                    "text": f"📨 *Received by Gemini Spark:*\n_{user_text}_\n\n⏳ Spark has your message and is processing it.",
                    "parse_mode": "Markdown"
                }
                try:
                    requests.post(confirm_url, json=confirm_payload, timeout=10)
                except Exception:
                    pass

        except requests.exceptions.RequestException:
            time.sleep(2)
        except Exception as e:
            log(f"[!] Poller error: {e}")
            time.sleep(2)

# Start poller thread
listener_thread = threading.Thread(target=telegram_poller, daemon=True)
listener_thread.start()

# =====================================================================
# MCP SERVER INITIALIZATION
# =====================================================================

app = MCPServer(
    name="AhmedGeminiSparkBridge",
    version="1.0.0",
    description="Two-way MCP bridge between Gemini Spark and Ahmed's phone via Telegram."
)

@app.tool()
def get_incoming_messages_from_ahmed(mark_as_read: bool = True) -> str:
    """
    Check if Ahmed has sent any new messages, questions, or task requests from his phone via Telegram.
    
    Args:
        mark_as_read: If True, marks fetched messages as read so they are not repeated.
    
    Returns:
        The text of new unread messages from Ahmed, or a notice if no new messages are waiting.
    """
    unread = inbox_manager.get_unread_messages(mark_as_read=mark_as_read)
    if not unread:
        return "No new unread messages from Ahmed's phone."

    formatted = []
    for m in unread:
        formatted.append(f"- [{m['timestamp']}] Ahmed says: \"{m['text']}\"")
    return "New message(s) from Ahmed:\n" + "\n".join(formatted)

@app.tool()
def reply_to_ahmed(message: str) -> str:
    """
    Sends Gemini Spark's answer, response, or status update directly back to Ahmed's phone on Telegram.
    
    Args:
        message: The response text to deliver to Ahmed's Telegram.
    """
    # Record reply in chat history
    inbox_manager.add_spark_reply(message)

    # Dispatch to phone
    telegram_text = f"✨ *Gemini Spark:*\n\n{message}"
    success = send_telegram(telegram_text)
    if success:
        return f"Successfully delivered reply to Ahmed's phone on Telegram: '{message}'"
    else:
        return "Failed to send reply to Ahmed. Check Telegram bot connection."

@app.tool()
def send_phone_notification(message: str) -> str:
    """
    Sends an urgent notification or proactive alert directly to Ahmed's phone via Telegram.
    
    Args:
        message: The alert or notification content to send.
    """
    inbox_manager.add_spark_reply(f"[Alert] {message}")
    success = send_headless_notification(f"🚨 *Alert from Spark:*\n{message}")
    if success:
        return f"Notification delivered to Ahmed's phone: '{message}'"
    else:
        return "Failed to deliver notification."

@app.tool()
def get_chat_history() -> str:
    """
    Retrieves the recent conversation history between Gemini Spark and Ahmed.
    """
    history = inbox_manager.get_conversation_history(limit=10)
    if not history:
        return "No conversation history yet."

    lines = []
    for h in history:
        lines.append(f"[{h['timestamp']}] {h['from']}: {h['text']}")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Gemini Spark Two-Way MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http", "http"],
        default="streamable-http",
        help="Transport type: 'streamable-http'/'http' (for Gemini Spark), 'sse', or 'stdio'"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", 8000)),
        help="Port for HTTP/SSE transport (reads $PORT from cloud environment)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("HOST", "0.0.0.0"),
        help="Host address (default: 0.0.0.0)"
    )
    args = parser.parse_args()

    sec_settings = TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
        allowed_hosts=["*"],
        allowed_origins=["*"]
    )

    if args.transport in ["streamable-http", "http"]:
        log(f"[*] Starting MCP Streamable HTTP Server on http://{args.host}:{args.port}/mcp ...")
        app.run(transport="streamable-http", host=args.host, port=args.port, transport_security=sec_settings)
    elif args.transport == "sse":
        log(f"[*] Starting MCP SSE Server on http://{args.host}:{args.port}/sse ...")
        app.run(transport="sse", host=args.host, port=args.port, transport_security=sec_settings)
    else:
        app.run(transport="stdio")

if __name__ == "__main__":
    main()
