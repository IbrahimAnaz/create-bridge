#!/usr/bin/env python3
"""
Secure Web Dashboard & Cloudflare HTTPS REST Bridge (tools/http_bridge.py)
Provides:
  1. A full browser-based Web GUI with one-click actions: Doctor, Compile, Test-Client, File Editor, Logs.
  2. Pure GET & POST REST endpoints with token authentication packaged directly into the URL:
     - https://<tunnel>/<token>/doctor
     - https://<tunnel>/<token>/compile
     - https://<tunnel>/<token>/test-client
     - https://<tunnel>/<token>/read?path=...
     - https://<tunnel>/<token>/write?path=...&content=...
"""

import sys
import os
import json
import time
import hmac
import base64
import secrets
import subprocess
import urllib.parse
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import defaultdict

try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PORT = 8090

FAILED_ATTEMPTS = defaultdict(list)
BANNED_IPS = {}

HTML_DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Create Bridge | Remote Agent Dashboard</title>
<style>
  :root {
    --bg: #0f172a; --panel: #1e293b; --border: #334155; --text: #f8fafc;
    --text-muted: #94a3b8; --accent: #38bdf8; --green: #22c55e; --red: #ef4444;
    --amber: #f59e0b;
  }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg); color: var(--text); margin: 0; padding: 20px;
  }
  .container { max-width: 1100px; margin: 0 auto; }
  header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 15px; margin-bottom: 20px; }
  h1 { margin: 0; font-size: 1.5rem; display: flex; align-items: center; gap: 10px; }
  .badge { background: #0369a1; color: #e0f2fe; padding: 4px 10px; border-radius: 999px; font-size: 0.75rem; font-weight: bold; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  .card { background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 18px; margin-bottom: 20px; }
  .card h2 { margin-top: 0; font-size: 1.1rem; color: var(--accent); border-bottom: 1px solid var(--border); padding-bottom: 8px; }
  .btn-group { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; }
  button {
    background: #0284c7; color: white; border: none; padding: 10px 16px; border-radius: 6px;
    font-weight: 600; cursor: pointer; transition: all 0.15s ease; font-size: 0.88rem;
  }
  button:hover { background: #0369a1; transform: translateY(-1px); }
  button.btn-green { background: #16a34a; }
  button.btn-green:hover { background: #15803d; }
  button.btn-amber { background: #d97706; }
  button.btn-amber:hover { background: #b45309; }
  pre {
    background: #090d16; border: 1px solid var(--border); border-radius: 6px; padding: 14px;
    overflow-x: auto; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 0.82rem; line-height: 1.45; color: #cbd5e1; max-height: 420px; white-space: pre-wrap;
  }
  input, textarea, select {
    background: #090d16; border: 1px solid var(--border); color: var(--text); border-radius: 6px;
    padding: 8px 12px; font-family: inherit; font-size: 0.9rem; width: 100%; box-sizing: border-box;
  }
  textarea { min-height: 240px; font-family: monospace; line-height: 1.4; resize: vertical; }
  .form-group { margin-bottom: 12px; }
  label { display: block; margin-bottom: 4px; font-size: 0.82rem; color: var(--text-muted); }
  .status-tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }
  .status-online { background: #14532d; color: #86efac; }
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>⚙️ Create Bridge | Agent Console <span class="badge">HTTPS Active</span></h1>
    <div>Auth Token: <code style="color:var(--accent);">__TOKEN_DISPLAY__</code></div>
  </header>

  <div class="card">
    <h2>⚡ Quick Action Controls</h2>
    <div class="btn-group">
      <button onclick="runAction('doctor')">🩺 Run Diagnostics (Doctor)</button>
      <button class="btn-green" onclick="runAction('compile')">🔨 Hot Compile Extension</button>
      <button class="btn-amber" onclick="runAction('test-client')">🤖 Test Headless Bedrock Client</button>
      <button onclick="runAction('status')">📊 Check Service Status</button>
      <button onclick="fetchLogs('geyser')">📜 Geyser Logs</button>
      <button onclick="fetchLogs('inventory')">🎒 Inventory Logs</button>
    </div>
  </div>

  <div class="grid">
    <div class="card">
      <h2>🖥️ Action Console Output</h2>
      <div id="loading" style="display:none; color:var(--accent); font-weight:bold; margin-bottom:8px;">⏳ Processing request on host machine...</div>
      <pre id="output">Click any action above to execute on the host machine.</pre>
    </div>

    <div class="card">
      <h2>📝 File Inspector & Code Editor</h2>
      <div class="form-group">
        <label>Quick Presets or Custom Relative Path:</label>
        <select onchange="selectPreset(this.value)">
          <option value="">-- Choose preset or type below --</option>
          <option value="CLIENT_EMULATION_BACKEND_HANDOFF.md">CLIENT_EMULATION_BACKEND_HANDOFF.md</option>
          <option value="HANDOFF.md">HANDOFF.md</option>
          <option value="portable_bridge/extension/src/com/createbridge/network/PacketInterceptorManager.java">PacketInterceptorManager.java</option>
          <option value="portable_bridge/extension/src/com/createbridge/network/BridgeSyncServer.java">BridgeSyncServer.java</option>
          <option value="headless_server/companion_mod/src/main/java/com/createbridge/companion/mixin/DepotBehaviourMixin.java">DepotBehaviourMixin.java</option>
          <option value="tools/dummy_bedrock/dummy_client.js">dummy_client.js</option>
        </select>
      </div>
      <div class="form-group">
        <input type="text" id="filepath" placeholder="relative/path/to/file.ext" value="HANDOFF.md">
      </div>
      <div class="btn-group" style="margin-bottom:12px;">
        <button onclick="loadFile()">📥 Read File</button>
        <button class="btn-green" onclick="saveFile(false)">💾 Save File</button>
        <button class="btn-amber" onclick="saveFile(true)">💾 Save & Recompile</button>
      </div>
      <textarea id="filecontent" placeholder="File content will load here..."></textarea>
    </div>
  </div>
</div>

<script>
const TOKEN = "__TOKEN_RAW__";
const BASE_URL = window.location.origin;

function getAuthUrl(endpoint) {
  const delim = endpoint.includes('?') ? '&' : '?';
  return `${BASE_URL}/${TOKEN}/${endpoint.replace(/^\\//, '')}`;
}

async function runAction(action) {
  const out = document.getElementById('output');
  const load = document.getElementById('loading');
  load.style.display = 'block';
  out.textContent = `Executing ${action}...`;
  try {
    const res = await fetch(getAuthUrl(action));
    const data = await res.json();
    out.textContent = data.stdout || data.output || JSON.stringify(data, null, 2);
  } catch (e) {
    out.textContent = `Request failed: ${e.message}`;
  } finally {
    load.style.display = 'none';
  }
}

async function fetchLogs(service) {
  const out = document.getElementById('output');
  out.textContent = `Fetching ${service} logs...`;
  try {
    const res = await fetch(getAuthUrl(`logs?service=${service}&lines=40`));
    const data = await res.json();
    out.textContent = data.output || JSON.stringify(data, null, 2);
  } catch (e) {
    out.textContent = `Error: ${e.message}`;
  }
}

function selectPreset(val) {
  if (val) {
    document.getElementById('filepath').value = val;
    loadFile();
  }
}

async function loadFile() {
  const path = document.getElementById('filepath').value.trim();
  const area = document.getElementById('filecontent');
  const out = document.getElementById('output');
  if (!path) return alert('Enter a file path');
  area.value = "Loading file...";
  try {
    const res = await fetch(getAuthUrl(`read?path=${encodeURIComponent(path)}`));
    const data = await res.json();
    if (data.content !== undefined) {
      area.value = data.content;
      out.textContent = `Successfully loaded ${path} (${data.bytes} bytes)`;
    } else {
      area.value = "";
      out.textContent = data.error || "Failed to load file.";
    }
  } catch (e) {
    area.value = "";
    out.textContent = `Read error: ${e.message}`;
  }
}

async function saveFile(andCompile) {
  const path = document.getElementById('filepath').value.trim();
  const content = document.getElementById('filecontent').value;
  const out = document.getElementById('output');
  if (!path) return alert('Enter a file path');
  out.textContent = `Saving ${path}...`;
  try {
    const res = await fetch(getAuthUrl('write'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, content })
    });
    const data = await res.json();
    if (data.status === 'success') {
      out.textContent = `File saved: ${path} (${data.bytes} bytes)`;
      if (andCompile) {
        runAction('compile');
      }
    } else {
      out.textContent = data.error || "Save failed.";
    }
  } catch (e) {
    out.textContent = `Write error: ${e.message}`;
  }
}
</script>
</body>
</html>
"""

class SecureBridgeHandler(BaseHTTPRequestHandler):
    auth_token = ""

    def log_message(self, format, *args):
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {self.client_address[0]} - {format % args}")

    def _check_rate_limit(self, client_ip):
        now = time.time()
        if client_ip in BANNED_IPS:
            if now < BANNED_IPS[client_ip]:
                remaining = int(BANNED_IPS[client_ip] - now)
                self.send_response(429)
                self.send_header("Content-Type", "application/json")
                self.send_header("Retry-After", str(remaining))
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Too many failed attempts. Try again in {remaining}s."}).encode("utf-8"))
                return False
            else:
                del BANNED_IPS[client_ip]
        return True

    def _record_failed_auth(self, client_ip):
        now = time.time()
        FAILED_ATTEMPTS[client_ip] = [t for t in FAILED_ATTEMPTS[client_ip] if now - t < 60]
        FAILED_ATTEMPTS[client_ip].append(now)
        if len(FAILED_ATTEMPTS[client_ip]) >= 5:
            ban_until = now + 60
            BANNED_IPS[client_ip] = ban_until
            print(f"[SECURITY ALERT] IP {client_ip} banned for 60s due to 5 consecutive failed auth attempts!")

    def _extract_and_validate_token(self):
        """Extracts token from URL path (/<token>/...), query param ?token=, or headers."""
        client_ip = self.client_address[0]
        if not self._check_rate_limit(client_ip):
            return None, False

        provided = ""
        clean_path = self.path

        # 1. Check path prefix: /<token>/endpoint...
        path_parts = self.path.lstrip("/").split("/", 1)
        if len(path_parts) > 0 and path_parts[0]:
            candidate = path_parts[0]
            if hmac.compare_digest(candidate, self.auth_token):
                provided = candidate
                clean_path = "/" + (path_parts[1] if len(path_parts) > 1 else "")

        # 2. Check query param: ?token=
        if not provided:
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            if "token" in params:
                cand = params["token"][0].strip()
                if hmac.compare_digest(cand, self.auth_token):
                    provided = cand

        # 3. Check Authorization header
        if not provided:
            auth_hdr = self.headers.get("Authorization", "")
            if auth_hdr.lower().startswith("bearer "):
                cand = auth_hdr[7:].strip()
                if hmac.compare_digest(cand, self.auth_token):
                    provided = cand

        # 4. Check X-Bridge-Token header
        if not provided:
            cand = self.headers.get("X-Bridge-Token", "").strip()
            if cand and hmac.compare_digest(cand, self.auth_token):
                provided = cand

        if provided:
            FAILED_ATTEMPTS.pop(client_ip, None)
            return clean_path, True

        self._record_failed_auth(client_ip)
        self.send_response(401)
        self.send_header("Content-Type", "application/json")
        self.send_header("WWW-Authenticate", 'Bearer realm="CreateBridge"')
        self.end_headers()
        self.wfile.write(json.dumps({
            "error": "Unauthorized: Valid token required.",
            "usage": "Include token in URL: https://<tunnel>/<token>/ or ?token=<token>"
        }).encode("utf-8"))
        return None, False

    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def _send_html(self, html, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _resolve_safe_path(self, target_rel):
        cleaned = target_rel.replace("\\", "/").lstrip("/")
        blocked_prefixes = [".git", "node_modules", "id_rsa", "id_ed25519", ".env"]
        for b in blocked_prefixes:
            if cleaned.startswith(b) or f"/{b}" in cleaned:
                return None
        target = (BASE_DIR / cleaned).resolve()
        try:
            target.relative_to(BASE_DIR.resolve())
            return target
        except ValueError:
            return None

    def do_OPTIONS(self):
        self._send_json({"status": "ok"})

    def do_GET(self):
        clean_path, authed = self._extract_and_validate_token()
        if not authed:
            return

        parsed = urllib.parse.urlparse(clean_path)
        path = parsed.path.rstrip("/")
        params = urllib.parse.parse_qs(parsed.query)

        # Serve Web UI Dashboard when hitting root or /dashboard
        if path in ["", "/dashboard"]:
            display_tok = self.auth_token[:8] + "..." + self.auth_token[-4:]
            html = HTML_DASHBOARD_TEMPLATE.replace("__TOKEN_RAW__", self.auth_token).replace("__TOKEN_DISPLAY__", display_tok)
            self._send_html(html)
            return

        if path == "/status":
            res = subprocess.run([sys.executable, str(BASE_DIR / "tools" / "bridge.py"), "status"], capture_output=True, text=True, cwd=BASE_DIR)
            self._send_json({
                "status": "online",
                "authenticated": True,
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "output": res.stdout.strip()
            })

        elif path == "/doctor":
            res = subprocess.run([sys.executable, str(BASE_DIR / "tools" / "bridge.py"), "doctor"], capture_output=True, text=True, cwd=BASE_DIR)
            self._send_json({"returncode": res.returncode, "stdout": res.stdout, "stderr": res.stderr})

        elif path == "/compile":
            print("[Web Bridge] Hot compiling bridge extension...")
            res = subprocess.run([sys.executable, str(BASE_DIR / "tools" / "compile_bridge.py")], capture_output=True, text=True, cwd=BASE_DIR)
            self._send_json({"returncode": res.returncode, "stdout": res.stdout, "stderr": res.stderr})

        elif path == "/test-client":
            print("[Web Bridge] Executing headless Bedrock protocol client test...")
            res = subprocess.run(["node", str(BASE_DIR / "tools" / "dummy_bedrock" / "dummy_client.js")], capture_output=True, text=True, cwd=BASE_DIR, timeout=25)
            self._send_json({"returncode": res.returncode, "stdout": res.stdout, "stderr": res.stderr})

        elif path == "/read":
            target = params.get("path", [""])[0]
            if not target:
                self._send_json({"error": "Missing 'path' query parameter"}, 400)
                return
            safe_file = self._resolve_safe_path(target)
            if not safe_file:
                self._send_json({"error": "Access denied: Path out of bounds or restricted"}, 403)
                return
            if not safe_file.exists():
                self._send_json({"error": f"File not found: {target}"}, 404)
                return
            try:
                content = safe_file.read_text(encoding="utf-8", errors="replace")
                self._send_json({"path": target, "bytes": len(content), "content": content})
            except Exception as e:
                self._send_json({"error": str(e)}, 500)

        elif path == "/write":
            # Allow writing via GET URL (using ?path=...&content=... or ?path=...&b64=...)
            target = params.get("path", [""])[0]
            if not target:
                self._send_json({"error": "Missing 'path'"}, 400)
                return
            if "b64" in params:
                try:
                    content = base64.b64decode(params["b64"][0]).decode("utf-8")
                except Exception as be:
                    self._send_json({"error": f"Invalid base64: {be}"}, 400)
                    return
            else:
                content = params.get("content", [""])[0]

            safe_file = self._resolve_safe_path(target)
            if not safe_file:
                self._send_json({"error": "Access denied: Path restricted"}, 403)
                return
            try:
                safe_file.parent.mkdir(parents=True, exist_ok=True)
                safe_file.write_text(content, encoding="utf-8")
                print(f"[Web Bridge GET] Updated {target} ({len(content)} bytes)")
                self._send_json({"status": "success", "path": target, "bytes": len(content)})
            except Exception as e:
                self._send_json({"error": str(e)}, 500)

        elif path == "/logs":
            service = params.get("service", ["geyser"])[0]
            lines = int(params.get("lines", [50])[0])
            res = subprocess.run([sys.executable, str(BASE_DIR / "tools" / "bridge.py"), "logs", service, "-n", str(lines)], capture_output=True, text=True, cwd=BASE_DIR)
            self._send_json({"service": service, "output": res.stdout})

        else:
            self._send_json({
                "error": "Not Found",
                "available_endpoints": [
                    "/dashboard",
                    "/status",
                    "/doctor",
                    "/compile",
                    "/test-client",
                    "/read?path=<file>",
                    "/write?path=<file>&content=<text>",
                    "/logs?service=geyser"
                ]
            }, 404)

    def do_POST(self):
        clean_path, authed = self._extract_and_validate_token()
        if not authed:
            return

        parsed = urllib.parse.urlparse(clean_path)
        path = parsed.path.rstrip("/")
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else ""

        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        if path == "/write":
            target = payload.get("path", "")
            content = payload.get("content", "")
            if not target:
                self._send_json({"error": "Missing 'path'"}, 400)
                return
            safe_file = self._resolve_safe_path(target)
            if not safe_file:
                self._send_json({"error": "Access denied: Path restricted"}, 403)
                return
            try:
                safe_file.parent.mkdir(parents=True, exist_ok=True)
                safe_file.write_text(content, encoding="utf-8")
                print(f"[Web Bridge POST] Updated {target} ({len(content)} bytes)")
                self._send_json({"status": "success", "path": target, "bytes": len(content)})
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif path == "/compile":
            res = subprocess.run([sys.executable, str(BASE_DIR / "tools" / "compile_bridge.py")], capture_output=True, text=True, cwd=BASE_DIR)
            self._send_json({"returncode": res.returncode, "stdout": res.stdout, "stderr": res.stderr})
        elif path == "/test-client":
            res = subprocess.run(["node", str(BASE_DIR / "tools" / "dummy_bedrock" / "dummy_client.js")], capture_output=True, text=True, cwd=BASE_DIR, timeout=25)
            self._send_json({"returncode": res.returncode, "stdout": res.stdout, "stderr": res.stderr})
        else:
            self._send_json({"error": "Not Found"}, 404)

def run_server(port=DEFAULT_PORT, token=None):
    if not token:
        token = secrets.token_urlsafe(32)

    SecureBridgeHandler.auth_token = token
    server = HTTPServer(("127.0.0.1", port), SecureBridgeHandler)

    print("\n" + "="*70)
    print("CREATE MOD BRIDGE - SECURE WEB DASHBOARD & REST BRIDGE")
    print("="*70)
    print(f"[*] Origin Port: http://127.0.0.1:{port}")
    print(f"[*] Secret Token: {token}")
    print("="*70)

    print("\n[+] Launching Cloudflare Quick Tunnel...")
    cf_proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace"
    )

    import re
    tunnel_url = None
    start = time.time()
    while time.time() - start < 18:
        line = cf_proc.stdout.readline()
        if not line:
            time.sleep(0.1)
            continue
        m = re.search(r"https://(?!api\.)[a-zA-Z0-9-]+\.trycloudflare\.com", line)
        if m:
            tunnel_url = m.group(0)
            break

    if tunnel_url:
        dashboard_url = f"{tunnel_url}/{token}/"
        endpoint_info = {
            "protocol": "https",
            "url": tunnel_url,
            "token": token,
            "dashboard_url": dashboard_url,
            "port": port,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        endpoint_file = BASE_DIR / ".bridge_actions" / "endpoint.json"
        endpoint_file.parent.mkdir(parents=True, exist_ok=True)
        endpoint_file.write_text(json.dumps(endpoint_info, indent=2), encoding="utf-8")

        print("\n" + "="*70, flush=True)
        print(f">>> LIVE WEB DASHBOARD URL (Browser / Zero cURL needed): <<<", flush=True)
        print(f"    {dashboard_url}", flush=True)
        print("="*70, flush=True)
        print(f"\nAll operations are packaged directly into the URL (pure GET):\n", flush=True)
        print(f"  Diagnostics:  {tunnel_url}/{token}/doctor", flush=True)
        print(f"  Compile:      {tunnel_url}/{token}/compile", flush=True)
        print(f"  Test Client:  {tunnel_url}/{token}/test-client", flush=True)
        print(f"  Read File:    {tunnel_url}/{token}/read?path=HANDOFF.md", flush=True)
        print(f"  Write File:   {tunnel_url}/{token}/write?path=...&content=...", flush=True)
        print("="*70 + "\n", flush=True)
    else:
        print("[!] Tunnel established. Listening for requests...")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[+] Shutting down bridge and closing Cloudflare tunnel...")
        cf_proc.terminate()
        server.server_close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Secure Web Dashboard & REST Bridge")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to listen on (default: 8090)")
    parser.add_argument("--token", help="Pre-shared token (auto-generated if omitted)")
    args = parser.parse_args()
    run_server(args.port, args.token)
