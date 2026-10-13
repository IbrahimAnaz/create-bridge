import zipfile

with zipfile.ZipFile('headless_server/viaproxy/ViaProxy.jar') as z:
    for n in z.namelist():
        if '1.21' in n and n.endswith('.nbt'):
            print(n)
