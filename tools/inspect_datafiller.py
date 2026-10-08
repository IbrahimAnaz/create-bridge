import zipfile
import subprocess

with zipfile.ZipFile("headless_server/viaproxy/ViaProxy.jar") as z:
    for item in z.infolist():
        if item.filename.endswith("StructuredDataType$DataFiller.class"):
            with open("tools/RealDataFiller.class", "wb") as f:
                f.write(z.read(item.filename))
            print("Extracted RealDataFiller.class", item.file_size)

res = subprocess.run([r"C:\Program Files\Java\jdk-21.0.12\bin\javap.exe", "-p", "-c", "tools/RealDataFiller.class"], text=True, capture_output=True)
print(res.stdout[:3000])
