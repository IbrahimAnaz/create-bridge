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
    return pid, stream.read()

def main():
    s = socket.create_connection(('127.0.0.1', 25565), timeout=10)
    print("Connected to NeoForge 25565")

    # 1. Handshake to Configuration (767 = 1.21.1, next_state = 2 for login)
    host = b'127.0.0.1'
    data = write_varint(767) + write_varint(len(host)) + host + struct.pack('>H', 25565) + write_varint(2)
    send_packet(s, 0x00, data)

    # 2. Login Start (name: ProbeBot, UUID: nil)
    name = b'ProbeBot'
    login_data = write_varint(len(name)) + name + (b'\x00' * 16)
    send_packet(s, 0x00, login_data)

    state = "LOGIN"
    while True:
        pid, payload = read_packet(s)
        stream = io.BytesIO(payload)
        # print(f"[{state}] Packet 0x{pid:02x}, len {len(payload)}")

        if state == "LOGIN":
            if pid == 0x02: # Login Success
                print("[LOGIN] Login Success!")
                # Send Login Acknowledged -> switch to CONFIG
                send_packet(s, 0x03, b'')
                state = "CONFIG"
            elif pid == 0x00: # Disconnect
                print("[LOGIN] Disconnected:", payload)
                break
        elif state == "CONFIG":
            if pid == 0x03: # Finish Configuration
                print("[CONFIG] Finish Configuration received!")
                send_packet(s, 0x03, b'') # Acknowledge
                state = "PLAY"
                print("[PLAY] Switched to PLAY state, waiting for chunk (0, -3)...")
            elif pid == 0x07: # Known Packs
                # Send empty known packs response
                send_packet(s, 0x07, write_varint(0))
            elif pid == 0x01: # Cookie Request
                pass
            elif pid == 0x00: # Custom report / ping
                pass
        elif state == "PLAY":
            # Chunk data packet in 1.21.1 is 0x27 (LevelChunkWithLight)
            # Let's inspect packet IDs around 0x27 or parse chunk coordinates
            if len(payload) > 500:
                try:
                    cx = struct.unpack('>i', payload[:4])[0]
                    cz = struct.unpack('>i', payload[4:8])[0]
                    if cx == 0 and cz == -3:
                        print(f"FOUND TARGET CHUNK ({cx}, {cz}), payload size {len(payload)}!")
                        with open("chunk_0_-3.bin", "wb") as f:
                            f.write(payload)
                        print("Saved chunk_0_-3.bin!")
                        break
                except:
                    pass

    s.close()

if __name__ == '__main__':
    main()
