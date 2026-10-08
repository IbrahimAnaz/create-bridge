import socket, struct, io

def write_varint(val):
    out = bytearray()
    while True:
        b = val & 0x7F
        val >>= 7
        if val != 0:
            out.append(b | 0x80)
        else:
            out.append(b)
            break
    return bytes(out)

def read_varint_from_stream(stream):
    res = 0
    shift = 0
    while True:
        b = stream.read(1)
        if not b:
            raise EOFError("Stream closed")
        b = b[0]
        res |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return res

def read_varint(s):
    res = 0
    shift = 0
    while True:
        b = s.recv(1)
        if not b:
            raise EOFError("Connection closed")
        b = b[0]
        res |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return res

def read_string(stream):
    length = read_varint_from_stream(stream)
    return stream.read(length).decode('utf-8', errors='ignore')

def send_packet(s, packet_id, data):
    payload = write_varint(packet_id) + data
    s.sendall(write_varint(len(payload)) + payload)

def read_packet(s):
    length = read_varint(s)
    data = bytearray()
    while len(data) < length:
        chunk = s.recv(length - len(data))
        if not chunk:
            raise EOFError("Premature EOF")
        data.extend(chunk)
    stream = io.BytesIO(data)
    pid = read_varint_from_stream(stream)
    return pid, stream


def main():
    s = socket.create_connection(('127.0.0.1', 25565), timeout=10)
    print("Connected to NeoForge 25565")

    # Handshake (767 = 1.21.1, next_state = 2 for login)
    host = b'127.0.0.1'
    data = write_varint(767) + write_varint(len(host)) + host + struct.pack('>H', 25565) + write_varint(2)
    send_packet(s, 0x00, data)

    # Login Start
    name = b'ItemProbeBot'
    login_data = write_varint(len(name)) + name + (b'\x00' * 16)
    send_packet(s, 0x00, login_data)

    state = "LOGIN"
    create_items = {}
    while True:
        pid, stream = read_packet(s)
        if state == "LOGIN":
            if pid == 0x02: # Login Success
                send_packet(s, 0x03, b'') # Login Acknowledged -> CONFIG
                state = "CONFIG"
            elif pid == 0x00:
                print("Disconnect:", stream.read())
                break
        elif state == "CONFIG":
            if pid == 0x07: # Known Packs
                send_packet(s, 0x07, write_varint(0))
            elif pid == 0x05: # Registry Data
                reg_id = read_string(stream)
                entry_count = read_varint_from_stream(stream)
                # print(f"Registry: {reg_id}, entries: {entry_count}")

                if reg_id == "minecraft:item":
                    print(f"Reading {entry_count} items from minecraft:item...")
                    for i in range(entry_count):
                        item_id_str = read_string(stream)
                        has_data = stream.read(1)[0]
                        if has_data:
                            # Skip NBT or data
                            # In 1.21.1, registry entry has optional NBT
                            # Let's read NBT tag
                            import nbtlib
                            pass
                        if "create" in item_id_str:
                            create_items[item_id_str] = i
                    print(f"Found {len(create_items)} Create items in registry!")
                    for k in sorted(create_items.keys()):
                        if any(c in k for c in ["casing", "cogwheel", "wrench", "depot", "chute"]):
                            print(f"  {k} -> ID {create_items[k]}")
                    break
            elif pid == 0x03: # Finish Configuration
                print("Finish configuration received before finding minecraft:item")
                break

    s.close()

if __name__ == "__main__":
    main()
