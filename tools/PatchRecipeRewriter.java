package tools;

import org.objectweb.asm.*;
import org.objectweb.asm.tree.*;

import java.io.*;
import java.nio.file.*;
import java.util.zip.*;

public class PatchRecipeRewriter {
    public static void main(String[] args) throws Exception {
        String jarPath = "headless_server/viaproxy/ViaProxy.jar";
        String entryName = "com/viaversion/viaversion/protocols/v1_21to1_21_2/rewriter/BlockItemPacketRewriter1_21_2.class";

        byte[] originalBytes;
        try (ZipFile zf = new ZipFile(jarPath)) {
            ZipEntry entry = zf.getEntry(entryName);
            try (InputStream is = zf.getInputStream(entry)) {
                originalBytes = is.readAllBytes();
            }
        }

        ClassReader cr = new ClassReader(originalBytes);
        ClassNode cn = new ClassNode();
        cr.accept(cn, 0);

        boolean patched = false;
        for (MethodNode mn : cn.methods) {
            if ("lambda$registerPackets$8".equals(mn.name)) {
                System.out.println("Found target method: " + mn.name + mn.desc);
                mn.instructions.clear();
                if (mn.tryCatchBlocks != null) {
                    mn.tryCatchBlocks.clear();
                }
                if (mn.localVariables != null) {
                    mn.localVariables.clear();
                }

                InsnList il = new InsnList();

                // 1. wrapper.user().put(new RecipeRewriter1_21_2(this.protocol));
                il.add(new VarInsnNode(Opcodes.ALOAD, 1));
                il.add(new MethodInsnNode(Opcodes.INVOKEINTERFACE,
                        "com/viaversion/viaversion/api/protocol/packet/PacketWrapper",
                        "user",
                        "()Lcom/viaversion/viaversion/api/connection/UserConnection;",
                        true));
                il.add(new TypeInsnNode(Opcodes.NEW, "com/viaversion/viaversion/protocols/v1_21to1_21_2/rewriter/RecipeRewriter1_21_2"));
                il.add(new InsnNode(Opcodes.DUP));
                il.add(new VarInsnNode(Opcodes.ALOAD, 0));
                il.add(new FieldInsnNode(Opcodes.GETFIELD,
                        "com/viaversion/viaversion/protocols/v1_21to1_21_2/rewriter/BlockItemPacketRewriter1_21_2",
                        "protocol",
                        "Lcom/viaversion/viaversion/api/protocol/Protocol;"));
                il.add(new MethodInsnNode(Opcodes.INVOKESPECIAL,
                        "com/viaversion/viaversion/protocols/v1_21to1_21_2/rewriter/RecipeRewriter1_21_2",
                        "<init>",
                        "(Lcom/viaversion/viaversion/api/protocol/Protocol;)V",
                        false));
                il.add(new MethodInsnNode(Opcodes.INVOKEINTERFACE,
                        "com/viaversion/viaversion/api/connection/UserConnection",
                        "put",
                        "(Lcom/viaversion/viaversion/api/connection/StorableObject;)V",
                        true));

                // 2. wrapper.clearPacket();
                il.add(new VarInsnNode(Opcodes.ALOAD, 1));
                il.add(new MethodInsnNode(Opcodes.INVOKEINTERFACE,
                        "com/viaversion/viaversion/api/protocol/packet/PacketWrapper",
                        "clearPacket",
                        "()V",
                        true));

                // 3. wrapper.write(Types.VAR_INT, Integer.valueOf(0));
                il.add(new VarInsnNode(Opcodes.ALOAD, 1));
                il.add(new FieldInsnNode(Opcodes.GETSTATIC,
                        "com/viaversion/viaversion/api/type/Types",
                        "VAR_INT",
                        "Lcom/viaversion/viaversion/api/type/types/VarIntType;"));
                il.add(new InsnNode(Opcodes.ICONST_0));
                il.add(new MethodInsnNode(Opcodes.INVOKESTATIC, "java/lang/Integer", "valueOf", "(I)Ljava/lang/Integer;", false));
                il.add(new MethodInsnNode(Opcodes.INVOKEINTERFACE,
                        "com/viaversion/viaversion/api/protocol/packet/PacketWrapper",
                        "write",
                        "(Lcom/viaversion/viaversion/api/type/Type;Ljava/lang/Object;)V",
                        true));

                // 4. wrapper.write(Types.VAR_INT, Integer.valueOf(0));
                il.add(new VarInsnNode(Opcodes.ALOAD, 1));
                il.add(new FieldInsnNode(Opcodes.GETSTATIC,
                        "com/viaversion/viaversion/api/type/Types",
                        "VAR_INT",
                        "Lcom/viaversion/viaversion/api/type/types/VarIntType;"));
                il.add(new InsnNode(Opcodes.ICONST_0));
                il.add(new MethodInsnNode(Opcodes.INVOKESTATIC, "java/lang/Integer", "valueOf", "(I)Ljava/lang/Integer;", false));
                il.add(new MethodInsnNode(Opcodes.INVOKEINTERFACE,
                        "com/viaversion/viaversion/api/protocol/packet/PacketWrapper",
                        "write",
                        "(Lcom/viaversion/viaversion/api/type/Type;Ljava/lang/Object;)V",
                        true));

                // 5. return;
                il.add(new InsnNode(Opcodes.RETURN));

                mn.instructions = il;
                patched = true;
                System.out.println("Patched lambda$registerPackets$8 to write clean empty recipes!");
                break;
            }
        }

        if (!patched) {
            throw new IllegalStateException("Could not find lambda$registerPackets$8!");
        }

        ClassWriter cw = new ClassWriter(ClassWriter.COMPUTE_FRAMES | ClassWriter.COMPUTE_MAXS) {
            @Override
            protected String getCommonSuperClass(String type1, String type2) {
                return "java/lang/Object";
            }
        };
        cn.accept(cw);
        byte[] patchedBytes = cw.toByteArray();

        Path outDir = Paths.get("tools/staging/com/viaversion/viaversion/protocols/v1_21to1_21_2/rewriter");
        Files.createDirectories(outDir);
        Path outFile = outDir.resolve("BlockItemPacketRewriter1_21_2.class");
        Files.write(outFile, patchedBytes);
        System.out.println("Written patched class to: " + outFile + " (" + patchedBytes.length + " bytes)");
    }
}
