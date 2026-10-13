import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(r"c:\Users\ibrah\Downloads\crt aro")
MOD_DIR = ROOT / "headless_server" / "companion_mod"
SRC_DIR = MOD_DIR / "src" / "main" / "java"
RES_DIR = MOD_DIR / "src" / "main" / "resources"
BUILD_DIR = MOD_DIR / "build" / "classes"
OUT_JAR = ROOT / "headless_server" / "mods" / "createbridge-companion.jar"

JAVAC = r"C:\Program Files\Java\jdk-21.0.12\bin\javac.exe"
JAR_BIN = r"C:\Program Files\Java\jdk-21.0.12\bin\jar.exe"
CP_FILE = ROOT / "headless_server" / "compile_cp.txt"

def build():
    print("[1/4] Preparing build directory...")
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    print("[2/4] Reading classpath...")
    with open(CP_FILE, "r", encoding="utf-8") as f:
        cp = f.read().strip()
    jarjar_dir = ROOT / "headless_server" / "libraries" / "create_jarjar"
    if jarjar_dir.exists():
        for j in jarjar_dir.glob("*.jar"):
            cp = f"{cp};{j}"

    print("[3/4] Compiling Java sources...")
    sources = [str(p) for p in SRC_DIR.rglob("*.java")]
    print(f"Found {len(sources)} source files.")
    
    cmd = [
        JAVAC,
        "-cp", cp,
        "-d", str(BUILD_DIR),
        *sources
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Compilation FAILED:")
        print(res.stderr)
        return False
    print("Compilation succeeded.")

    # Copy resources
    print("Copying resources...")
    for root, dirs, files in os.walk(RES_DIR):
        rel = Path(root).relative_to(RES_DIR)
        target_dir = BUILD_DIR / rel
        target_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            shutil.copy2(Path(root) / f, target_dir / f)
            print(f"  + Added resource: {rel / f}")

    print("[4/4] Packaging jar...")
    OUT_JAR.parent.mkdir(parents=True, exist_ok=True)
    cmd_jar = [
        JAR_BIN, "cf", str(OUT_JAR),
        "-C", str(BUILD_DIR), "."
    ]
    res_jar = subprocess.run(cmd_jar, capture_output=True, text=True)
    if res_jar.returncode != 0:
        print("Packaging FAILED:")
        print(res_jar.stderr)
        return False

    size = OUT_JAR.stat().st_size
    print(f"Successfully generated {OUT_JAR.name} ({size} bytes) in headless_server/mods!")
    return True

if __name__ == "__main__":
    build()
