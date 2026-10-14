import os
import subprocess
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORTABLE_EXT = ROOT / "portable_bridge" / "extension"
HEADLESS_GEYSER = ROOT / "headless_server" / "geyser"
HEADLESS_GEYSER_EXT = HEADLESS_GEYSER / "extensions"
BIN_DIR = PORTABLE_EXT / "bin"
SRC_DIR = PORTABLE_EXT / "src"
RES_DIR = PORTABLE_EXT / "resources"

GEYSER_JAR = HEADLESS_GEYSER / "Geyser-Standalone.jar"

# Resolve javac and jar across Windows, Linux, and Cloud environments (strictly targeting Java 21)
def find_jdk_binary(name):
    # Check standard Windows location for JDK 21 first
    win_cand = Path(r"C:\Program Files\Java\jdk-21.0.12\bin") / (name + ".exe")
    if win_cand.exists():
        return str(win_cand)
    # Check JAVA_HOME
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        cand = Path(java_home) / "bin" / (name + (".exe" if os.name == "nt" else ""))
        if cand.exists():
            return str(cand)
    # Check PATH
    found = shutil.which(name)
    if found:
        return found
    # Fallback to binary name
    return name

JAVAC = find_jdk_binary("javac")
JAR_BIN = find_jdk_binary("jar")

def ensure_geyser_jar():
    if not GEYSER_JAR.exists():
        print(f"[compile_bridge] Geyser jar not found at {GEYSER_JAR}. Downloading Geyser-Standalone...", flush=True)
        GEYSER_JAR.parent.mkdir(parents=True, exist_ok=True)
        import urllib.request
        url = "https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest/downloads/standalone"
        urllib.request.urlretrieve(url, GEYSER_JAR)
        print("[compile_bridge] Geyser-Standalone jar downloaded successfully.", flush=True)

def compile_and_package():
    ensure_geyser_jar()
    print("[1/3] Preparing build directory...")
    if BIN_DIR.exists():
        shutil.rmtree(BIN_DIR)
    BIN_DIR.mkdir(parents=True, exist_ok=True)

    print("[2/3] Compiling Java classes (targeting Java 21)...")
    sources = list(SRC_DIR.rglob("*.java"))
    print(f"Found {len(sources)} source files.")
    
    cmd = [
        JAVAC,
        "--release", "21",
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
    HEADLESS_GEYSER_EXT.mkdir(parents=True, exist_ok=True)
    build_dir = PORTABLE_EXT / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    out_jar = build_dir / "CreateBridge.jar"
    cmd_jar = [
        JAR_BIN, "cf", str(out_jar),
        "-C", str(BIN_DIR), "."
    ]
    res_jar = subprocess.run(cmd_jar, capture_output=True, text=True)
    if res_jar.returncode != 0:
        print(f"Jar packaging FAILED:\n{res_jar.stderr}")
        return False

    size = out_jar.stat().st_size
    print(f"Successfully generated CreateBridge.jar ({size} bytes) in {build_dir}!")
    try:
        shutil.copy2(out_jar, HEADLESS_GEYSER_EXT / "CreateBridge.jar")
        print(f"Deployed to {HEADLESS_GEYSER_EXT}")
    except Exception as e:
        print(f"Note: Could not copy directly to {HEADLESS_GEYSER_EXT} (file locked by active Geyser): {e}")
    return True

if __name__ == "__main__":
    compile_and_package()
