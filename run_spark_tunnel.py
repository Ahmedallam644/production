import os
import sys
import re
import time
import subprocess
import threading

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

CLOUDFLARED_BIN = r"C:\Program Files (x86)\cloudflared\cloudflared.exe"
PYTHON_EXE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "Scripts", "python.exe")
MCP_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_server.py")
URL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spark_url.txt")
PORT = 8000

def main():
    print("=" * 70, flush=True)
    print("   STARTING GEMINI SPARK MCP SERVER & SECURE TUNNEL", flush=True)
    print("=" * 70, flush=True)

    # 1. Start the MCP server process without pipe buffering (direct std streams)
    print(f"[*] Starting local MCP server on port {PORT}...", flush=True)
    server_proc = subprocess.Popen(
        [PYTHON_EXE, "-u", MCP_SCRIPT, "--transport", "streamable-http", "--port", str(PORT)],
        stdout=sys.stdout,
        stderr=sys.stderr
    )

    time.sleep(2)
    if server_proc.poll() is not None:
        print("[!] Local MCP server exited early.", flush=True)
        return

    # 2. Start cloudflared tunnel
    print(f"[*] Launching Cloudflare Tunnel from {CLOUDFLARED_BIN}...", flush=True)
    cf_proc = subprocess.Popen(
        [CLOUDFLARED_BIN, "tunnel", "--url", f"http://127.0.0.1:{PORT}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    tunnel_url = None
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    def read_cf():
        nonlocal tunnel_url
        for line in cf_proc.stderr:
            match = url_pattern.search(line)
            if match and not tunnel_url:
                tunnel_url = match.group(0)
                mcp_link = f"{tunnel_url}/mcp"
                try:
                    with open(URL_FILE, "w", encoding="utf-8") as f:
                        f.write(mcp_link)
                except Exception:
                    pass
                print("\n" + "=" * 70, flush=True)
                print("           [+] GEMINI SPARK MCP CONNECTION LINK READY!", flush=True)
                print("=" * 70, flush=True)
                print(" -> Copy this exact URL:", flush=True)
                print(f"\n    {mcp_link}\n", flush=True)
                print(" -> In Gemini Spark:", flush=True)
                print("    1. Paste this link into 'Add a custom app link to get started'", flush=True)
                print("    2. Click 'Next'", flush=True)
                print("=" * 70, flush=True)
                print("[*] Server is active and ready for Gemini Spark requests!\n", flush=True)

    t = threading.Thread(target=read_cf, daemon=True)
    t.start()

    # Wait for tunnel URL
    for _ in range(40):
        if tunnel_url:
            break
        time.sleep(1)

    if not tunnel_url:
        print("[!] Tunnel URL not detected. Please check cloudflared output.", flush=True)

    try:
        while True:
            time.sleep(1)
            if server_proc.poll() is not None:
                print("[!] MCP server process exited.", flush=True)
                break
            if cf_proc.poll() is not None:
                print("[!] Cloudflare tunnel process exited.", flush=True)
                break
    except KeyboardInterrupt:
        print("\n[*] Stopping...", flush=True)
    finally:
        server_proc.terminate()
        cf_proc.terminate()

if __name__ == "__main__":
    main()
