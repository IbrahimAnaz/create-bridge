import os
import subprocess
import shutil
from pathlib import Path

ROOT = Path(r"c:\Users\ibrah\Downloads\crt aro")
PORTABLE_EXT = ROOT / "portable_bridge" / "extension"
PORTABLE_GEYSER_EXT = ROOT / "portable_bridge" / "geyser" / "extensions"
HEADLESS_GEYSER_EXT = ROOT / "headless_server" / "geyser" / "extensions"
BIN_DIR = PORTABLE_EXT / "bin"
SRC_DIR = PORTABLE_EXT / "src"
RES_DIR = PORTABLE_EXT / "resources"

GEYSER_JAR = ROOT / "portable_bridge" / "geyser" / "Geyser-Standalone.jar"
JAVAC = r"C:\Program Files\Java\jdk-21.0.12\bin\javac.exe"
JAR_BIN = r"C:\Program Files\Java\jdk-21.0.12\bin\jar.exe"

def compile_and_package():
    print("[1/3] Preparing build directory...")
    if BIN_DIR.exists():
        shutil.rmtree(BIN_DIR)
    BIN_DIR.mkdir(parents=True, exist_ok=True)

    print("[2/3] Compiling Java classes...")
    sources = list(SRC_DIR.rglob("*.java"))
    print(f"Found {len(sources)} source files.")
    
    cmd = [
        JAVAC,
        "-cp", str(GEYSER_JAR),
        "-d", str(BIN_DIR),
        *[str(s) for s in sources]
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Compilation FAILED:\n{res.stderr}")
        return False
    print("Classes compiled successfully.")

    # Copy resources
    print("Copying resources to bin...")
    for res_file in RES_DIR.iterdir():
        if res_file.is_file():
            shutil.copy2(res_file, BIN_DIR / res_file.name)
            print(f"  + Added resource: {res_file.name}")

    print("[3/3] Packaging CreateBridge.jar...")
    PORTABLE_GEYSER_EXT.mkdir(parents=True, exist_ok=True)
    HEADLESS_GEYSER_EXT.mkdir(parents=True, exist_ok=True)

    out_jar = PORTABLE_GEYSER_EXT / "CreateBridge.jar"
    cmd_jar = [
        JAR_BIN, "cf", str(out_jar),
        "-C", str(BIN_DIR), "."
    ]
    res_jar = subprocess.run(cmd_jar, capture_output=True, text=True)
    if res_jar.returncode != 0:
        print(f"Jar packaging FAILED:\n{res_jar.stderr}")
        return False

    shutil.copy2(out_jar, HEADLESS_GEYSER_EXT / "CreateBridge.jar")
    size = out_jar.stat().st_size
    print(f"Successfully generated CreateBridge.jar ({size} bytes) for both bridges!")
    return True

if __name__ == "__main__":
    compile_and_package()
