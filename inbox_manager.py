import os
import json
import time

INBOX_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_history.json")

def _load_data():
    if not os.path.exists(INBOX_FILE):
        return {"messages": []}
    try:
        with open(INBOX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"messages": []}

def _save_data(data):
    try:
        with open(INBOX_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[!] Error saving chat history: {e}")

def add_user_message(sender: str, text: str):
    """Stores a message received from Ahmed's phone."""
    data = _load_data()
    msg_id = len(data["messages"]) + 1
    entry = {
        "id": msg_id,
        "from": sender,
        "text": text,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "role": "user",
        "unread": True
    }
    data["messages"].append(entry)
    _save_data(data)
    return entry

def add_spark_reply(text: str):
    """Stores a reply sent by Gemini Spark."""
    data = _load_data()
    msg_id = len(data["messages"]) + 1
    entry = {
        "id": msg_id,
        "from": "Gemini Spark",
        "text": text,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "role": "assistant",
        "unread": False
    }
    data["messages"].append(entry)
    _save_data(data)
    return entry

def get_unread_messages(mark_as_read: bool = True):
    """Retrieves unread messages from Ahmed for Gemini Spark."""
    data = _load_data()
    unread = [m for m in data["messages"] if m.get("unread") and m.get("role") == "user"]
    if mark_as_read and unread:
        for m in data["messages"]:
            if m.get("unread"):
                m["unread"] = False
        _save_data(data)
    return unread

def get_conversation_history(limit: int = 15):
    """Returns the recent conversation history."""
    data = _load_data()
    return data["messages"][-limit:]
