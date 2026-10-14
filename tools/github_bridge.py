#!/usr/bin/env python3
"""
GitHub Bridge Tool (tools/github_bridge.py)
Bidirectional GitHub sync bridge allowing an external web IDE / cloud agent
to seamlessly read and write files to the local Create Bridge project directory.

Supports:
- Git remote synchronization (push, pull, bidirectional sync)
- GitHub REST API direct read/write (using GITHUB_TOKEN or PAT)
- Continuous watch daemon: auto-pulls changes from the web IDE and triggers hot reloads
"""

import sys
import os
import argparse
import subprocess
import time
import json
import urllib.request
import urllib.error
import base64
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "tools" / "github_bridge_config.json"

def get_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "repo": "",
        "branch": "master",
        "remote_name": "origin",
        "poll_interval_sec": 5,
        "auto_compile": True
    }

def save_config(cfg):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

def run_git(args, check=True, capture=True, timeout=30):
    cmd = ["git"] + args
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        res = subprocess.run(
            cmd,
            cwd=BASE_DIR,
            check=check,
            text=True,
            capture_output=capture,
            errors="replace",
            env=env,
            timeout=timeout
        )
        return res.stdout.strip() if capture else ""
    except subprocess.TimeoutExpired:
        print(f"[Git Error] Command timed out after {timeout}s: {' '.join(cmd)}", file=sys.stderr)
        raise
    except subprocess.CalledProcessError as e:
        if capture:
            print(f"[Git Error] {e.stderr.strip()}", file=sys.stderr)
        raise

def get_current_branch():
    try:
        return run_git(["branch", "--show-current"])
    except Exception:
        return "master"

def get_token():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    cfg = get_config()
    return cfg.get("token", "")

# ---------------------------------------------------------------------------
# CLI Commands
# ---------------------------------------------------------------------------

def cmd_setup(args):
    """Configures the GitHub repository remote and branch."""
    cfg = get_config()
    repo = args.repo.strip()
    branch = args.branch or cfg.get("branch", "master")
    token = args.token or cfg.get("token", "")

    # Format remote URL
    if repo.startswith("http://") or repo.startswith("https://") or repo.startswith("git@"):
        remote_url = repo
        # Extract owner/repo
        parts = repo.rstrip("/").split("/")
        cfg["repo"] = f"{parts[-2]}/{parts[-1].replace('.git', '')}"
    else:
        # Assumed format: owner/repo
        cfg["repo"] = repo
        if token:
            remote_url = f"https://x-access-token:{token}@github.com/{repo}.git"
        else:
            remote_url = f"https://github.com/{repo}.git"

    cfg["branch"] = branch
    if token:
        cfg["token"] = token
    save_config(cfg)

    # Configure git remote
    remotes = run_git(["remote"]).splitlines()
    remote_name = cfg.get("remote_name", "origin")
    if remote_name in remotes:
        run_git(["remote", "set-url", remote_name, remote_url])
        print(f"[GitHub Bridge] Updated remote '{remote_name}' -> {remote_url}")
    else:
        run_git(["remote", "add", remote_name, remote_url])
        print(f"[GitHub Bridge] Added remote '{remote_name}' -> {remote_url}")

    print(f"[GitHub Bridge] Setup complete for repository '{cfg['repo']}' (branch: '{branch}')")

def cmd_push(args):
    """Stages local changes, commits, and pushes to GitHub so the web IDE can read them."""
    cfg = get_config()
    branch = args.branch or cfg.get("branch", get_current_branch())
    remote = cfg.get("remote_name", "origin")
    msg = args.message or f"bridge(sync): local updates from agent at {time.strftime('%Y-%m-%d %H:%M:%S')}"

    print(f"[GitHub Bridge] Staging modified files...")
    # Stage tracked modifications + new tools/extension files
    run_git(["add", "portable_bridge/", "headless_server/companion_mod/", "tools/", "create_cogwheel_rp/"])
    if args.all:
        run_git(["add", "-u"])

    status = run_git(["status", "--porcelain"])
    if not status:
        print("[GitHub Bridge] No staged changes to commit. Pushing existing commits...")
    else:
        print(f"[GitHub Bridge] Committing changes: '{msg}'")
        run_git(["commit", "-m", msg])

    print(f"[GitHub Bridge] Pushing to {remote}/{branch}...")
    try:
        run_git(["push", "-u", remote, branch], capture=False)
        print(f"[GitHub Bridge] >>> PUSH SUCCESS! Web IDE can now read the latest files on GitHub. <<<")
    except Exception as e:
        print(f"[GitHub Bridge] Push failed: {e}")
        sys.exit(1)

def cmd_pull(args):
    """Pulls changes written by the web IDE from GitHub into our local directory."""
    cfg = get_config()
    branch = args.branch or cfg.get("branch", get_current_branch())
    remote = cfg.get("remote_name", "origin")

    print(f"[GitHub Bridge] Fetching updates from {remote}/{branch}...")
    try:
        out = run_git(["pull", "--rebase", remote, branch])
        print(f"[GitHub Bridge] {out}")
        print(f"[GitHub Bridge] >>> PULL SUCCESS! Local directory updated from web IDE. <<<")
        if cfg.get("auto_compile", True) and ("portable_bridge" in out or "extension" in out):
            print("[GitHub Bridge] Detected extension modifications. Triggering recompile...")
            compile_script = BASE_DIR / "tools" / "compile_bridge.py"
            if compile_script.exists():
                subprocess.run([sys.executable, str(compile_script)], check=False)
    except Exception as e:
        print(f"[GitHub Bridge] Pull failed: {e}")
        sys.exit(1)

def cmd_sync(args):
    """Bidirectional sync: pulls web IDE updates, then pushes local changes."""
    print("[GitHub Bridge] === STEP 1: PULL FROM WEB IDE ===")
    try:
        cmd_pull(args)
    except SystemExit:
        print("[GitHub Bridge] Pull encountered an error. Attempting push...")
    print("\n[GitHub Bridge] === STEP 2: PUSH TO WEB IDE ===")
    cmd_push(args)

ACTIONS_DIR = BASE_DIR / ".bridge_actions"
REQUEST_FILE = ACTIONS_DIR / "request.json"
RESPONSE_FILE = ACTIONS_DIR / "response.json"

def process_remote_actions(remote, branch):
    """Checks for pending action requests from the Web IDE and executes them."""
    if not REQUEST_FILE.exists():
        return False

    try:
        with open(REQUEST_FILE, "r", encoding="utf-8") as f:
            req = json.load(f)
    except Exception as e:
        return False

    req_id = req.get("id")
    if not req_id:
        return False

    # Check if already processed
    if RESPONSE_FILE.exists():
        try:
            with open(RESPONSE_FILE, "r", encoding="utf-8") as f:
                last_resp = json.load(f)
                if last_resp.get("id") == req_id:
                    return False  # Already executed
        except Exception:
            pass

    action = req.get("action", "")
    params = req.get("params", {})
    print(f"\n[Remote Action Dispatcher] Executing action '{action}' (ID: {req_id})...")
    start_t = time.time()

    stdout = ""
    stderr = ""
    returncode = 0

    try:
        if action == "doctor":
            res = subprocess.run([sys.executable, str(BASE_DIR / "tools" / "bridge.py"), "doctor"],
                                 cwd=BASE_DIR, capture_output=True, text=True, errors="replace")
            stdout, stderr, returncode = res.stdout, res.stderr, res.returncode

        elif action == "status":
            res = subprocess.run([sys.executable, str(BASE_DIR / "tools" / "bridge.py"), "status"],
                                 cwd=BASE_DIR, capture_output=True, text=True, errors="replace")
            stdout, stderr, returncode = res.stdout, res.stderr, res.returncode

        elif action == "compile":
            res = subprocess.run([sys.executable, str(BASE_DIR / "tools" / "compile_bridge.py")],
                                 cwd=BASE_DIR, capture_output=True, text=True, errors="replace")
            stdout, stderr, returncode = res.stdout, res.stderr, res.returncode

        elif action == "test-client":
            res = subprocess.run([sys.executable, str(BASE_DIR / "tools" / "bridge.py"), "test-client"],
                                 cwd=BASE_DIR, capture_output=True, text=True, errors="replace")
            stdout, stderr, returncode = res.stdout, res.stderr, res.returncode

        elif action == "logs":
            service = params.get("service", "geyser")
            lines_count = int(params.get("lines", 50))
            log_map = {
                "geyser": BASE_DIR / "headless_server" / "geyser" / "logs" / "latest.log",
                "inventory": BASE_DIR / "headless_server" / "geyser" / "logs" / "inventory_debug.log",
                "server": BASE_DIR / "headless_server" / "logs" / "latest.log",
                "viaproxy": BASE_DIR / "headless_server" / "viaproxy" / "logs" / "latest.log"
            }
            target_log = log_map.get(service, log_map["geyser"])
            if target_log.exists():
                with open(target_log, "r", encoding="utf-8", errors="replace") as lf:
                    lines = lf.readlines()
                    stdout = "".join(lines[-lines_count:])
            else:
                stderr = f"Log file not found: {target_log}"
                returncode = 1

        elif action == "server-cmd":
            cmd_str = params.get("cmd", "")
            if cmd_str:
                # Append command to NeoForge or run via task/script
                stdout = f"[Server Command Queued] {cmd_str}\n(Execute via NeoForge stdin)"
            else:
                stderr = "No 'cmd' string provided in params"
                returncode = 1

        elif action == "exec":
            script = params.get("script", "")
            script_path = BASE_DIR / "tools" / script
            if script_path.exists():
                res = subprocess.run([sys.executable, str(script_path)],
                                     cwd=BASE_DIR, capture_output=True, text=True, errors="replace")
                stdout, stderr, returncode = res.stdout, res.stderr, res.returncode
            else:
                stderr = f"Script not found: {script_path}"
                returncode = 1
        else:
            stderr = f"Unknown action: {action}"
            returncode = 1

    except Exception as e:
        stderr = f"Exception running action {action}: {e}"
        returncode = -1

    duration = round(time.time() - start_t, 2)
    response_payload = {
        "id": req_id,
        "action": action,
        "returncode": returncode,
        "duration_sec": duration,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "stdout": stdout,
        "stderr": stderr
    }

    ACTIONS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESPONSE_FILE, "w", encoding="utf-8") as f:
        json.dump(response_payload, f, indent=2)

    # Write human readable log
    with open(ACTIONS_DIR / "latest_run.log", "w", encoding="utf-8") as f:
        f.write(f"=== ACTION: {action} (ID: {req_id}, Code: {returncode}, {duration}s) ===\n")
        f.write(stdout)
        if stderr:
            f.write("\n--- STDERR ---\n" + stderr)

    print(f"[Remote Action Dispatcher] Finished '{action}' (code {returncode}) in {duration}s. Pushing response...")

    # Commit and push response back to GitHub
    try:
        run_git(["add", "-f", str(RESPONSE_FILE), str(ACTIONS_DIR / "latest_run.log")])
        run_git(["commit", "-m", f"bridge(action): result for {action} [{req_id}]"])
        run_git(["push", remote, branch], capture=False)
        print(f"[Remote Action Dispatcher] >>> Pushed action response back to GitHub! <<<")
    except Exception as pe:
        print(f"[Remote Action Dispatcher] Warning: Failed to push response: {pe}")

    return True

def cmd_watch(args):
    """Continuously monitors GitHub, auto-pulls updates, and executes Web IDE remote actions."""
    cfg = get_config()
    interval = args.interval or cfg.get("poll_interval_sec", 5)
    branch = args.branch or cfg.get("branch", get_current_branch())
    remote = cfg.get("remote_name", "origin")

    print(f"[GitHub Bridge Daemon] Starting watch & action dispatcher daemon...")
    print(f"  Target: {remote}/{branch}")
    print(f"  Poll interval: {interval}s")
    print(f"  Auto-compile: {cfg.get('auto_compile', True)}")
    print(f"  Remote Action Mailbox: .bridge_actions/request.json -> response.json")
    print("Press Ctrl+C to stop.\n")

    last_remote_sha = None

    while True:
        try:
            # Check remote head commit sha
            run_git(["fetch", remote, branch], check=False)
            remote_sha = run_git(["rev-parse", f"{remote}/{branch}"])
            local_sha = run_git(["rev-parse", branch])

            if remote_sha != local_sha and remote_sha != last_remote_sha:
                print(f"[{time.strftime('%H:%M:%S')}] Detected new commit from Web IDE: {remote_sha[:7]}")
                out = run_git(["pull", "--rebase", remote, branch])
                print(f"[{time.strftime('%H:%M:%S')}] {out}")
                last_remote_sha = remote_sha

                # Check if there is an action request in this commit
                process_remote_actions(remote, branch)

                if cfg.get("auto_compile", True) and ("portable_bridge" in out or "extension" in out):
                    print(f"[{time.strftime('%H:%M:%S')}] Auto-compiling CreateBridge extension...")
                    compile_script = BASE_DIR / "tools" / "compile_bridge.py"
                    if compile_script.exists():
                        subprocess.run([sys.executable, str(compile_script)], check=False)
            else:
                # Check if there is an unhandled local request file
                process_remote_actions(remote, branch)

            time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[GitHub Bridge Daemon] Stopped.")
            break
        except Exception as e:
            time.sleep(interval)

# ---------------------------------------------------------------------------
# Direct GitHub REST API Helpers (Works without full Git CLI credentials)
# ---------------------------------------------------------------------------

def api_request(endpoint, token=None, method="GET", data=None):
    url = f"https://api.github.com/{endpoint.lstrip('/')}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "CreateBridge-SyncTool"
    }
    tok = token or get_token()
    if tok:
        headers["Authorization"] = f"Bearer {tok}"

    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def cmd_api_read(args):
    """Reads a file directly from GitHub repository using the GitHub API."""
    cfg = get_config()
    repo = args.repo or cfg.get("repo")
    if not repo:
        print("[Error] No repository specified. Run 'setup' or provide --repo <owner/repo>")
        sys.exit(1)

    file_path = args.path.replace("\\", "/").lstrip("/")
    endpoint = f"repos/{repo}/contents/{file_path}?ref={args.branch or cfg.get('branch', 'master')}"
    try:
        data = api_request(endpoint)
        if "content" in data:
            content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            if args.output:
                out_path = Path(args.output)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"[GitHub Bridge API] Saved {file_path} -> {out_path}")
            else:
                print(content)
    except urllib.error.HTTPError as e:
        print(f"[GitHub Bridge API Error] HTTP {e.code}: {e.read().decode('utf-8')}")
        sys.exit(1)

def cmd_api_write(args):
    """Writes / commits a file directly to GitHub repository using GitHub API."""
    cfg = get_config()
    repo = args.repo or cfg.get("repo")
    token = get_token()
    if not repo or not token:
        print("[Error] Writing via API requires both repository and GITHUB_TOKEN. Run 'setup'.")
        sys.exit(1)

    file_path = args.path.replace("\\", "/").lstrip("/")
    local_file = Path(args.source or (BASE_DIR / file_path))
    if not local_file.exists():
        print(f"[Error] Local file not found: {local_file}")
        sys.exit(1)

    with open(local_file, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("utf-8")

    # Check if file exists to get SHA
    branch = args.branch or cfg.get("branch", "master")
    endpoint = f"repos/{repo}/contents/{file_path}?ref={branch}"
    sha = None
    try:
        existing = api_request(endpoint, token)
        sha = existing.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise

    payload = {
        "message": args.message or f"bridge(api): update {file_path}",
        "content": content_b64,
        "branch": branch
    }
    if sha:
        payload["sha"] = sha

    res = api_request(f"repos/{repo}/contents/{file_path}", token=token, method="PUT", data=payload)
    print(f"[GitHub Bridge API] Committed {file_path} to {repo}:{branch} (commit {res.get('commit', {}).get('sha', '')[:7]})")

# ---------------------------------------------------------------------------
# Main Router
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="GitHub Bridge Tool: Connect Web IDEs to Local Directory")
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    # setup
    p_setup = subparsers.add_parser("setup", help="Configure GitHub repository remote, branch, and token")
    p_setup.add_argument("repo", help="Repository format 'owner/repo' or https URL")
    p_setup.add_argument("--branch", default="master", help="Target branch (default: master)")
    p_setup.add_argument("--token", help="Personal Access Token (optional, or set GITHUB_TOKEN)")

    # push
    p_push = subparsers.add_parser("push", help="Push local files to GitHub so Web IDE can read them")
    p_push.add_argument("-m", "--message", help="Commit message")
    p_push.add_argument("--branch", help="Target branch")
    p_push.add_argument("--all", action="store_true", help="Stage all modified tracked files")

    # pull
    p_pull = subparsers.add_parser("pull", help="Pull changes written by Web IDE into local directory")
    p_pull.add_argument("--branch", help="Target branch")

    # sync
    p_sync = subparsers.add_parser("sync", help="Bidirectional sync (pull web IDE changes, then push local changes)")
    p_sync.add_argument("-m", "--message", help="Commit message for push")
    p_sync.add_argument("--branch", help="Target branch")
    p_sync.add_argument("--all", action="store_true", help="Stage all tracked files")

    # watch
    p_watch = subparsers.add_parser("watch", help="Continuously poll GitHub and auto-apply Web IDE changes")
    p_watch.add_argument("--interval", type=int, default=5, help="Poll interval in seconds (default: 5)")
    p_watch.add_argument("--branch", help="Target branch")

    # api-read
    p_aread = subparsers.add_parser("api-read", help="Read file from GitHub via REST API")
    p_aread.add_argument("path", help="Relative file path in repo")
    p_aread.add_argument("--repo", help="owner/repo")
    p_aread.add_argument("--branch", help="branch")
    p_aread.add_argument("-o", "--output", help="Save content to local path")

    # api-write
    p_awrite = subparsers.add_parser("api-write", help="Write/commit file to GitHub via REST API")
    p_awrite.add_argument("path", help="Relative file path in repo")
    p_awrite.add_argument("--source", help="Source local file (defaults to matching path)")
    p_awrite.add_argument("--repo", help="owner/repo")
    p_awrite.add_argument("--branch", help="branch")
    p_awrite.add_argument("-m", "--message", help="Commit message")

    args = parser.parse_args()

    dispatch = {
        "setup": cmd_setup,
        "push": cmd_push,
        "pull": cmd_pull,
        "sync": cmd_sync,
        "watch": cmd_watch,
        "api-read": cmd_api_read,
        "api-write": cmd_api_write
    }

    dispatch[args.cmd](args)

if __name__ == "__main__":
    main()
