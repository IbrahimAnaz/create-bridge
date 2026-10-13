import http.server
import socketserver
import json
import os
import sys
import urllib.parse
import zipfile

PORT = 8088
RP_DIR = os.path.abspath("create_cogwheel_rp")
RESOURCES_DIR = os.path.abspath("portable_bridge/extension/resources")
JAR_PATH = os.path.abspath("headless_server/mods/create-1.21.1-6.0.8.jar")

class PackViewerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=RP_DIR, **kwargs)

    def do_GET(self):
        if self.path == "/" or self.path == "/viewer" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            with open(os.path.join(os.path.dirname(__file__), "pack_viewer.html"), "rb") as f:
                self.wfile.write(f.read())
            return

        if self.path.startswith("/api/blockstate"):
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            block_name = qs.get("name", [""])[0]

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            result = {"name": block_name, "variants": [], "multipart": []}
            if os.path.exists(JAR_PATH):
                try:
                    with zipfile.ZipFile(JAR_PATH, "r") as z:
                        bs_path = f"assets/create/blockstates/{block_name}.json"
                        if bs_path in z.namelist():
                            raw = json.loads(z.read(bs_path).decode("utf-8"))
                            if "variants" in raw:
                                for var_key, var_val in raw["variants"].items():
                                    props = {}
                                    if var_key:
                                        for part in var_key.split(","):
                                            if "=" in part:
                                                k, v = part.split("=", 1)
                                                props[k] = v
                                    val_list = var_val if isinstance(var_val, list) else [var_val]
                                    for v_item in val_list:
                                        result["variants"].append({
                                            "variant": var_key or "default",
                                            "properties": props,
                                            "model": v_item.get("model", ""),
                                            "x": v_item.get("x", 0),
                                            "y": v_item.get("y", 0),
                                            "uvlock": v_item.get("uvlock", False)
                                        })
                            if "multipart" in raw:
                                result["multipart"] = raw["multipart"]
                except Exception as e:
                    result["error"] = str(e)

            self.wfile.write(json.dumps(result).encode("utf-8"))
            return

        if self.path == "/api/blocks":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            # Load terrain_texture.json
            tt_path = os.path.join(RP_DIR, "textures", "terrain_texture.json")
            terrain_textures = {}
            if os.path.exists(tt_path):
                with open(tt_path, "r", encoding="utf-8") as f:
                    terrain_textures = json.load(f).get("texture_data", {})

            # Load geo_blocks.json
            geo_path = os.path.join(RESOURCES_DIR, "geo_blocks.json")
            geo_map = {}
            if os.path.exists(geo_path):
                with open(geo_path, "r", encoding="utf-8") as f:
                    geo_map = json.load(f)

            # Load registry dump
            dump_path = os.path.join(RESOURCES_DIR, "create_registry_dump.json")
            dump = {}
            if os.path.exists(dump_path):
                with open(dump_path, "r", encoding="utf-8") as f:
                    dump = json.load(f)

            blockstates = dump.get("blockstates", {})

            blocks = []
            for full_id, state_ids in blockstates.items():
                name = full_id.split(":")[-1]
                tex_key = "create_" + name
                tex_info = terrain_textures.get(tex_key, {})
                tex_path = tex_info.get("textures", "")
                if isinstance(tex_path, list):
                    tex_path = tex_path[0]
                if tex_path and not tex_path.endswith(".png"):
                    tex_path += ".png"

                geo_id = geo_map.get(name)
                geo_file = None
                if geo_id:
                    possible_file = os.path.join(RP_DIR, "models", "blocks", f"{name}.geo.json")
                    if os.path.exists(possible_file):
                        geo_file = f"models/blocks/{name}.geo.json"

                blocks.append({
                    "id": full_id,
                    "name": name,
                    "rawIds": state_ids,
                    "textureKey": tex_key,
                    "texturePath": tex_path,
                    "geoId": geo_id,
                    "geoFile": geo_file,
                    "isGeo": bool(geo_file)
                })

            blocks.sort(key=lambda b: (not b["isGeo"], b["name"]))
            self.wfile.write(json.dumps(blocks).encode("utf-8"))
            return

        super().do_GET()

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), PackViewerHandler) as httpd:
        print(f"[PackViewer] Server started at http://localhost:{PORT}")
        print(f"[PackViewer] Serving pack root: {RP_DIR}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("[PackViewer] Stopping server...")

if __name__ == "__main__":
    run_server()
