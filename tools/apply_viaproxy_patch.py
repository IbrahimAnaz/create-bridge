import os
import zipfile
import subprocess
import shutil

JAR_PATH = "headless_server/viaproxy/ViaProxy.jar"
STAGING = "tools/staging"
os.makedirs(STAGING, exist_ok=True)

print("1. Extracting classes from ViaProxy.jar...")
with zipfile.ZipFile(JAR_PATH, "r") as z:
    with open(os.path.join(STAGING, "MappingDataBase.class"), "wb") as f:
        f.write(z.read("com/viaversion/viaversion/api/data/MappingDataBase.class"))
    with open(os.path.join(STAGING, "BackwardsMappingData.class"), "wb") as f:
        f.write(z.read("com/viaversion/viabackwards/api/data/BackwardsMappingData.class"))

print("2. Compiling PatchViaProxyItems.java...")
javac = "C:\\Program Files\\Java\\jdk-21.0.12\\bin\\javac.exe"
asm_cp = "headless_server/libraries/org/ow2/asm/asm/9.10.1/asm-9.10.1.jar;headless_server/libraries/org/ow2/asm/asm-commons/9.10.1/asm-commons-9.10.1.jar;headless_server/libraries/org/ow2/asm/asm-tree/9.10.1/asm-tree-9.10.1.jar;headless_server/viaproxy/ViaProxy.jar"
res = subprocess.run([
    javac,
    "-cp", asm_cp,
    "-d", "tools",
    "tools/PatchViaProxyItems.java"
], capture_output=True, text=True)
if res.returncode != 0:
    print("javac failed:", res.stderr)
    exit(1)

print("3. Running PatchViaProxyItems...")
res = subprocess.run([
    "java",
    "-cp", "tools;" + asm_cp,
    "PatchViaProxyItems"
], capture_output=True, text=True)
print(res.stdout)
if res.returncode != 0:
    print("PatchViaProxyItems failed:", res.stderr)
    exit(1)

print("4. Verifying patched bytecode with javap...")
javap = "C:\\Program Files\\Java\\jdk-21.0.12\\bin\\javap.exe"

print("\n--- MappingDataBase.getOldItemId: ---")
p = subprocess.run([javap, "-c", "-p", "tools/staging/MappingDataBase_patched.class"], capture_output=True, text=True)
lines = p.stdout.splitlines()
recording = False
for line in lines:
    if "int getOldItemId(" in line or "int getOldBlockId(" in line:
        recording = True
    if recording:
        print(line)
        if "ireturn" in line:
            print("---")
            recording = False

print("\n--- BackwardsMappingData.getNewItemId & getNewBlockId: ---")
p2 = subprocess.run([javap, "-c", "-p", "tools/staging/BackwardsMappingData_patched.class"], capture_output=True, text=True)
lines = p2.stdout.splitlines()
recording = False
for line in lines:
    if "int getNewItemId(" in line or "int getNewBlockId(" in line:
        recording = True
    if recording:
        print(line)
        if "ireturn" in line:
            print("---")
            recording = False

print("5. Injecting into ViaProxy.jar...")
# Create backup
backup_path = JAR_PATH + ".bak"
if not os.path.exists(backup_path):
    shutil.copy2(JAR_PATH, backup_path)
    print("Created backup at", backup_path)

# Update jar using python zipfile
tmp_jar = JAR_PATH + ".tmp"
with zipfile.ZipFile(JAR_PATH, "r") as zin:
    with zipfile.ZipFile(tmp_jar, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "com/viaversion/viaversion/api/data/MappingDataBase.class":
                with open("tools/staging/MappingDataBase_patched.class", "rb") as pf:
                    zout.writestr(item, pf.read())
            elif item.filename == "com/viaversion/viabackwards/api/data/BackwardsMappingData.class":
                with open("tools/staging/BackwardsMappingData_patched.class", "rb") as pf:
                    zout.writestr(item, pf.read())
            else:
                zout.writestr(item, zin.read(item.filename))

os.replace(tmp_jar, JAR_PATH)
print("Successfully injected patched classes into", JAR_PATH)
