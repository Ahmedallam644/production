import os
import sys
import time
import subprocess
import urllib.parse
import requests
from dotenv import load_dotenv, set_key

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def log(msg: str):
    """Logs to stderr so MCP stdio JSON-RPC protocol is never corrupted."""
    print(msg, file=sys.stderr)

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(ENV_PATH)

DEFAULT_TOPIC = os.getenv("NTFY_TOPIC", "ahmedallam111_alerts")

# =====================================================================
# 1. NTFY PUSH NOTIFICATIONS (100% FREE, ZERO SIGNUP, HEADLESS PUSH TO PHONE)
# =====================================================================

def send_ntfy(message: str, topic: str | None = None) -> bool:
    """
    Sends an instant push notification to phone/desktop via ntfy.sh.
    Zero accounts, zero API keys, 100% headless HTTP POST.
    Subscribe on your phone (Android/iOS ntfy app) to the topic to get instant ring/vibrate.
    """
    target_topic = topic or os.getenv("NTFY_TOPIC", DEFAULT_TOPIC)
    url = f"https://ntfy.sh/{target_topic}"
    try:
        res = requests.post(
            url,
            data=message.encode("utf-8"),
            headers={
                "Title": "Productivity Automation",
                "Priority": "high",
                "Tags": "robot,bell"
            },
            timeout=10
        )
        if res.status_code == 200:
            log(f"[+] Push notification sent to topic: {target_topic}")
            return True
        else:
            log(f"[!] ntfy error ({res.status_code}): {res.text}")
            return False
    except requests.exceptions.RequestException as e:
        log(f"[!] Network error sending ntfy notification: {e}")
        return False

# =====================================================================
# 2. TELEGRAM (OFFICIAL API, 100% FREE, HEADLESS, FOR @ahmedallam111)
# =====================================================================

def send_telegram(message: str, chat_id: str | None = None, bot_token: str | None = None) -> bool:
    """
    Sends a message via Telegram Bot API silently in the background (0 browser).
    """
    token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    target_chat = chat_id or os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token or not target_chat:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": target_chat,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        res = requests.post(url, json=payload, timeout=10)
        data = res.json()
        if data.get("ok"):
            log(f"[+] Telegram notification successfully sent to @ahmedallam111!")
            return True
        else:
            log(f"[!] Telegram API error: {data.get('description')}")
            return False
    except requests.exceptions.RequestException as e:
        log(f"[!] Network error sending Telegram message: {e}")
        return False

def setup_telegram_wizard() -> bool:
    """
    Interactive 30-second setup wizard for Telegram notifications.
    Guides the user to create a bot with @BotFather, captures chat ID, and saves to .env.
    """
    print("\n" + "=" * 65)
    print("        TELEGRAM HEADLESS NOTIFICATION SETUP (30 SECONDS)")
    print("=" * 65)
    print("1. Open Telegram on your phone or PC and search for: @BotFather")
    print("2. Send: /newbot")
    print("3. Give your bot a name (e.g. Ahmed Productivity)")
    print("4. Give it a username ending in 'bot' (e.g. ahmedallam_alert_bot)")
    print("5. BotFather will provide an HTTP API token (e.g. 123456789:ABCdefGhI...)\n")
    
    token = input("Paste your Bot Token here: ").strip()
    if not token:
        print("[!] Setup cancelled: Token cannot be empty.")
        return False

    # Verify token
    try:
        verify_res = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        verify_data = verify_res.json()
        if not verify_data.get("ok"):
            print(f"[!] Invalid Token: {verify_data.get('description')}")
            return False
        bot_username = verify_data["result"]["username"]
        print(f"\n[+] Token verified! Connected to bot: @{bot_username}")
    except Exception as e:
        print(f"[!] Connection failed: {e}")
        return False

    print("\n" + "-" * 65)
    print(f"ACTION REQUIRED: Open your bot in Telegram: https://t.me/{bot_username}")
    print("Click 'START' (or send any message like 'hello') to link your account.")
    print("-" * 65)
    print("[*] Waiting to detect your chat ID (listening for your message)...")

    # Clear previous updates
    try:
        requests.get(f"https://api.telegram.org/bot{token}/getUpdates?offset=-1", timeout=10)
    except Exception:
        pass

    chat_id = None
    for _ in range(30):
        time.sleep(2)
        try:
            updates_res = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)
            updates = updates_res.json().get("result", [])
            if updates:
                last_msg = updates[-1].get("message", {})
                chat = last_msg.get("chat", {})
                if chat.get("id"):
                    chat_id = str(chat["id"])
                    first_name = chat.get("first_name", "")
                    username = chat.get("username", "")
                    print(f"\n[+] User detected: {first_name} (@{username}) with Chat ID: {chat_id}")
                    break
        except Exception:
            pass

    if not chat_id:
        print("[!] Timeout: No message received. Please start the bot and try again.")
        return False

    # Save to .env
    set_key(ENV_PATH, "TELEGRAM_BOT_TOKEN", token)
    set_key(ENV_PATH, "TELEGRAM_CHAT_ID", chat_id)
    os.environ["TELEGRAM_BOT_TOKEN"] = token
    os.environ["TELEGRAM_CHAT_ID"] = chat_id

    print(f"[+] Credentials saved to .env successfully!")
    print("[*] Sending a test message...")
    send_telegram("🚀 *Setup Complete!* Headless background notifications are now active and ready for automation.", chat_id=chat_id, bot_token=token)
    return True

# =====================================================================
# 3. WINDOWS NATIVE TOAST (HEADLESS DESKTOP POPUP - 0 BROWSER)
# =====================================================================

def send_windows_toast(title: str, message: str) -> bool:
    """Displays a native Windows toast notification banner silently."""
    clean_msg = message.replace('"', '`"').replace("'", "`'")
    clean_title = title.replace('"', '`"').replace("'", "`'")
    ps_cmd = (
        f"[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; "
        f"$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
        f"$textNodes = $template.GetElementsByTagName('text'); "
        f"$textNodes.Item(0).AppendChild($template.CreateTextNode('{clean_title}')) | Out-Null; "
        f"$textNodes.Item(1).AppendChild($template.CreateTextNode('{clean_msg}')) | Out-Null; "
        f"$toast = [Windows.UI.Notifications.ToastNotification]::new($template); "
        f"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Productivity Automation').Show($toast);"
    )
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, timeout=5)
        return True
    except Exception:
        return False

# =====================================================================
# UNIFIED HEADLESS DISPATCHER (WORKS IMMEDIATELY)
# =====================================================================

def send_headless_notification(message: str) -> bool:
    """
    Sends a silent background notification directly to your phone via Telegram.
    Zero laptop toast popups, zero browser windows.
    """
    log(f"[*] Sending notification to your phone: '{message}'...")

    # Send directly to your phone via Telegram
    if os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
        return send_telegram(message)
    
    # Fallback to ntfy if Telegram is not configured
    return send_ntfy(message)


if __name__ == "__main__":
    send_headless_notification("🚀 Productivity automation system is fully operational!")
