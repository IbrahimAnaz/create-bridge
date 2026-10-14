#!/usr/bin/env python3
"""
Google Drive Sync & Remote Action Bridge (tools/drive_bridge.py)
Synchronizes files between a Google Drive folder and this local workspace.
Automatically hot-recompiles on edits and executes actions (doctor, compile, test-client)
dispatched by the remote agent via request.json in Google Drive!

Usage:
  # Package project bundle for Google Drive
  python tools/drive_bridge.py pack

  # Watch Google Drive synced folder (e.g. G:\\My Drive\\CreateBridge or a local synced folder)
  python tools/drive_bridge.py watch --drive-dir "G:\\My Drive\\CreateBridge"
"""

import sys
import os
import time
import json
import shutil
import zipfile
import argparse
import subprocess
from pathlib import Path

try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

def cmd_pack(args):
    """Packages a clean, lightweight zip bundle to upload into Google Drive."""
    out_zip = BASE_DIR / "create_bridge.zip"
    print(f"[Drive Bridge] Creating clean project zip: {out_zip.name}...", flush=True)
    
    targets = ["portable_bridge", "headless_server/companion_mod", "tools", ".bridge_actions"]
    count = 0
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for target in targets:
            target_path = BASE_DIR / target
            if not target_path.exists():
                continue
            for root, _, files in os.walk(target_path):
                for f in files:
                    # Exclude heavy binaries, logs, and build directories
                    if any(x in f.lower() for x in [".log", ".gz", ".class", ".jar", ".tar"]):
                        continue
                    if any(x in root for x in ["bin", "build", "logs", ".git"]):
                        continue
                    full_p = Path(root) / f
                    rel_p = full_p.relative_to(BASE_DIR)
                    z.write(full_p, rel_p)
                    count += 1
        
        # Include top-level handoffs and readme
        for doc in ["HANDOFF.md", "REMOTE_AGENT_HANDOFF.md", "CLIENT_EMULATION_BACKEND_HANDOFF.md", "GCP_SETUP.md"]:
            doc_p = BASE_DIR / doc
            if doc_p.exists():
                z.write(doc_p, doc)
                count += 1

    size_mb = round(out_zip.stat().st_size / (1024 * 1024), 2)
    print(f"[Drive Bridge] >>> Pack complete! Added {count} files ({size_mb} MB) -> {out_zip} <<<")
    print("Drop this file into Google Drive (drive.google.com) for your agent.")

def process_drive_action(drive_path: Path):
    """Checks for request.json in the Google Drive folder, executes it, and writes response.json."""
    req_file = drive_path / "request.json"
    if not req_file.exists():
        # Check inside .bridge_actions/
        req_file = drive_path / ".bridge_actions" / "request.json"
        if not req_file.exists():
            return

    try:
        req_data = json.loads(req_file.read_text(encoding="utf-8"))
    except Exception:
        return

    req_id = req_data.get("id", f"req-{int(time.time()*1000)}")
    action = req_data.get("action", "doctor")
    params = req_data.get("params", {})

    print(f"\n[Drive Bridge Action] >>> Detected request '{action}' (ID: {req_id}) from Google Drive! <<<")
    start_t = time.time()
    stdout = ""
    stderr = ""
    returncode = 0

    try:
        if action == "doctor":
            res = subprocess.run([sys.executable, str(BASE_DIR / "tools" / "bridge.py"), "doctor"], capture_output=True, text=True, cwd=BASE_DIR)
            stdout = res.stdout
            stderr = res.stderr
            returncode = res.returncode

        elif action == "compile":
            res = subprocess.run([sys.executable, str(BASE_DIR / "tools" / "compile_bridge.py")], capture_output=True, text=True, cwd=BASE_DIR)
            stdout = res.stdout
            stderr = res.stderr
            returncode = res.returncode

        elif action == "test-client":
            res = subprocess.run(["node", str(BASE_DIR / "tools" / "dummy_bedrock" / "dummy_client.js")], capture_output=True, text=True, cwd=BASE_DIR, timeout=30)
            stdout = res.stdout
            stderr = res.stderr
            returncode = res.returncode

        elif action == "status":
            res = subprocess.run([sys.executable, str(BASE_DIR / "tools" / "bridge.py"), "status"], capture_output=True, text=True, cwd=BASE_DIR)
            stdout = res.stdout
            returncode = res.returncode

        elif action == "logs":
            service = params.get("service", "geyser")
            lines = params.get("lines", 50)
            res = subprocess.run([sys.executable, str(BASE_DIR / "tools" / "bridge.py"), "logs", service, "-n", str(lines)], capture_output=True, text=True, cwd=BASE_DIR)
            stdout = res.stdout
            returncode = res.returncode
        else:
            stderr = f"Unknown action: {action}"
            returncode = 1
    except Exception as e:
        stderr = str(e)
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

    # Write response.json and latest_run.log into Drive folder
    resp_file = drive_path / "response.json"
    log_file = drive_path / "latest_run.log"
    resp_file.write_text(json.dumps(response_payload, indent=2), encoding="utf-8")
    log_file.write_text(f"=== ACTION: {action} (Code {returncode}, {duration}s) ===\n{stdout}\n{stderr}", encoding="utf-8")

    # Also sync into .bridge_actions/ inside drive
    drive_actions = drive_path / ".bridge_actions"
    if drive_actions.exists():
        (drive_actions / "response.json").write_text(json.dumps(response_payload, indent=2), encoding="utf-8")

    # Remove or archive request.json so it doesn't re-trigger
    try:
        req_file.unlink()
    except Exception:
        pass

    print(f"[Drive Bridge Action] Finished '{action}' in {duration}s. Wrote response.json to Google Drive!")

def sync_drive_to_local(drive_path: Path):
    """Copies updated source files from Google Drive into our local workspace and recompiles."""
    recompile_needed = False
    
    # Check portable_bridge source files
    drive_ext = drive_path / "portable_bridge" / "extension" / "src"
    local_ext = BASE_DIR / "portable_bridge" / "extension" / "src"
    if drive_ext.exists():
        for root, _, files in os.walk(drive_ext):
            for f in files:
                if f.endswith(".java") or f.endswith(".json"):
                    src_f = Path(root) / f
                    rel_p = src_f.relative_to(drive_ext)
                    dst_f = local_ext / rel_p
                    if not dst_f.exists() or src_f.stat().st_mtime > dst_f.stat().st_mtime:
                        dst_f.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_f, dst_f)
                        print(f"[Drive Sync] Updated from Drive: {rel_p}")
                        recompile_needed = True

    if recompile_needed:
        print("[Drive Sync] Extension source changes detected. Auto-recompiling CreateBridge.jar...")
        subprocess.run([sys.executable, str(BASE_DIR / "tools" / "compile_bridge.py")], cwd=BASE_DIR)

def cmd_watch(args):
    """Monitors a Google Drive folder continuously."""
    drive_dir = Path(args.drive_dir).resolve()
    if not drive_dir.exists():
        print(f"[Error] Google Drive directory not found: {drive_dir}")
        print("Please provide the path to your synced Google Drive folder (e.g. 'G:\\My Drive\\CreateBridge')")
        sys.exit(1)

    interval = args.interval
    print(f"[Google Drive Bridge] Watching Google Drive folder: {drive_dir}")
    print(f"  Polling interval: {interval}s")
    print(f"  Mailbox: {drive_dir / 'request.json'} -> {drive_dir / 'response.json'}")
    print("Press Ctrl+C to stop.\n")

    while True:
        try:
            # 1. Process any incoming action requests from the remote agent
            process_drive_action(drive_dir)
            # 2. Check for updated source files in Drive
            sync_drive_to_local(drive_dir)
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[Google Drive Bridge] Stopped.")
            break
        except Exception as e:
            time.sleep(interval)

def main():
    parser = argparse.ArgumentParser(description="Google Drive Sync & Remote Action Bridge")
    sub = parser.add_subparsers(dest="command")

    pack_p = sub.add_parser("pack", help="Create clean project zip for Google Drive")

    watch_p = sub.add_parser("watch", help="Watch Google Drive folder and auto-execute requests")
    watch_p.add_argument("--drive-dir", required=True, help="Path to your local synced Google Drive folder")
    watch_p.add_argument("--interval", type=int, default=3, help="Polling interval in seconds (default: 3)")

    args = parser.parse_args()
    if args.command == "pack":
        cmd_pack(args)
    elif args.command == "watch":
        cmd_watch(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
