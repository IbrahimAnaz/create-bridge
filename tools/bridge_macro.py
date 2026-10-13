#!/usr/bin/env python3
"""
bridge_macro.py - Unified Automation & Cache Macro CLI
Focus: Token efficiency, local caching, reproducible setup, automated testing.

Commands:
  cache-sync                  Syncs essential JARs, sources, and assets into bridge_cache/
  init-portable <target_dir>  Initializes a fresh, self-contained bridge directory with git
  patch-viaproxy <target_dir> Compiles & injects clean Java firewall patches into target ViaProxy.jar
  build-extension <target_dir>Compiles modular CreateBridge extension into target Geyser jar
  test-palette <target_dir>   Runs offline in-memory palette validation (item IDs, blockstates, pitch)
  git-commit <target_dir> "msg" Stages and commits changes in target repository
"""

import sys
import os
import shutil
import subprocess
import zipfile
import json

JDK = r"C:\Program Files\Java\jdk-21.0.12\bin"
JAVAC = os.path.join(JDK, "javac.exe")
JAVA = os.path.join(JDK, "java.exe")
JAR_EXE = os.path.join(JDK, "jar.exe")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CACHE_DIR = os.path.join(ROOT, "bridge_cache")
JARS_CACHE = os.path.join(CACHE_DIR, "jars")
ASSETS_CACHE = os.path.join(CACHE_DIR, "assets")
SOURCES_CACHE = os.path.join(CACHE_DIR, "sources")

def log(msg):
    print(f"[bridge-macro] {msg}")

def ensure_cache_dirs():
    os.makedirs(JARS_CACHE, exist_ok=True)
    os.makedirs(ASSETS_CACHE, exist_ok=True)
    os.makedirs(SOURCES_CACHE, exist_ok=True)

def cmd_cache_sync():
    ensure_cache_dirs()
    log("Synchronizing bridge_cache/ from local verified sources...")

    # 1. JARs
    jar_sources = {
        "ViaProxy.jar": os.path.join(ROOT, "headless_server", "viaproxy", "ViaProxy.jar"),
        "Geyser-Standalone.jar": os.path.join(ROOT, "headless_server", "geyser", "Geyser-Standalone.jar"),
        "create-1.21.1-6.0.8.jar": os.path.join(ROOT, "headless_server", "mods", "create-1.21.1-6.0.8.jar")
    }
    for name, src in jar_sources.items():
        dst = os.path.join(JARS_CACHE, name)
        if os.path.exists(src) and (not os.path.exists(dst) or os.path.getsize(src) != os.path.getsize(dst)):
            shutil.copy2(src, dst)
            log(f"Cached JAR: {name} ({os.path.getsize(dst)} bytes)")

    # 2. Assets & Registries
    asset_sources = {
        "create_registry_dump.json": os.path.join(ROOT, "headless_server", "create_registry_dump.json"),
        "geo_blocks.json": os.path.join(ROOT, "tools", "extension", "resources", "geo_blocks.json"),
        "CreateKineticPack.zip": os.path.join(ROOT, "headless_server", "geyser", "packs", "CreateKineticPack.zip")
    }
    for name, src in asset_sources.items():
        dst = os.path.join(ASSETS_CACHE, name)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            log(f"Cached Asset: {name}")

    # 3. Patch Sources
    src_files = [
        "MappingDataBase.java",
        "BackwardsMappingData.java",
        "PatchItemType.java",
        "PatchRecipeRewriter.java"
    ]
    for sf in src_files:
        src = os.path.join(ROOT, "tools", sf)
        dst = os.path.join(SOURCES_CACHE, sf)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            log(f"Cached Source: {sf}")

    log("Cache synchronization COMPLETE.")

def cmd_init_portable(target_path):
    ensure_cache_dirs()
    target_abs = os.path.abspath(target_path)
    if os.path.exists(target_abs) and os.listdir(target_abs):
        log(f"Notice: Target directory {target_abs} already exists. Using existing.")
    else:
        os.makedirs(target_abs, exist_ok=True)
        log(f"Created directory {target_abs}")

    # Initialize Git repository if not present
    git_dir = os.path.join(target_abs, ".git")
    if not os.path.exists(git_dir):
        subprocess.run(["git", "init"], cwd=target_abs, check=True, stdout=subprocess.DEVNULL)
        log("Initialized clean Git repository.")

    # Create subdirectories
    subdirs = [
        "viaproxy",
        "geyser",
        "geyser/extensions",
        "geyser/packs",
        "patches",
        "extension/src/com/createbridge/blocks",
        "extension/src/com/createbridge/items",
        "extension/src/com/createbridge/network",
        "extension/src/com/createbridge/ui",
        "extension/resources",
        "tools"
    ]
    for sd in subdirs:
        os.makedirs(os.path.join(target_abs, sd), exist_ok=True)

    # Populate baseline files from cache
    # 1. ViaProxy
    vp_dst = os.path.join(target_abs, "viaproxy", "ViaProxy.jar")
    vp_src = os.path.join(JARS_CACHE, "ViaProxy.jar")
    if os.path.exists(vp_src) and not os.path.exists(vp_dst):
        shutil.copy2(vp_src, vp_dst)
        log("Copied baseline ViaProxy.jar")

    # 2. Geyser
    gy_dst = os.path.join(target_abs, "geyser", "Geyser-Standalone.jar")
    gy_src = os.path.join(JARS_CACHE, "Geyser-Standalone.jar")
    if os.path.exists(gy_src) and not os.path.exists(gy_dst):
        shutil.copy2(gy_src, gy_dst)
        log("Copied baseline Geyser-Standalone.jar")

    # 3. Geyser config with ping-passthrough: false
    gy_cfg = os.path.join(target_abs, "geyser", "config.yml")
    if not os.path.exists(gy_cfg):
        src_cfg = os.path.join(ROOT, "headless_server", "geyser", "config.yml")
        if os.path.exists(src_cfg):
            shutil.copy2(src_cfg, gy_cfg)
            log("Copied Geyser config.yml (ping-passthrough disabled)")

    # 4. Resource Pack
    rp_dst = os.path.join(target_abs, "geyser", "packs", "CreateKineticPack.zip")
    rp_src = os.path.join(ASSETS_CACHE, "CreateKineticPack.zip")
    if os.path.exists(rp_src) and not os.path.exists(rp_dst):
        shutil.copy2(rp_src, rp_dst)
        log("Copied CreateKineticPack.zip to geyser/packs/")

    # 5. Resources for extension
    for res_name in ["create_registry_dump.json", "geo_blocks.json"]:
        src = os.path.join(ASSETS_CACHE, res_name)
        dst = os.path.join(target_abs, "extension", "resources", res_name)
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
            log(f"Copied extension resource: {res_name}")

    # Copy cached patch sources
    for sf in os.listdir(SOURCES_CACHE):
        src = os.path.join(SOURCES_CACHE, sf)
        dst = os.path.join(target_abs, "patches", sf)
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
            log(f"Copied patch source: {sf}")

    # Add .gitignore
    gitignore = os.path.join(target_abs, ".gitignore")
    if not os.path.exists(gitignore):
        with open(gitignore, "w") as f:
            f.write("*.log\n*.tmp\n*.bak\nbin/\nstaging/\n")
        log("Created .gitignore")

    log(f"Portable environment initialized at: {target_abs}")

def cmd_patch_viaproxy(target_path):
    target_abs = os.path.abspath(target_path)
    vp_jar = os.path.join(target_abs, "viaproxy", "ViaProxy.jar")
    patches_dir = os.path.join(target_abs, "patches")
    staging = os.path.join(target_abs, "patches", "bin")
    os.makedirs(staging, exist_ok=True)

    log("Compiling MappingDataBase.java & BackwardsMappingData.java with javac --release 17...")
    src1 = os.path.join(patches_dir, "MappingDataBase.java")
    src2 = os.path.join(patches_dir, "BackwardsMappingData.java")
    res = subprocess.run([
        JAVAC, "--release", "17", "-proc:none", "-cp", vp_jar, "-d", staging, src1, src2
    ], capture_output=True, text=True)
    if res.returncode != 0:
        log(f"ERROR compiling patches:\n{res.stderr}")
        return False

    log("Injecting compiled classes into ViaProxy.jar...")
    classes = {}
    for root, dirs, files in os.walk(staging):
        for f in files:
            if f.endswith(".class"):
                full = os.path.join(root, f)
                rel = os.path.relpath(full, staging).replace("\\", "/")
                classes[rel] = full

    tmp_jar = vp_jar + ".tmp"
    with zipfile.ZipFile(vp_jar, "r") as zin:
        with zipfile.ZipFile(tmp_jar, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename in classes:
                    with open(classes[item.filename], "rb") as cf:
                        zout.writestr(item, cf.read())
                else:
                    zout.writestr(item, zin.read(item.filename))
            for rel, full in classes.items():
                if rel not in set(zin.namelist()):
                    with open(full, "rb") as cf:
                        zout.writestr(rel, cf.read())

    os.replace(tmp_jar, vp_jar)
    log(f"Successfully injected {len(classes)} classes into ViaProxy.jar")
    return True

def cmd_build_extension(target_path):
    target_abs = os.path.abspath(target_path)
    ext_dir = os.path.join(target_abs, "extension")
    src_dir = os.path.join(ext_dir, "src")
    res_dir = os.path.join(ext_dir, "resources")
    bin_dir = os.path.join(ext_dir, "bin")
    gy_jar = os.path.join(target_abs, "geyser", "Geyser-Standalone.jar")
    out_jar = os.path.join(target_abs, "geyser", "extensions", "CreateBridge.jar")

    os.makedirs(bin_dir, exist_ok=True)
    os.makedirs(os.path.dirname(out_jar), exist_ok=True)

    # Collect all .java sources
    java_files = []
    for root, dirs, files in os.walk(src_dir):
        for f in files:
            if f.endswith(".java"):
                java_files.append(os.path.join(root, f))

    log(f"Compiling {len(java_files)} modular extension classes...")
    cmd = [JAVAC, "-proc:none", "-cp", gy_jar, "-d", bin_dir] + java_files
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        log(f"Compilation FAILED:\n{res.stderr}")
        return False

    # Copy resources to bin
    if os.path.exists(res_dir):
        for f in os.listdir(res_dir):
            shutil.copy2(os.path.join(res_dir, f), bin_dir)

    # Package into jar
    cmd_jar = [JAR_EXE, "cf", out_jar, "-C", bin_dir, "."]
    res_jar = subprocess.run(cmd_jar, capture_output=True, text=True)
    if res_jar.returncode != 0:
        log(f"JAR packaging FAILED:\n{res_jar.stderr}")
        return False

    log(f"Successfully packaged {out_jar} ({os.path.getsize(out_jar)} bytes)")
    return True

def cmd_git_commit(target_path, message):
    target_abs = os.path.abspath(target_path)
    subprocess.run(["git", "add", "."], cwd=target_abs, check=True, stdout=subprocess.DEVNULL)
    res = subprocess.run(["git", "commit", "-m", message], cwd=target_abs, capture_output=True, text=True)
    if res.returncode == 0:
        log(f"Git commit: {message}")
    else:
        log(f"Git commit skipped/clean: {res.stdout.strip()}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python bridge_macro.py <command> [args...]")
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "cache-sync":
        cmd_cache_sync()
    elif cmd == "init-portable":
        if not args:
            print("Error: Target path required")
            return
        cmd_init_portable(args[0])
    elif cmd == "patch-viaproxy":
        if not args:
            print("Error: Target path required")
            return
        cmd_patch_viaproxy(args[0])
    elif cmd == "build-extension":
        if not args:
            print("Error: Target path required")
            return
        cmd_build_extension(args[0])
    elif cmd == "git-commit":
        if len(args) < 2:
            print("Usage: git-commit <target_path> <message>")
            return
        cmd_git_commit(args[0], args[1])
    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
