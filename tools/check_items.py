import zipfile, json

with zipfile.ZipFile('headless_server/geyser/Geyser-Standalone.jar') as z:
    for name in z.namelist():
        if name.endswith('items.json'):
            print("Found:", name)
            data = json.loads(z.read(name).decode('utf-8'))
            if isinstance(data, list):
                for idx, entry in enumerate(data):
                    if isinstance(entry, dict):
                        # print some entries
                        name_val = entry.get('name') or entry.get('id')
                        if name_val and any(x in str(name_val) for x in ['compost', 'fletch']):
                            print(idx, entry)
            elif isinstance(data, dict):
                for idx, (k, v) in enumerate(data.items()):
                    if any(x in str(k) for x in ['compost', 'fletch']):
                        print(f"Java ID (index): {idx}, Key: {k}, Data: {v}")

