#!/usr/bin/env python3
"""
Secure HTTP & Cloudflare REST Bridge (tools/http_bridge.py)
Exposes local directory read/write and server execution over a secure Cloudflare Tunnel
guarded by mandatory cryptographic token authentication, constant-time verification,
failed attempt rate-limiting, and strict filesystem sandboxing.

Usage:
  python tools/http_bridge.py [--port 8090] [--token <SECRET_KEY>]
"""

import sys
import os
import json
import time
import hmac
import secrets
import subprocess
import urllib.parse
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PORT = 8090

# Rate limiting for failed authentication attempts: max 5 failures per 60 seconds
FAILED_ATTEMPTS = defaultdict(list)
BANNED_IPS = {}

class SecureBridgeHandler(BaseHTTPRequestHandler):
    auth_token = ""

    def log_message(self, format, *args):
        # Custom clean timestamped log
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {self.client_address[0]} - {format % args}")

    def _check_rate_limit(self, client_ip):
        now = time.time()
        # Check if currently banned
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
        # Prune old failures (> 60s)
        FAILED_ATTEMPTS[client_ip] = [t for t in FAILED_ATTEMPTS[client_ip] if now - t < 60]
        FAILED_ATTEMPTS[client_ip].append(now)

        if len(FAILED_ATTEMPTS[client_ip]) >= 5:
            ban_until = now + 60
            BANNED_IPS[client_ip] = ban_until
            print(f"[SECURITY ALERT] IP {client_ip} banned for 60s due to 5 consecutive failed auth attempts!")

    def _check_auth(self):
        client_ip = self.client_address[0]
        if not self._check_rate_limit(client_ip):
            return False

        provided = ""
        # 1. Check Authorization header (Bearer <token>)
        auth_hdr = self.headers.get("Authorization", "")
        if auth_hdr.lower().startswith("bearer "):
            provided = auth_hdr[7:].strip()

        # 2. Check X-Bridge-Token header
        if not provided:
            provided = self.headers.get("X-Bridge-Token", "").strip()

        # 3. Check query param ?token=
        if not provided:
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            provided = params.get("token", [""])[0].strip()

        # Constant-time comparison to prevent timing attacks
        if provided and hmac.compare_digest(provided, self.auth_token):
            # Reset failures on successful auth
            FAILED_ATTEMPTS.pop(client_ip, None)
            return True

        self._record_failed_auth(client_ip)
        self.send_response(401)
        self.send_header("Content-Type", "application/json")
        self.send_header("WWW-Authenticate", 'Bearer realm="CreateBridge"')
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Unauthorized: Valid token required"}).encode("utf-8"))
        return False

    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Bridge-Token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def _resolve_safe_path(self, target_rel):
        """Strictly sandboxes target_rel within BASE_DIR, blocking sensitive folders."""
        cleaned = target_rel.replace("\\", "/").lstrip("/")
        # Disallow access to .git, private keys, or root files
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
        if not self._check_auth():
            return

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path in ["/", "/status"]:
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

        elif path == "/logs":
            service = params.get("service", ["geyser"])[0]
            lines = int(params.get("lines", [50])[0])
            res = subprocess.run([sys.executable, str(BASE_DIR / "tools" / "bridge.py"), "logs", service, "-n", str(lines)], capture_output=True, text=True, cwd=BASE_DIR)
            self._send_json({"service": service, "output": res.stdout})

        else:
            self._send_json({
                "error": "Not Found",
                "available_endpoints": [
                    "/status",
                    "/doctor",
                    "/read?path=<file>",
                    "/logs?service=geyser&lines=50",
                    "POST /write",
                    "POST /compile",
                    "POST /test-client",
                    "POST /action"
                ]
            }, 404)

    def do_POST(self):
        if not self._check_auth():
            return

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
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
                self._send_json({"error": "Missing 'path' parameter"}, 400)
                return
            safe_file = self._resolve_safe_path(target)
            if not safe_file:
                self._send_json({"error": "Access denied: Path out of bounds or restricted"}, 403)
                return
            try:
                safe_file.parent.mkdir(parents=True, exist_ok=True)
                safe_file.write_text(content, encoding="utf-8")
                print(f"[HTTP Bridge] Updated {target} ({len(content)} bytes)")
                self._send_json({"status": "success", "path": target, "bytes": len(content)})
            except Exception as e:
                self._send_json({"error": str(e)}, 500)

        elif path == "/compile":
            print("[HTTP Bridge] Compiling bridge extension...")
            res = subprocess.run([sys.executable, str(BASE_DIR / "tools" / "compile_bridge.py")], capture_output=True, text=True, cwd=BASE_DIR)
            self._send_json({"returncode": res.returncode, "stdout": res.stdout, "stderr": res.stderr})

        elif path == "/test-client":
            print("[HTTP Bridge] Executing headless Bedrock protocol client test...")
            res = subprocess.run(["node", str(BASE_DIR / "tools" / "dummy_bedrock" / "dummy_client.js")], capture_output=True, text=True, cwd=BASE_DIR, timeout=25)
            self._send_json({"returncode": res.returncode, "stdout": res.stdout, "stderr": res.stderr})

        elif path == "/action":
            action = payload.get("action", "doctor")
            from tools.github_bridge import ACTIONS_DIR, REQUEST_FILE, process_remote_actions
            req_id = f"sec-http-{int(time.time()*1000)}"
            ACTIONS_DIR.mkdir(parents=True, exist_ok=True)
            with open(REQUEST_FILE, "w", encoding="utf-8") as f:
                json.dump({"id": req_id, "action": action, "params": payload.get("params", {})}, f)
            process_remote_actions("origin", "master")
            resp_file = ACTIONS_DIR / "response.json"
            if resp_file.exists():
                data = json.loads(resp_file.read_text(encoding="utf-8"))
                self._send_json(data)
            else:
                self._send_json({"error": "Action execution failed"}, 500)
        else:
            self._send_json({"error": "Not Found"}, 404)

def run_server(port=DEFAULT_PORT, token=None):
    # Mandatory cryptographic token generation if none supplied
    if not token:
        token = secrets.token_urlsafe(32)

    SecureBridgeHandler.auth_token = token
    server = HTTPServer(("127.0.0.1", port), SecureBridgeHandler)
    
    print("\n" + "="*70)
    print("CREATE MOD BRIDGE - SECURE CLOUDFLARE REST BRIDGE")
    print("="*70)
    print(f"[*] Local Origin Port: http://127.0.0.1:{port}")
    print(f"[*] Mandatory Pre-Shared Secret Token:")
    print(f"\n      {token}\n")
    print("[*] Authentication Requirements:")
    print(f"      - Header:   'Authorization: Bearer {token}'")
    print(f"      - Or Header: 'X-Bridge-Token: {token}'")
    print(f"      - Or Param:  '?token={token}'")
    print("[*] Brute-Force Shield: Auto-bans IPs for 60s after 5 invalid attempts.")
    print("[*] Strict Sandbox: Paths outside workspace root are rejected.")
    print("="*70)

    # Launch cloudflared tunnel
    print("\n[+] Launching Cloudflare Quick Tunnel...")
    cf_proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace"
    )

    tunnel_url = None
    start = time.time()
    while time.time() - start < 15:
        line = cf_proc.stdout.readline()
        if "trycloudflare.com" in line:
            for part in line.split():
                if "trycloudflare.com" in part and part.startswith("http"):
                    tunnel_url = part.strip()
                    break
            if tunnel_url:
                break

    if tunnel_url:
        print("\n" + "="*70)
        print(f">>> LIVE SECURE ENDPOINT: {tunnel_url} <<<")
        print("="*70)
        print("\nReady-to-use cURL commands for the remote Web IDE / agent:\n")
        print(f"1. Check Diagnostics:")
        print(f'   curl -H "Authorization: Bearer {token}" {tunnel_url}/doctor\n')
        print(f"2. Read Source File:")
        print(f'   curl -H "Authorization: Bearer {token}" "{tunnel_url}/read?path=HANDOFF.md"\n')
        print(f"3. Recompile Extension:")
        print(f'   curl -X POST -H "Authorization: Bearer {token}" {tunnel_url}/compile\n')
        print(f"4. Test Bedrock Client:")
        print(f'   curl -X POST -H "Authorization: Bearer {token}" {tunnel_url}/test-client\n')
        print("="*70 + "\n")
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
    parser = argparse.ArgumentParser(description="Secure HTTP & Cloudflare REST Bridge")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to listen on (default: 8090)")
    parser.add_argument("--token", help="Pre-shared token (auto-generated if omitted)")
    args = parser.parse_args()
    run_server(args.port, args.token)
