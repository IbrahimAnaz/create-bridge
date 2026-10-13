import zipfile
import subprocess

javap = r"C:\Program Files\Java\jdk-21.0.12\bin\javap.exe"
jar = r"headless_server\libraries\net\neoforged\neoforge\21.1.248\neoforge-21.1.248-server.jar"
with zipfile.ZipFile(jar, "r") as z:
    for n in z.namelist():
        if "DataComponentPatch$1" in n:
            print("Found:", n)
            with open("real_dcp1.class", "wb") as f:
                f.write(z.read(n))

res = subprocess.run([javap, "-c", "-p", "real_dcp1.class"], capture_output=True, text=True)
print(res.stdout)
