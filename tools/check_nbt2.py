import zipfile, gzip, io

with zipfile.ZipFile('headless_server/viaproxy/ViaProxy.jar') as z:
    raw = z.read('assets/viaversion/data/identifiers-1.21.nbt')
    # see if gzipped
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    print("Length uncompressed:", len(raw))
    # print some strings found in raw
    import re
    strings = re.findall(b'[a-z0-9_/-]{3,}', raw)
    items = [s.decode('ascii', errors='ignore') for s in strings if b':' in s or b'item' in s or b'fletch' in s or b'compost' in s]
    print("Sample items:", items[:20])
    for s in ['compost', 'fletch', 'millstone', 'cogwheel']:
        matches = [x for x in items if s in x]
        print(f"Matches for {s}:", matches)
