package net.raphimc.netminecraft.packet.impl.login;

import io.netty.buffer.ByteBuf;
import net.raphimc.netminecraft.packet.Packet;
import net.raphimc.netminecraft.packet.PacketTypes;
import net.raphimc.netminecraft.util.UUIDAdapter;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public class S2CLoginGameProfilePacket implements Packet {

    public UUID uuid;
    public String name;
    public List<String[]> properties;
    public boolean strictErrorHandling;
    public UUID sessionId;

    public S2CLoginGameProfilePacket() {
    }

    public S2CLoginGameProfilePacket(UUID uuid, String name) {
        this.uuid = uuid;
        this.name = name;
    }

    public S2CLoginGameProfilePacket(UUID uuid, String name, List<String[]> properties) {
        this(uuid, name);
        this.properties = properties;
    }

    public S2CLoginGameProfilePacket(UUID uuid, String name, List<String[]> properties, boolean strictErrorHandling) {
        this(uuid, name, properties);
        this.strictErrorHandling = strictErrorHandling;
    }

    public S2CLoginGameProfilePacket(UUID uuid, String name, List<String[]> properties, boolean strictErrorHandling, UUID sessionId) {
        this(uuid, name, properties, strictErrorHandling);
        this.sessionId = sessionId;
    }

    @Override
    public void read(ByteBuf buf, int version) {
        if (version <= 4) {
            this.uuid = UUIDAdapter.fromString(PacketTypes.readString(buf, 36));
        } else if (version <= 578) {
            this.uuid = UUID.fromString(PacketTypes.readString(buf, 36));
        } else {
            this.uuid = PacketTypes.readUuid(buf);
        }

        this.name = PacketTypes.readString(buf, 16);

        if (version >= 759) {
            int propCount = PacketTypes.readVarInt(buf);
            this.properties = new ArrayList<>();
            for (int i = 0; i < propCount; i++) {
                String propName = PacketTypes.readString(buf, 32767);
                String propVal = PacketTypes.readString(buf, 32767);
                String propSig = null;
                if (buf.readBoolean()) {
                    propSig = PacketTypes.readString(buf, 32767);
                }
                this.properties.add(new String[]{propName, propVal, propSig});
            }
        }

        if (version >= 766 && version <= 767) {
            this.strictErrorHandling = buf.readBoolean();
        }

        if (version >= 776) {
            if (buf.readableBytes() >= 16) {
                this.sessionId = PacketTypes.readUuid(buf);
            } else {
                this.sessionId = UUID.randomUUID();
            }
        }
    }

    @Override
    public void write(ByteBuf buf, int version) {
        if (version <= 4) {
            PacketTypes.writeString(buf, this.uuid != null ? UUIDAdapter.fromUUID(this.uuid) : "");
        } else if (version <= 578) {
            PacketTypes.writeString(buf, this.uuid != null ? this.uuid.toString() : "");
        } else {
            PacketTypes.writeUuid(buf, this.uuid);
        }

        PacketTypes.writeString(buf, this.name);

        if (version >= 759) {
            PacketTypes.writeVarInt(buf, this.properties != null ? this.properties.size() : 0);
            if (this.properties != null) {
                for (String[] prop : this.properties) {
                    PacketTypes.writeString(buf, prop[0]);
                    PacketTypes.writeString(buf, prop[1]);
                    if (prop[2] != null) {
                        buf.writeBoolean(true);
                        PacketTypes.writeString(buf, prop[2]);
                    } else {
                        buf.writeBoolean(false);
                    }
                }
            }
        }

        if (version >= 766 && version <= 767) {
            buf.writeBoolean(this.strictErrorHandling);
        }

        if (version >= 776) {
            PacketTypes.writeUuid(buf, this.sessionId != null ? this.sessionId : UUID.randomUUID());
        }
    }
}
