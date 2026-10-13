import zipfile, json

with zipfile.ZipFile('headless_server/mods/create-1.21.1-6.0.8.jar', 'r') as z:
    d = json.loads(z.read('assets/create/models/block/mechanical_pump/item.json'))
    for i, el in enumerate(d.get('elements', [])):
        print(f"Elem {i}: from={el.get('from')} to={el.get('to')} rot={el.get('rotation')}")
        for f, fd in el.get('faces', {}).items():
            print(f"   {f}: uv={fd.get('uv')} rot={fd.get('rotation', 0)} tex={fd.get('texture')}")
