import subprocess

javap = r"C:\Program Files\Java\jdk-21.0.12\bin\javap.exe"
res = subprocess.run([javap, "-c", "-p", "-v", "adc.class"], capture_output=True, text=True)
lines = res.stdout.splitlines()

# Search for networkSynchronized or StreamCodec in the entire decompiled output
for i, l in enumerate(lines):
    if "networkSynchronized" in l or "streamCodec" in l:
        print(f"--- Line {i}: {l} ---")
        for j in range(max(0, i-10), min(len(lines), i+10)):
            print(f"{j}: {lines[j]}")
