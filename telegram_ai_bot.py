import os
import sys
import time
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(ENV_PATH)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip().replace("'", "").replace('"', "")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Initialize Gemini Client if key is available
gemini_client = None
chat_session = None

def init_gemini():
    global gemini_client, chat_session
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key == "your_gemini_api_key_here":
        return False
    try:
        from google import genai
        gemini_client = genai.Client(api_key=key)
        chat_session = gemini_client.chats.create(model="gemini-2.5-flash")
        print("[+] Gemini AI Chat initialized successfully with model: gemini-2.5-flash", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[!] Failed to initialize Gemini client: {e}", file=sys.stderr)
        return False

def send_reply(chat_id: str, text: str):
    """Sends a reply back to the user on Telegram."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        # Fallback if markdown parsing fails
        if not res.json().get("ok"):
            payload.pop("parse_mode")
            requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[!] Error sending reply: {e}", file=sys.stderr)

def send_typing(chat_id: str):
    """Shows 'typing...' status in Telegram chat."""
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendChatAction", json={"chat_id": chat_id, "action": "typing"}, timeout=5)
    except Exception:
        pass

def handle_message(user_msg: str, chat_id: str) -> str:
    """Processes user message with Gemini AI."""
    global chat_session

    if user_msg.strip() == "/start":
        return "👋 Hello Ahmed! I am your AI assistant connected to Gemini.\nAsk me anything, or send me instructions and I will reply right here!"

    if user_msg.strip() == "/clear":
        init_gemini()
        return "🧹 Memory cleared! Starting a fresh conversation."

    if not gemini_client:
        if not init_gemini():
            return (
                "⚠️ Gemini API Key not set yet!\n\n"
                "Please add your free Gemini API key to `.env`:\n"
                "`GEMINI_API_KEY=AIzaSy...`\n\n"
                "Get your key for free in 10 seconds at: https://aistudio.google.com"
            )

    try:
        send_typing(chat_id)
        response = chat_session.send_message(user_msg)
        return response.text
    except Exception as e:
        print(f"[!] Gemini generation error: {e}", file=sys.stderr)
        # Try re-initializing on failure
        init_gemini()
        return f"⚠️ Error communicating with Gemini: {str(e)[:150]}"

def run_bot():
    print("=" * 60, file=sys.stderr)
    print("   TELEGRAM <-> GEMINI AI TWO-WAY CHAT BOT ACTIVE", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    if not TOKEN:
        print("[!] TELEGRAM_BOT_TOKEN missing in .env", file=sys.stderr)
        return

    init_gemini()
    print("[*] Listening for messages from Ahmed on Telegram...", file=sys.stderr)

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
                user_text = msg.get("text", "")

                if not user_text:
                    continue

                # Security: Only respond to Ahmed's authorized chat
                if ALLOWED_CHAT_ID and chat_id != ALLOWED_CHAT_ID:
                    print(f"[!] Ignored message from unauthorized chat_id: {chat_id}", file=sys.stderr)
                    continue

                print(f"[User]: {user_text}", file=sys.stderr)
                reply = handle_message(user_text, chat_id)
                send_reply(chat_id, reply)
                print(f"[Gemini Reply sent to phone]", file=sys.stderr)

        except requests.exceptions.RequestException:
            time.sleep(2)
        except Exception as e:
            print(f"[!] Unexpected error in poll loop: {e}", file=sys.stderr)
            time.sleep(2)

if __name__ == "__main__":
    run_bot()
