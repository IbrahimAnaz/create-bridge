#!/usr/bin/env python3
"""
Colab Sync Tool (tools/colab_sync.py)
Synchronizes local files directly to an active Google Colab SSH session via SCP/SSH.

Usage:
  python tools/colab_sync.py --host <tmate_host_or_ip> --port <port> [--user root] [--key <path>]
  python tools/colab_sync.py --ssh-cmd "ssh root@..."
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def main():
    parser = argparse.ArgumentParser(description="Sync local files to Colab SSH session")
    parser.add_argument("--ssh-cmd", help="Full SSH connection string (e.g. 'ssh ro-xyz@nyc1.tmate.io')")
    parser.add_argument("--host", help="SSH host or IP")
    parser.add_argument("--port", type=int, default=22, help="SSH port (default 22)")
    parser.add_argument("--user", default="root", help="SSH user (default: root)")
    parser.add_argument("--remote-dir", default="/content/create-bridge", help="Target directory in Colab")
    parser.add_argument("--action", choices=["push", "pull", "exec"], default="push", help="Action to perform")
    parser.add_argument("--cmd", help="Command to execute if action is 'exec'")

    args = parser.parse_args()

    host = args.host
    port = args.port
    user = args.user

    if args.ssh_cmd:
        # Parse 'ssh -p 1234 user@host' or 'ssh user@host'
        parts = args.ssh_cmd.strip().split()
        if "ssh" in parts[0]:
            parts = parts[1:]
        i = 0
        while i < len(parts):
            if parts[i] == "-p" and i + 1 < len(parts):
                port = int(parts[i+1])
                i += 2
            elif "@" in parts[i]:
                user, host = parts[i].split("@", 1)
                i += 1
            else:
                host = parts[i]
                i += 1

    if not host:
        print("[Error] Must provide either --host or --ssh-cmd")
        sys.exit(1)

    print(f"[Colab Sync] Target: {user}@{host}:{port} -> {args.remote_dir}")

    if args.action == "push":
        # Create tarball of modified source directories to transfer fast over SSH
        print("[Colab Sync] Packaging extension, companion mod, and tools...")
        tar_file = BASE_DIR / "colab_update.tar.gz"
        tar_cmd = [
            "tar", "-czf", str(tar_file),
            "--exclude=*.log",
            "--exclude=build",
            "--exclude=bin",
            "--exclude=.git",
            "portable_bridge", "headless_server/companion_mod", "tools"
        ]
        subprocess.run(tar_cmd, cwd=BASE_DIR, check=True)

        print(f"[Colab Sync] Uploading update bundle via SCP...")
        scp_cmd = [
            "scp", "-P", str(port),
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            str(tar_file),
            f"{user}@{host}:{args.remote_dir}/colab_update.tar.gz"
        ]
        subprocess.run(scp_cmd, check=True)

        print(f"[Colab Sync] Extracting on remote Colab instance and recompiling...")
        remote_extract = f"cd {args.remote_dir} && tar -xzf colab_update.tar.gz && rm colab_update.tar.gz && python3 tools/compile_bridge.py"
        ssh_cmd = [
            "ssh", "-p", str(port),
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            f"{user}@{host}",
            remote_extract
        ]
        subprocess.run(ssh_cmd, check=True)
        print("[Colab Sync] >>> PUSH & RECOMPILE COMPLETE! <<<")

    elif args.action == "exec":
        if not args.cmd:
            print("[Error] Must provide --cmd for exec action")
            sys.exit(1)
        ssh_cmd = [
            "ssh", "-p", str(port),
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            f"{user}@{host}",
            f"cd {args.remote_dir} && {args.cmd}"
        ]
        subprocess.run(ssh_cmd)

if __name__ == "__main__":
    main()
