import os
import zipfile
from pathlib import Path

ROOT = Path(r"c:\Users\ibrah\Downloads\crt aro")
RP_DIR = ROOT / "create_cogwheel_rp"
GEYSER_PACKS = ROOT / "headless_server" / "geyser" / "packs"
PACK_ZIP = GEYSER_PACKS / "CreateKineticPack.zip"

def main():
    GEYSER_PACKS.mkdir(parents=True, exist_ok=True)
    if PACK_ZIP.exists():
        PACK_ZIP.unlink()
    
    file_count = 0
    with zipfile.ZipFile(PACK_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for f in RP_DIR.rglob("*"):
            if f.is_file():
                rel_path = str(f.relative_to(RP_DIR)).replace("\\", "/")
                z.write(f, rel_path)
                file_count += 1
                
    size = PACK_ZIP.stat().st_size
    print(f"Successfully packed {file_count} files into {PACK_ZIP.name} ({size} bytes)")

if __name__ == "__main__":
    main()
