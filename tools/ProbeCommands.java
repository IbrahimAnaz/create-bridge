package tools;

import org.geysermc.mcprotocollib.network.Session;
import org.geysermc.mcprotocollib.network.event.session.SessionAdapter;
import org.geysermc.mcprotocollib.network.packet.Packet;
import org.geysermc.mcprotocollib.network.session.ClientNetworkSession;
import org.geysermc.mcprotocollib.protocol.MinecraftProtocol;
import org.geysermc.mcprotocollib.protocol.data.game.command.CommandNode;
import org.geysermc.mcprotocollib.protocol.packet.ingame.clientbound.ClientboundCommandsPacket;

import java.net.InetSocketAddress;
import java.util.concurrent.ForkJoinPool;

public class ProbeCommands {
    public static void main(String[] args) throws Exception {
        System.out.println("[Probe] Connecting to ViaProxy (127.0.0.1:25568) as FickleMirror67...");
        MinecraftProtocol protocol = new MinecraftProtocol("FickleMirror67");
        ClientNetworkSession session = new ClientNetworkSession(
            new InetSocketAddress("127.0.0.1", 25568),
            protocol,
            ForkJoinPool.commonPool(),
            null,
            null
        );

        session.addListener(new SessionAdapter() {
            @Override
            public void packetReceived(Session s, Packet packet) {
                if (packet instanceof ClientboundCommandsPacket cmdPacket) {
                    System.out.println("=================================================");
                    System.out.println("[Probe] Received ClientboundCommandsPacket!");
                    CommandNode[] nodes = cmdPacket.getNodes();
                    System.out.println("  Total nodes: " + nodes.length);
                    int rootIndex = cmdPacket.getFirstNodeIndex();
                    System.out.println("  Root index: " + rootIndex);
                    CommandNode root = nodes[rootIndex];
                    System.out.println("  Root children count: " + root.getChildIndices().length);

                    for (int childIdx : root.getChildIndices()) {
                        CommandNode cmd = nodes[childIdx];
                        System.out.printf("  - Command: %-25s (type: %s, parser: %s, children: %d)%n",
                            cmd.getName(),
                            cmd.getType(),
                            cmd.getParser(),
                            cmd.getChildIndices().length
                        );
                    }
                    System.out.println("=================================================");
                    System.exit(0);
                }
            }
        });

        session.connect(true);
        Thread.sleep(10000);
        System.out.println("[Probe] Timed out waiting for commands packet.");
        System.exit(1);
    }
}
