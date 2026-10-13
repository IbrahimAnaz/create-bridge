import shutil
import zipfile
import os

jars = [
    r"headless_server\libraries\net\neoforged\neoforge\21.1.248\neoforge-21.1.248-server.jar",
    r"headless_server\libraries\net\minecraft\server\1.21.1-20240808.144430\server-1.21.1-20240808.144430-srg.jar"
]

target_entry = "net/minecraft/core/component/DataComponentPatch$1.class"

with open("real_dcp1_patched.class", "rb") as f:
    patched_bytes = f.read()

for jar in jars:
    bak = jar + ".bak"
    if not os.path.exists(bak):
        shutil.copyfile(jar, bak)
        print(f"Backed up {jar} to {bak}")

    tmp = jar + ".tmp"
    with zipfile.ZipFile(jar, "r") as zin:
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == target_entry:
                    print(f"Replacing {target_entry} in {jar}...")
                    zout.writestr(item, patched_bytes)
                else:
                    zout.writestr(item, zin.read(item.filename))

    os.replace(tmp, jar)
    print(f"[+] Successfully injected into {jar}!")

print("ALL JARS INJECTED!")
