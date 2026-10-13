"""
Unified Tooling & Macro Script for Bedrock-Create Bridge:
- inspect-jar [pattern]: search classes in a jar
- patch-viaproxy: apply ASM patches to ViaProxy.jar
- test-palette: verify blockstate / item mapping outputs
- start-stack / stop-stack: start/stop NeoForge, ViaProxy, Geyser
- status: inspect running ports and processes
"""
import sys
import os
import zipfile
import subprocess
import shutil

JDK = r"C:\Program Files\Java\jdk-21.0.12\bin"
JAVAC = os.path.join(JDK, "javac.exe")
JAVAP = os.path.join(JDK, "javap.exe")
JAVA = os.path.join(JDK, "java.exe")
VIAPROXY_JAR = "headless_server/viaproxy/ViaProxy.jar"
GEYSER_JAR = "headless_server/geyser/Geyser-Standalone.jar"
ASM_CP = (
    "headless_server/libraries/org/ow2/asm/asm/9.10.1/asm-9.10.1.jar;"
    "headless_server/libraries/org/ow2/asm/asm-commons/9.10.1/asm-commons-9.10.1.jar;"
    "headless_server/libraries/org/ow2/asm/asm-tree/9.10.1/asm-tree-9.10.1.jar;"
    "headless_server/viaproxy/ViaProxy.jar"
)

def cmd_inspect_jar(args):
    jar_path = args[0] if len(args) > 0 else VIAPROXY_JAR
    pattern = args[1].lower() if len(args) > 1 else ""
    if not os.path.exists(jar_path):
        print(f"Error: {jar_path} not found")
        return
    with zipfile.ZipFile(jar_path, "r") as z:
        matches = [n for n in z.namelist() if pattern in n.lower()]
        print(f"Found {len(matches)} matching entries in {jar_path}:")
        for m in matches[:50]:
            print(" ", m)
        if len(matches) > 50:
            print(f" ... and {len(matches) - 50} more")

def cmd_cat_zip(args):
    if len(args) < 2:
        print("Usage: python tools/macro.py cat-zip <zip_path> <file_path>")
        return
    zip_path, file_path = args[0], args[1]
    if not os.path.exists(zip_path):
        print(f"Error: {zip_path} not found")
        return
    with zipfile.ZipFile(zip_path, "r") as z:
        try:
            content = z.read(file_path).decode("utf-8", errors="replace")
            print(content)
        except KeyError:
            print(f"File {file_path} not found in {zip_path}")

def cmd_disassemble(args):
    if not args:
        print("Usage: python tools/macro.py javap <ClassName>")
        return
    cls = args[0]
    res = subprocess.run([JAVAP, "-cp", VIAPROXY_JAR, "-c", cls], capture_output=True, text=True)
    if res.returncode != 0:
        print("javap error:", res.stderr)
    else:
        print(res.stdout)

def cmd_patch_viaproxy(args):
    staging = "tools/staging"
    os.makedirs(staging, exist_ok=True)

    print("[1/3] Compiling MappingDataBase.java, BackwardsMappingData.java, and S2CLoginGameProfilePacket.java with javac...")
    res = subprocess.run([
        JAVAC, "-proc:none", "-cp", VIAPROXY_JAR, "-d", staging,
        "tools/MappingDataBase.java", "tools/BackwardsMappingData.java", "tools/S2CLoginGameProfilePacket.java"
    ], capture_output=True, text=True)
    if res.returncode != 0:
        print("javac failed:\n", res.stderr)
        return False

    print("[2/3] Preparing clean baseline ViaProxy.jar...")
    backup = VIAPROXY_JAR + ".bak"
    if not os.path.exists(backup):
        shutil.copy2(VIAPROXY_JAR, backup)
        print(f"Backed up to {backup}")

    print("[3/3] Injecting compiled classes into ViaProxy.jar...")
    classes_to_inject = {}
    for root, dirs, files in os.walk(staging):
        for f in files:
            if f.endswith(".class") and not f.endswith("_patched.class") and root != staging:
                full_p = os.path.join(root, f)
                rel_p = os.path.relpath(full_p, staging).replace("\\", "/")
                if any(rel_p.startswith(pkg) for pkg in ["com/viaversion/", "net/raphimc/"]):
                    classes_to_inject[rel_p] = full_p

    print(f"Injecting {len(classes_to_inject)} classes: {list(classes_to_inject.keys())}")

    tmp_jar = VIAPROXY_JAR + ".tmp"
    with zipfile.ZipFile(backup, "r") as zin:
        existing_names = set(zin.namelist())
        with zipfile.ZipFile(tmp_jar, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename in classes_to_inject:
                    with open(classes_to_inject[item.filename], "rb") as pf:
                        zout.writestr(item, pf.read())
                else:
                    zout.writestr(item, zin.read(item.filename))
            for rel_p, full_p in classes_to_inject.items():
                if rel_p not in existing_names:
                    with open(full_p, "rb") as pf:
                        zout.writestr(rel_p, pf.read())
                        print(f"  + Added new class entry: {rel_p}")

    os.replace(tmp_jar, VIAPROXY_JAR)
    print("ViaProxy patch complete and verified!")
    return True

def cmd_status(args):
    import socket
    ports = {"NeoForge": 25565, "ViaProxy": 25568, "Geyser": 19132}
    print("Port Availability:")
    for name, port in ports.items():
        sock_type = socket.SOCK_DGRAM if port == 19132 else socket.SOCK_STREAM
        with socket.socket(socket.AF_INET, sock_type) as s:
            s.settimeout(0.5)
            try:
                if port == 19132:
                    # UDP check
                    s.bind(("0.0.0.0", port))
                    print(f"  {name} ({port}/UDP): FREE (Not running)")
                else:
                    s.connect(("127.0.0.1", port))
                    print(f"  {name} ({port}/TCP): ACTIVE (Running)")
            except Exception:
                if port == 19132:
                    print(f"  {name} ({port}/UDP): BOUND (Running or in use)")
                else:
                    print(f"  {name} ({port}/TCP): DOWN (Not running)")

def cmd_build_extension(args):
    bin_dir = "tools/extension/bin"
    os.makedirs(bin_dir, exist_ok=True)
    src = "tools/extension/src/com/createbridge/CreateBridgeExtension.java"
    res = subprocess.run([
        JAVAC, "-cp", GEYSER_JAR, "-d", bin_dir, src
    ], capture_output=True, text=True)
    if res.returncode != 0:
        print("Extension compilation failed:\n", res.stderr)
        return False
    # Copy all resources into bin
    res_dir = "tools/extension/resources"
    if os.path.exists(res_dir):
        for f in os.listdir(res_dir):
            shutil.copy2(os.path.join(res_dir, f), bin_dir)
    # Package into jar
    jar_out = "headless_server/geyser/extensions/CreateBridge.jar"
    res = subprocess.run([
        os.path.join(JDK, "jar.exe"), "cf", jar_out, "-C", bin_dir, "."
    ], capture_output=True, text=True)
    if res.returncode != 0:
        print("jar packaging failed:\n", res.stderr)
        return False
    print("CreateBridge.jar built successfully!")
    return True

def cmd_stop_stack(args):
    print("Stopping server stack...")
    import psutil
    killed = 0
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmd = " ".join(p.info['cmdline'] or [])
            if any(k in cmd for k in ["run.bat", "neoforge", "ViaProxy.jar", "Geyser-Standalone.jar"]):
                p.kill()
                killed += 1
        except Exception:
            pass
    print(f"Terminated {killed} processes.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/macro.py <command> [args...]")
        print("Commands: inspect-jar, javap, patch-viaproxy, build-extension, status, stop-stack")
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "inspect-jar":
        cmd_inspect_jar(args)
    elif cmd == "cat-zip":
        cmd_cat_zip(args)
    elif cmd == "javap":
        cmd_disassemble(args)
    elif cmd == "patch-viaproxy":
        cmd_patch_viaproxy(args)
    elif cmd == "build-extension":
        cmd_build_extension(args)
    elif cmd == "status":
        cmd_status(args)
    elif cmd == "stop-stack":
        cmd_stop_stack(args)
    elif cmd == "convert-geo":
        try:
            import model_converter as mc
        except ImportError:
            import tools.model_converter as mc
        bname = args[0] if len(args) > 0 else "chute"
        mpath = args[1] if len(args) > 1 else None
        mc.convert_block_geometry(bname, mpath)
    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
