# Headless Automation & Notification System

This system provides **100% headless background notifications** with **zero browser popups** (`0% GUI / 100% API`). It is designed for scripts, cron jobs, task automation, and background processes.

---

## Why Telegram is the Best Choice for Headless Automation
In WhatsApp, sending automated messages without opening a browser requires either paid enterprise APIs (Meta charges per conversation, Twilio is paid) or unofficial cloud gateways.

**Telegram**, on the other hand:
- Has an **official, free-forever API** specifically built for bots and automation.
- Requires **zero browser** — sends via a simple background HTTP request in `~0.1 seconds`.
- Never blocks accounts or rate-limits personal notifications.
- Directly reaches your account (**@ahmedallam111**) on both your phone and PC.

---

## 30-Second Setup Wizard (Telegram)

Run the automated setup wizard:
```powershell
.\.venv\Scripts\python main.py setup-telegram
```

The wizard will:
1. Prompt you to open `@BotFather` on Telegram and create a bot (`/newbot`).
2. Ask you to paste the bot token.
3. Automatically detect your Telegram user account when you press "Start".
4. Save your credentials to `.env` and immediately send a test confirmation!

---

## Using in Your Automation Scripts

Once configured, any script can send background alerts in one line:

### From the Command Line:
```powershell
.\.venv\Scripts\python main.py notify -m "✅ Database backup complete!"
```

### From Any Python Script:
```python
from notifier import send_headless_notification

# Your automation code here...
print("Processing data...")

# Send background alert when done:
send_headless_notification("🚀 Workflow completed successfully!")
```

---

## Alternative Cloud WhatsApp Option (Green-API)
If you also need WhatsApp messages sent headlessly from the cloud without a browser on your PC:
1. Register for a free Developer account at [green-api.com](https://green-api.com/).
2. Get your `idInstance` and `apiTokenInstance`.
3. Add them to `.env`:
   ```env
   GREEN_API_ID_INSTANCE=...
   GREEN_API_TOKEN=...
   ```
The script will automatically support headless WhatsApp dispatch.

---

## MCP Server (Model Context Protocol for Gemini Spark / AI)

You can connect your notifications directly into **Gemini Spark** or any MCP-compatible AI agent.

### Registered Tools:
- `send_phone_notification(message)`: Lets your AI agent send real-time alerts straight to your phone.
- `check_notification_status()`: Checks notification health and readiness.

### How to Connect to Gemini Spark:

#### Stdio Mode (Desktop AI Agents):
Add this to your MCP configuration (found in `mcp_config.json`):
```json
{
  "mcpServers": {
    "ahmed_productivity": {
      "command": "D:\\productivity\\.venv\\Scripts\\python.exe",
      "args": ["D:\\productivity\\mcp_server.py"],
      "env": {
        "PYTHONPATH": "D:\\productivity"
      }
    }
  }
}
```

#### SSE / Network Mode (Web / Cloud Agents):
Run:
```powershell
.\.venv\Scripts\python mcp_server.py --transport sse --port 8000
```
Then point your AI client to `http://localhost:8000/sse`.

