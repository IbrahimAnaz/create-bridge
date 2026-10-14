#!/usr/bin/env python3
"""
Remote CLI for Web IDE (tools/remote_cli.py)
Run this inside your Web IDE (Codespaces, cloud VM, or remote IDE terminal)
to execute actions, diagnostics, tests, and compilation on the host Minecraft server!

Usage examples in Web IDE:
  python tools/remote_cli.py doctor
  python tools/remote_cli.py test-client
  python tools/remote_cli.py compile
  python tools/remote_cli.py status
  python tools/remote_cli.py logs --service geyser --lines 40
  python tools/remote_cli.py exec test_block.py
"""

import sys
import os
import argparse
import json
import time
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ACTIONS_DIR = BASE_DIR / ".bridge_actions"
REQUEST_FILE = ACTIONS_DIR / "request.json"
RESPONSE_FILE = ACTIONS_DIR / "response.json"

def run_git(args, check=True, timeout=30):
    cmd = ["git"] + args
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    res = subprocess.run(cmd, cwd=BASE_DIR, check=check, text=True, capture_output=True, errors="replace", env=env, timeout=timeout)
    return res.stdout.strip()

def main():
    parser = argparse.ArgumentParser(description="Web IDE Remote Execution Client")
    parser.add_argument("action", choices=["doctor", "test-client", "compile", "status", "logs", "server-cmd", "exec"],
                        help="Action to execute on host server")
    parser.add_argument("--service", default="geyser", choices=["geyser", "inventory", "server", "viaproxy"],
                        help="Target service for 'logs' action")
    parser.add_argument("--lines", type=int, default=50, help="Number of tail lines for 'logs'")
    parser.add_argument("--cmd", help="Console command for 'server-cmd'")
    parser.add_argument("--script", help="Script name in tools/ for 'exec'")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout in seconds waiting for host response")

    args = parser.parse_args()

    ACTIONS_DIR.mkdir(parents=True, exist_ok=True)
    req_id = f"req-{int(time.time() * 1000)}"

    params = {}
    if args.action == "logs":
        params = {"service": args.service, "lines": args.lines}
    elif args.action == "server-cmd":
        params = {"cmd": args.cmd or ""}
    elif args.action == "exec":
        params = {"script": args.script or ""}

    request_payload = {
        "id": req_id,
        "action": args.action,
        "params": params,
        "client_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    print(f"[Remote CLI] Preparing action '{args.action}' (ID: {req_id})...")
    with open(REQUEST_FILE, "w", encoding="utf-8") as f:
        json.dump(request_payload, f, indent=2)

    # Commit and push request to GitHub
    print("[Remote CLI] Dispatching action request to GitHub...")
    try:
        run_git(["add", str(REQUEST_FILE)])
        run_git(["commit", "-m", f"bridge(req): {args.action} [{req_id}]"])
        run_git(["push"])
        print("[Remote CLI] Request dispatched! Waiting for host server execution...")
    except Exception as e:
        print(f"[Remote CLI Error] Failed to push request: {e}", file=sys.stderr)
        sys.exit(1)

    # Poll for response
    start_t = time.time()
    while time.time() - start_t < args.timeout:
        time.sleep(3)
        try:
            run_git(["pull", "--rebase"], check=False)
            if RESPONSE_FILE.exists():
                with open(RESPONSE_FILE, "r", encoding="utf-8") as f:
                    resp = json.load(f)
                if resp.get("id") == req_id:
                    print(f"\n================ HOST EXECUTION RESULT ({resp.get('duration_sec')}s) ================")
                    print(f"Action: {resp.get('action')}")
                    print(f"Exit Code: {resp.get('returncode')}")
                    print(f"Host Timestamp: {resp.get('timestamp')}")
                    print("------------------------ STDOUT ------------------------")
                    print(resp.get("stdout", ""))
                    if resp.get("stderr"):
                        print("------------------------ STDERR ------------------------")
                        print(resp.get("stderr", ""))
                    print("========================================================================\n")
                    sys.exit(resp.get("returncode", 0))
        except Exception:
            pass
        print(f"[Remote CLI] Waiting for host response... ({int(time.time() - start_t)}s elapsed)", end="\r")

    print(f"\n[Remote CLI Error] Timed out waiting for host response after {args.timeout}s.")
    print("Ensure the host machine is running 'python tools/bridge.py github watch'!")
    sys.exit(1)

if __name__ == "__main__":
    main()
