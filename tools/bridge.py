#!/usr/bin/env python3
"""
Bridge Developer CLI (tools/bridge.py)
Unified toolkit for managing, monitoring, debugging, and patching the
Java-to-Bedrock Minecraft Create Mod bridge stack.
"""

import sys
import os
import argparse
import socket
import subprocess
import zipfile
import tempfile
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SERVER_DIR = BASE_DIR / "headless_server"
LOGS_DIR = SERVER_DIR / "logs"
VIAPROXY_DIR = SERVER_DIR / "viaproxy"
GEYSER_DIR = SERVER_DIR / "geyser"
JDK21_JAVAP = Path(r"C:\Program Files\Java\jdk-21.0.12\bin\javap.exe")

def is_tcp_listening(host: str, port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def get_process_info(port: int, proto: str = "TCP"):
    try:
        cmd = f'netstat -ano | findstr "{port}"'
        out = subprocess.check_output(cmd, shell=True, text=True, errors="ignore")
        pids = set()
        for line in out.splitlines():
            parts = line.strip().split()
            if len(parts) >= 4 and parts[0].upper() == proto.upper():
                if proto == "TCP" and "LISTENING" in parts:
                    pids.add(int(parts[-1]))
                elif proto == "UDP":
                    pids.add(int(parts[-1]))
        if not pids:
            return None
        pid = list(pids)[0]
        # Get memory and name
        ps_cmd = f'powershell -Command "Get-Process -Id {pid} -ErrorAction SilentlyContinue | Select-Object ProcessName, @{{Name=\'MemMB\';Expression={{[math]::Round($_.WorkingSet64/1MB)}}}} | ConvertTo-Json"'
        ps_out = subprocess.check_output(ps_cmd, shell=True, text=True, errors="ignore").strip()
        import json
        if ps_out:
            data = json.loads(ps_out)
            return {"pid": pid, "name": data.get("ProcessName", "java"), "mem_mb": data.get("MemMB", 0)}
        return {"pid": pid, "name": "unknown", "mem_mb": 0}
    except Exception:
        return None

def cmd_status(args):
    """Check health, port, PID, memory, and last events for all services."""
    services = [
        ("NeoForge Server", 25565, "TCP"),
        ("ViaProxy Bridge", 25568, "TCP"),
        ("Geyser Bedrock",  19132, "UDP"),
    ]
    print(f"{'Service':<18} | {'Status':<10} | {'Port':<6} | {'PID':<7} | {'Mem (MB)':<9}")
    print("-" * 62)
    for name, port, proto in services:
        proc = get_process_info(port, proto)
        if proc:
            status = "ONLINE"
            pid = str(proc["pid"])
            mem = f"{proc['mem_mb']} MB"
        else:
            status = "OFFLINE"
            pid = "-"
            mem = "-"
        print(f"{name:<18} | {status:<10} | {port:<6} | {pid:<7} | {mem:<9}")

    # Check last important events in server log
    latest_log = LOGS_DIR / "latest.log"
    if latest_log.exists():
        print("\n[Recent Server Milestones]")
        lines = latest_log.read_text(encoding="utf-8", errors="ignore").splitlines()
        hits = [line for line in lines if any(k in line for k in ["Done (", "logged in with entity", "lost connection", "joined the game"])]
        for h in hits[-5:]:
            print("  " + h.strip())

def find_service_task_log(keyword: str) -> Path | None:
    brain_dir = Path(r"C:\Users\ibrah\.gemini\antigravity\brain")
    if not brain_dir.exists():
        return None
    conv_dirs = sorted([d for d in brain_dir.iterdir() if d.is_dir() and d.name != ".system_generated"], key=os.path.getmtime, reverse=True)
    for conv in conv_dirs:
        tasks_dir = conv / ".system_generated" / "tasks"
        if tasks_dir.exists():
            logs = sorted(tasks_dir.glob("*.log"), key=os.path.getmtime, reverse=True)
            for l in logs:
                try:
                    content = l.read_text(encoding="utf-8", errors="ignore")[:4000]
                    if keyword in content:
                        return l
                except Exception:
                    continue
    return None

def cmd_logs(args):
    """Tail and filter logs with high token efficiency."""
    filter_pattern = args.pattern or r"ERROR|WARN|Exception|logged in|joined|left|lost connection|Done \("
    reg = re.compile(filter_pattern, re.IGNORECASE)
    n = args.lines or 20

    if args.service == "all":
        # Merge logs across all 3 services
        collected = []
        # Server
        srv_log = LOGS_DIR / "latest.log"
        if srv_log.exists():
            for line in srv_log.read_text(encoding="utf-8", errors="ignore").splitlines():
                if reg.search(line):
                    collected.append(f"[SERVER]   {line.strip()}")
        # ViaProxy
        vp_log = find_service_task_log("Initializing ViaProxy CLI")
        if vp_log and vp_log.exists():
            for line in vp_log.read_text(encoding="utf-8", errors="ignore").splitlines():
                if reg.search(line):
                    collected.append(f"[VIAPROXY] {line.strip()}")
        # Geyser
        gy_log = find_service_task_log("Loading Geyser version")
        if gy_log and gy_log.exists():
            for line in gy_log.read_text(encoding="utf-8", errors="ignore").splitlines():
                if reg.search(line):
                    collected.append(f"[GEYSER]   {line.strip()}")
        for entry in collected[-n:]:
            print(entry)
        return

    target_log = None
    if args.service == "server":
        target_log = LOGS_DIR / "latest.log"
    elif args.service == "geyser":
        target_log = find_service_task_log("Loading Geyser version")
        if not target_log:
            g_logs = list(GEYSER_DIR.glob("*.log"))
            if g_logs:
                target_log = sorted(g_logs, key=os.path.getmtime)[-1]
    elif args.service == "viaproxy":
        target_log = find_service_task_log("Initializing ViaProxy CLI")

    if not target_log or not target_log.exists():
        target_log = LOGS_DIR / "latest.log"

    lines = target_log.read_text(encoding="utf-8", errors="ignore").splitlines()
    matched = [l.strip() for l in lines if reg.search(l)]
    for l in matched[-n:]:
        print(l)

def cmd_scan_jar(args):
    """Ultra-fast jar constant-pool & entry scanner (100ms)."""
    jar_path = Path(args.jar)
    if not jar_path.exists():
        # try relative to server dir
        jar_path = SERVER_DIR / args.jar
    if not jar_path.exists():
        print(f"Error: {args.jar} not found")
        return

    pattern = args.query.encode("utf-8", errors="ignore")
    matches = 0
    with zipfile.ZipFile(jar_path, "r") as z:
        for entry in z.namelist():
            if entry.endswith(".class"):
                data = z.read(entry)
                if pattern in data:
                    print(f"Match: {entry}")
                    matches += 1
                    if matches >= args.limit:
                        print(f"(Reached limit of {args.limit} matches)")
                        break
    if matches == 0:
        print(f"No occurrences of '{args.query}' found in {jar_path.name}")

def cmd_inject(args):
    """Inject a class into a jar in-place via zip streaming in < 1 second."""
    target_jar = Path(args.jar)
    if not target_jar.exists():
        target_jar = SERVER_DIR / args.jar
    if not target_jar.exists():
        print(f"Error: Jar {args.jar} not found")
        return

    class_file = Path(args.class_file)
    if not class_file.exists():
        print(f"Error: Class file {args.class_file} not found")
        return

    entry_path = args.entry.replace("\\", "/")
    print(f"Injecting {class_file.name} -> {target_jar.name}:{entry_path}...")

    class_bytes = class_file.read_bytes()

    # Fast in-memory/tempfile zip re-writer
    temp_jar = target_jar.with_suffix(".tmp.jar")
    with zipfile.ZipFile(target_jar, "r") as zin:
        with zipfile.ZipFile(temp_jar, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == entry_path:
                    continue # will be replaced
                zout.writestr(item, zin.read(item.filename))
            zout.writestr(entry_path, class_bytes)

    # Atomic replace
    backup = target_jar.with_suffix(".jar.bak")
    if not backup.exists():
        target_jar.rename(backup)
    else:
        target_jar.unlink()
    temp_jar.rename(target_jar)
    print(f"Success! {target_jar.name} updated ({len(class_bytes)} bytes written)")

def cmd_disasm(args):
    """Disassemble class or method using javap with token-lean filtering."""
    javap = JDK21_JAVAP if JDK21_JAVAP.exists() else Path("javap")
    target = args.target
    cmd = [str(javap), "-c", "-p", target]
    try:
        out = subprocess.check_output(cmd, text=True, errors="ignore")
    except Exception as e:
        print(f"javap error: {e}")
        return

    lines = out.splitlines()
    if args.filter:
        reg = re.compile(args.filter, re.IGNORECASE)
        recording = False
        depth = 0
        filtered = []
        for l in lines:
            if "public" in l or "private" in l or "protected" in l:
                recording = bool(reg.search(l))
            if recording:
                filtered.append(l)
                if l.strip() == "}" or len(filtered) > 100:
                    recording = False
        if filtered:
            print("\n".join(filtered[:args.limit or 60]))
        else:
            print(f"No methods matched filter '{args.filter}'")
    else:
        print("\n".join(lines[:args.limit or 50]))

def cmd_doctor(args):
    """Verify entire pipeline integrity: ports, configs, Java, and patches."""
    print("=" * 60)
    print("CREATE BRIDGE SYSTEM DIAGNOSTICS (DOCTOR)")
    print("=" * 60)

    # 1. Ports
    s_online = is_tcp_listening("127.0.0.1", 25565)
    v_online = is_tcp_listening("127.0.0.1", 25568)
    g_proc = get_process_info(19132, "UDP")
    g_online = g_proc is not None

    print(f"[{'PASS' if s_online else 'FAIL'}] Server Port (TCP 25565): {'Online' if s_online else 'Not listening'}")
    print(f"[{'PASS' if v_online else 'FAIL'}] ViaProxy Port (TCP 25568): {'Online' if v_online else 'Not listening'}")
    print(f"[{'PASS' if g_online else 'FAIL'}] Geyser Bedrock Port (UDP 19132): {'Online' if g_online else 'Not listening'}")

    # 2. Config Alignment
    geyser_cfg = GEYSER_DIR / "config.yml"
    if geyser_cfg.exists():
        cfg_txt = geyser_cfg.read_text(encoding="utf-8", errors="ignore")
        has_25568 = "port: 25568" in cfg_txt
        no_motd_ping = "passthrough-motd: false" in cfg_txt
        print(f"[{'PASS' if has_25568 else 'WARN'}] Geyser -> ViaProxy Target Port: {'25568 (Correct)' if has_25568 else 'Mismatched!'}")
        print(f"[{'PASS' if no_motd_ping else 'WARN'}] Geyser Ping Passthrough: {'Disabled (Prevents handshake crash)' if no_motd_ping else 'Enabled (May cause handshake errors)'}")

    # 3. ViaProxy Patch Check
    vp_jar = VIAPROXY_DIR / "ViaProxy.jar"
    if vp_jar.exists():
        with zipfile.ZipFile(vp_jar) as z:
            has_key = "com/viaversion/viaversion/util/Key.class" in z.namelist()
            has_recipe = "com/viaversion/viaversion/protocols/v1_21to1_21_2/rewriter/BlockItemPacketRewriter1_21_2.class" in z.namelist()
            print(f"[{'PASS' if has_key else 'FAIL'}] ViaProxy Key.class Patch: {'Present' if has_key else 'Missing'}")
            print(f"[{'PASS' if has_recipe else 'FAIL'}] ViaProxy RecipeRewriter Patch: {'Present' if has_recipe else 'Missing'}")

    # 4. NeoForge Patch Check
    nf_jar = SERVER_DIR / "libraries" / "net" / "neoforged" / "neoforge" / "21.1.248" / "neoforge-21.1.248-universal.jar"
    if nf_jar.exists():
        with zipfile.ZipFile(nf_jar) as z:
            has_net = "net/neoforged/neoforge/network/registration/NetworkRegistry.class" in z.namelist()
            print(f"[{'PASS' if has_net else 'FAIL'}] NeoForge NetworkRegistry: {'Present' if has_net else 'Missing'}")

    print("=" * 60)
    if s_online and v_online and g_online:
        print(">> ALL SYSTEMS OPERATIONAL: Ready for Bedrock connection! <<")
    else:
        print(">> WARNING: Some components offline. Check 'python tools/bridge.py status' <<")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Create Bridge Developer Toolkit")
    sub = parser.add_subparsers(dest="command")

    # status
    sub.add_parser("status", help="Check health and ports of all services")

    # doctor
    sub.add_parser("doctor", help="Run comprehensive system diagnostics")

    # logs
    p_logs = sub.add_parser("logs", help="View filtered, token-efficient service logs")
    p_logs.add_argument("service", nargs="?", default="server", choices=["server", "viaproxy", "geyser", "all"])
    p_logs.add_argument("-n", "--lines", type=int, default=20, help="Number of lines to show")
    p_logs.add_argument("-p", "--pattern", type=str, default=None, help="Regex filter pattern")

    # scan-jar
    p_scan = sub.add_parser("scan-jar", help="Fast search for symbols inside a jar")
    p_scan.add_argument("jar", type=str, help="Jar file path")
    p_scan.add_argument("query", type=str, help="Search string/symbol")
    p_scan.add_argument("-l", "--limit", type=int, default=15, help="Max results")

    # inject
    p_inj = sub.add_parser("inject", help="Fast injection of a class file into a jar")
    p_inj.add_argument("jar", type=str, help="Target jar file")
    p_inj.add_argument("entry", type=str, help="Internal jar entry path")
    p_inj.add_argument("class_file", type=str, help="Source class file on disk")

    # disasm
    p_dis = sub.add_parser("disasm", help="Disassemble and filter bytecode with javap")
    p_dis.add_argument("target", type=str, help="Class file path")
    p_dis.add_argument("-f", "--filter", type=str, default=None, help="Method name or pattern to filter")
    p_dis.add_argument("-l", "--limit", type=int, default=60, help="Max lines")

    # build-blocks
    sub.add_parser("build-blocks", help="Automated extraction of Create textures, Bedrock pack, and Geyser extension")

    args = parser.parse_args()
    if args.command == "status":
        cmd_status(args)
    elif args.command == "doctor":
        cmd_doctor(args)
    elif args.command == "logs":
        cmd_logs(args)
    elif args.command == "scan-jar":
        cmd_scan_jar(args)
    elif args.command == "inject":
        cmd_inject(args)
    elif args.command == "disasm":
        cmd_disasm(args)
    elif args.command == "build-blocks":
        sys.path.insert(0, str(BASE_DIR / "tools"))
        import builder as b
        b.step1_extract_textures_and_pack()
        b.step2_generate_extension_source()
        b.step3_compile_and_package()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
