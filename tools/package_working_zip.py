import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_ZIP = ROOT / "create_bridge_working.zip"

EXCLUDE_DIRS = {
    ".git",
    ".gradle",
    "world",
    "world_backup",
    "logs",
    "dumps",
    "test_temp",
    ".bridge_actions",
    "bridge_cache",
    "__pycache__",
    "temp_decomp",
    "com",
    "node_modules",
    "reference"
}

EXCLUDE_FILES = {
    "create_bridge_working.zip",
    "create_bridge.zip",
    "create_bridge_bundle.tar.gz"
}

EXCLUDE_EXTS = {
    ".class",
    ".javap",
    ".log",
    ".tmp"
}

def should_exclude(rel_path: Path) -> bool:
    parts = rel_path.parts
    # Exclude any folder match
    for part in parts:
        if part in EXCLUDE_DIRS:
            return True
    
    # Exclude files
    filename = rel_path.name
    if filename in EXCLUDE_FILES:
        return True
    
    ext = rel_path.suffix.lower()
    # Don't exclude .class inside libraries or jar/zip
    if ext in EXCLUDE_EXTS:
        if "libraries" not in parts and "mods" not in parts:
            return True
            
    return False

def package_repo():
    print(f"[Package] Building clean working zip: {OUTPUT_ZIP.name}...")
    file_count = 0
    total_uncompressed = 0

    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for dirpath, dirnames, filenames in os.walk(ROOT):
            rel_dir = Path(dirpath).relative_to(ROOT)
            
            # Prune excluded directories
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

            for f in filenames:
                full_path = Path(dirpath) / f
                rel_path = full_path.relative_to(ROOT)

                if should_exclude(rel_path):
                    continue

                try:
                    zf.write(full_path, str(rel_path))
                    file_count += 1
                    total_uncompressed += full_path.stat().st_size
                    if file_count % 1000 == 0:
                        print(f"  ... packaged {file_count} files ({total_uncompressed / (1024*1024):.1f} MB uncompressed)")
                except Exception as e:
                    print(f"  Warning: Skipping {rel_path}: {e}")

    zip_size = OUTPUT_ZIP.stat().st_size
    print(f"\n[Package Complete] {file_count} files packaged into {OUTPUT_ZIP.name}")
    print(f"  Uncompressed: {total_uncompressed / (1024*1024):.2f} MB")
    print(f"  Zip Archive:  {zip_size / (1024*1024):.2f} MB")
    return OUTPUT_ZIP

if __name__ == "__main__":
    package_repo()
