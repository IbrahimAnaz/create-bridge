import org.objectweb.asm.*;
import java.io.*;
import java.nio.file.*;

public class PatchDataComponentCodec {
    public static void main(String[] args) throws Exception {
        byte[] bytes = Files.readAllBytes(new File("real_dcp1.class").toPath());
        ClassReader cr = new ClassReader(bytes);
        ClassWriter cw = new ClassWriter(ClassWriter.COMPUTE_MAXS | ClassWriter.COMPUTE_FRAMES);

        ClassVisitor cv = new ClassVisitor(Opcodes.ASM9, cw) {
            @Override
            public MethodVisitor visitMethod(int access, String name, String descriptor, String signature, String[] exceptions) {
                // If it's the specific encode method, drop it! We will emit the replacement in visitEnd.
                if ("encode".equals(name) && "(Lnet/minecraft/network/RegistryFriendlyByteBuf;Lnet/minecraft/core/component/DataComponentPatch;)V".equals(descriptor)) {
                    return null;
                }
                return super.visitMethod(access, name, descriptor, signature, exceptions);
            }

            @Override
            public void visitEnd() {
                generateIsVanillaHelper(cw);
                generateFilteredEncode(cw);
                super.visitEnd();
            }
        };

        cr.accept(cv, ClassReader.EXPAND_FRAMES);
        byte[] patched = cw.toByteArray();
        Files.write(new File("real_dcp1_patched.class").toPath(), patched);
        System.out.println("PATCHED_SUCCESSFULLY! Bytes: " + patched.length);
    }

    private static void generateIsVanillaHelper(ClassWriter cw) {
        MethodVisitor mv = cw.visitMethod(Opcodes.ACC_PRIVATE | Opcodes.ACC_STATIC, "isVanilla", "(Lnet/minecraft/core/component/DataComponentType;)Z", null, null);
        mv.visitCode();
        Label notVanilla = new Label();

        // BuiltInRegistries.DATA_COMPONENT_TYPE.getKey(type)
        mv.visitFieldInsn(Opcodes.GETSTATIC, "net/minecraft/core/registries/BuiltInRegistries", "DATA_COMPONENT_TYPE", "Lnet/minecraft/core/Registry;");
        mv.visitVarInsn(Opcodes.ALOAD, 0);
        mv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "net/minecraft/core/Registry", "getKey", "(Ljava/lang/Object;)Lnet/minecraft/resources/ResourceLocation;", true);
        mv.visitInsn(Opcodes.DUP);
        mv.visitJumpInsn(Opcodes.IFNULL, notVanilla);

        // key.getNamespace().equals("minecraft")
        mv.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "net/minecraft/resources/ResourceLocation", "getNamespace", "()Ljava/lang/String;", false);
        mv.visitLdcInsn("minecraft");
        mv.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "java/lang/String", "equals", "(Ljava/lang/Object;)Z", false);
        mv.visitInsn(Opcodes.IRETURN);

        mv.visitLabel(notVanilla);
        mv.visitInsn(Opcodes.POP);
        mv.visitInsn(Opcodes.ICONST_0);
        mv.visitInsn(Opcodes.IRETURN);

        mv.visitMaxs(0, 0);
        mv.visitEnd();
    }

    private static void generateFilteredEncode(ClassWriter cw) {
        MethodVisitor mv = cw.visitMethod(Opcodes.ACC_PUBLIC, "encode", "(Lnet/minecraft/network/RegistryFriendlyByteBuf;Lnet/minecraft/core/component/DataComponentPatch;)V", null, null);
        mv.visitCode();

        Label endLabel = new Label();
        Label nonEmpty = new Label();

        // if (patch.isEmpty()) { buf.writeVarInt(0); buf.writeVarInt(0); return; }
        mv.visitVarInsn(Opcodes.ALOAD, 2);
        mv.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "net/minecraft/core/component/DataComponentPatch", "isEmpty", "()Z", false);
        mv.visitJumpInsn(Opcodes.IFEQ, nonEmpty);

        mv.visitVarInsn(Opcodes.ALOAD, 1);
        mv.visitInsn(Opcodes.ICONST_0);
        mv.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "net/minecraft/network/RegistryFriendlyByteBuf", "writeVarInt", "(I)Lnet/minecraft/network/FriendlyByteBuf;", false);
        mv.visitInsn(Opcodes.POP);

        mv.visitVarInsn(Opcodes.ALOAD, 1);
        mv.visitInsn(Opcodes.ICONST_0);
        mv.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "net/minecraft/network/RegistryFriendlyByteBuf", "writeVarInt", "(I)Lnet/minecraft/network/FriendlyByteBuf;", false);
        mv.visitInsn(Opcodes.POP);
        mv.visitJumpInsn(Opcodes.GOTO, endLabel);

        mv.visitLabel(nonEmpty);
        // int addedCount = 0; int removedCount = 0;
        mv.visitInsn(Opcodes.ICONST_0);
        mv.visitVarInsn(Opcodes.ISTORE, 3);
        mv.visitInsn(Opcodes.ICONST_0);
        mv.visitVarInsn(Opcodes.ISTORE, 4);

        // Iterator it = Reference2ObjectMaps.fastIterable(patch.map).iterator();
        mv.visitVarInsn(Opcodes.ALOAD, 2);
        mv.visitFieldInsn(Opcodes.GETFIELD, "net/minecraft/core/component/DataComponentPatch", "map", "Lit/unimi/dsi/fastutil/objects/Reference2ObjectMap;");
        mv.visitMethodInsn(Opcodes.INVOKESTATIC, "it/unimi/dsi/fastutil/objects/Reference2ObjectMaps", "fastIterable", "(Lit/unimi/dsi/fastutil/objects/Reference2ObjectMap;)Lit/unimi/dsi/fastutil/objects/ObjectIterable;", false);
        mv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "it/unimi/dsi/fastutil/objects/ObjectIterable", "iterator", "()Lit/unimi/dsi/fastutil/objects/ObjectIterator;", true);
        mv.visitVarInsn(Opcodes.ASTORE, 5);

        Label loop1Condition = new Label();
        Label loop1Start = new Label();

        mv.visitLabel(loop1Start);
        mv.visitVarInsn(Opcodes.ALOAD, 5);
        mv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "java/util/Iterator", "hasNext", "()Z", true);
        mv.visitJumpInsn(Opcodes.IFEQ, loop1Condition);

        mv.visitVarInsn(Opcodes.ALOAD, 5);
        mv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "java/util/Iterator", "next", "()Ljava/lang/Object;", true);
        mv.visitTypeInsn(Opcodes.CHECKCAST, "it/unimi/dsi/fastutil/objects/Reference2ObjectMap$Entry");
        mv.visitVarInsn(Opcodes.ASTORE, 6);

        // Check if key is vanilla
        mv.visitVarInsn(Opcodes.ALOAD, 6);
        mv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "it/unimi/dsi/fastutil/objects/Reference2ObjectMap$Entry", "getKey", "()Ljava/lang/Object;", true);
        mv.visitTypeInsn(Opcodes.CHECKCAST, "net/minecraft/core/component/DataComponentType");
        mv.visitMethodInsn(Opcodes.INVOKESTATIC, "net/minecraft/core/component/DataComponentPatch$1", "isVanilla", "(Lnet/minecraft/core/component/DataComponentType;)Z", false);
        mv.visitJumpInsn(Opcodes.IFEQ, loop1Start); // Skip non-vanilla!

        // if (entry.getValue().isPresent()) addedCount++; else removedCount++;
        mv.visitVarInsn(Opcodes.ALOAD, 6);
        mv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "it/unimi/dsi/fastutil/objects/Reference2ObjectMap$Entry", "getValue", "()Ljava/lang/Object;", true);
        mv.visitTypeInsn(Opcodes.CHECKCAST, "java/util/Optional");
        mv.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "java/util/Optional", "isPresent", "()Z", false);
        Label removedBranch = new Label();
        mv.visitJumpInsn(Opcodes.IFEQ, removedBranch);
        mv.visitIincInsn(3, 1);
        mv.visitJumpInsn(Opcodes.GOTO, loop1Start);

        mv.visitLabel(removedBranch);
        mv.visitIincInsn(4, 1);
        mv.visitJumpInsn(Opcodes.GOTO, loop1Start);

        mv.visitLabel(loop1Condition);
        // Write counts
        mv.visitVarInsn(Opcodes.ALOAD, 1);
        mv.visitVarInsn(Opcodes.ILOAD, 3);
        mv.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "net/minecraft/network/RegistryFriendlyByteBuf", "writeVarInt", "(I)Lnet/minecraft/network/FriendlyByteBuf;", false);
        mv.visitInsn(Opcodes.POP);

        mv.visitVarInsn(Opcodes.ALOAD, 1);
        mv.visitVarInsn(Opcodes.ILOAD, 4);
        mv.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "net/minecraft/network/RegistryFriendlyByteBuf", "writeVarInt", "(I)Lnet/minecraft/network/FriendlyByteBuf;", false);
        mv.visitInsn(Opcodes.POP);

        // Loop 2: Write added components
        mv.visitVarInsn(Opcodes.ALOAD, 2);
        mv.visitFieldInsn(Opcodes.GETFIELD, "net/minecraft/core/component/DataComponentPatch", "map", "Lit/unimi/dsi/fastutil/objects/Reference2ObjectMap;");
        mv.visitMethodInsn(Opcodes.INVOKESTATIC, "it/unimi/dsi/fastutil/objects/Reference2ObjectMaps", "fastIterable", "(Lit/unimi/dsi/fastutil/objects/Reference2ObjectMap;)Lit/unimi/dsi/fastutil/objects/ObjectIterable;", false);
        mv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "it/unimi/dsi/fastutil/objects/ObjectIterable", "iterator", "()Lit/unimi/dsi/fastutil/objects/ObjectIterator;", true);
        mv.visitVarInsn(Opcodes.ASTORE, 5);

        Label loop2Start = new Label();
        Label loop2End = new Label();

        mv.visitLabel(loop2Start);
        mv.visitVarInsn(Opcodes.ALOAD, 5);
        mv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "java/util/Iterator", "hasNext", "()Z", true);
        mv.visitJumpInsn(Opcodes.IFEQ, loop2End);

        mv.visitVarInsn(Opcodes.ALOAD, 5);
        mv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "java/util/Iterator", "next", "()Ljava/lang/Object;", true);
        mv.visitTypeInsn(Opcodes.CHECKCAST, "it/unimi/dsi/fastutil/objects/Reference2ObjectMap$Entry");
        mv.visitVarInsn(Opcodes.ASTORE, 6);

        mv.visitVarInsn(Opcodes.ALOAD, 6);
        mv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "it/unimi/dsi/fastutil/objects/Reference2ObjectMap$Entry", "getValue", "()Ljava/lang/Object;", true);
        mv.visitTypeInsn(Opcodes.CHECKCAST, "java/util/Optional");
        mv.visitVarInsn(Opcodes.ASTORE, 7);

        mv.visitVarInsn(Opcodes.ALOAD, 7);
        mv.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "java/util/Optional", "isPresent", "()Z", false);
        mv.visitJumpInsn(Opcodes.IFEQ, loop2Start);

        mv.visitVarInsn(Opcodes.ALOAD, 6);
        mv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "it/unimi/dsi/fastutil/objects/Reference2ObjectMap$Entry", "getKey", "()Ljava/lang/Object;", true);
        mv.visitTypeInsn(Opcodes.CHECKCAST, "net/minecraft/core/component/DataComponentType");
        mv.visitVarInsn(Opcodes.ASTORE, 8);

        mv.visitVarInsn(Opcodes.ALOAD, 8);
        mv.visitMethodInsn(Opcodes.INVOKESTATIC, "net/minecraft/core/component/DataComponentPatch$1", "isVanilla", "(Lnet/minecraft/core/component/DataComponentType;)Z", false);
        mv.visitJumpInsn(Opcodes.IFEQ, loop2Start); // Skip non-vanilla!

        // DataComponentType.STREAM_CODEC.encode(buffer, type);
        mv.visitFieldInsn(Opcodes.GETSTATIC, "net/minecraft/core/component/DataComponentType", "STREAM_CODEC", "Lnet/minecraft/network/codec/StreamCodec;");
        mv.visitVarInsn(Opcodes.ALOAD, 1);
        mv.visitVarInsn(Opcodes.ALOAD, 8);
        mv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "net/minecraft/network/codec/StreamCodec", "encode", "(Ljava/lang/Object;Ljava/lang/Object;)V", true);

        // encodeComponent(buffer, type, opt.get());
        mv.visitVarInsn(Opcodes.ALOAD, 1);
        mv.visitVarInsn(Opcodes.ALOAD, 8);
        mv.visitVarInsn(Opcodes.ALOAD, 7);
        mv.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "java/util/Optional", "get", "()Ljava/lang/Object;", false);
        mv.visitMethodInsn(Opcodes.INVOKESTATIC, "net/minecraft/core/component/DataComponentPatch$1", "encodeComponent", "(Lnet/minecraft/network/RegistryFriendlyByteBuf;Lnet/minecraft/core/component/DataComponentType;Ljava/lang/Object;)V", false);
        mv.visitJumpInsn(Opcodes.GOTO, loop2Start);

        mv.visitLabel(loop2End);

        // Loop 3: Write removed components
        mv.visitVarInsn(Opcodes.ALOAD, 2);
        mv.visitFieldInsn(Opcodes.GETFIELD, "net/minecraft/core/component/DataComponentPatch", "map", "Lit/unimi/dsi/fastutil/objects/Reference2ObjectMap;");
        mv.visitMethodInsn(Opcodes.INVOKESTATIC, "it/unimi/dsi/fastutil/objects/Reference2ObjectMaps", "fastIterable", "(Lit/unimi/dsi/fastutil/objects/Reference2ObjectMap;)Lit/unimi/dsi/fastutil/objects/ObjectIterable;", false);
        mv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "it/unimi/dsi/fastutil/objects/ObjectIterable", "iterator", "()Lit/unimi/dsi/fastutil/objects/ObjectIterator;", true);
        mv.visitVarInsn(Opcodes.ASTORE, 5);

        Label loop3Start = new Label();
        Label loop3End = new Label();

        mv.visitLabel(loop3Start);
        mv.visitVarInsn(Opcodes.ALOAD, 5);
        mv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "java/util/Iterator", "hasNext", "()Z", true);
        mv.visitJumpInsn(Opcodes.IFEQ, loop3End);

        mv.visitVarInsn(Opcodes.ALOAD, 5);
        mv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "java/util/Iterator", "next", "()Ljava/lang/Object;", true);
        mv.visitTypeInsn(Opcodes.CHECKCAST, "it/unimi/dsi/fastutil/objects/Reference2ObjectMap$Entry");
        mv.visitVarInsn(Opcodes.ASTORE, 6);

        mv.visitVarInsn(Opcodes.ALOAD, 6);
        mv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "it/unimi/dsi/fastutil/objects/Reference2ObjectMap$Entry", "getValue", "()Ljava/lang/Object;", true);
        mv.visitTypeInsn(Opcodes.CHECKCAST, "java/util/Optional");
        mv.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "java/util/Optional", "isEmpty", "()Z", false);
        mv.visitJumpInsn(Opcodes.IFEQ, loop3Start);

        mv.visitVarInsn(Opcodes.ALOAD, 6);
        mv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "it/unimi/dsi/fastutil/objects/Reference2ObjectMap$Entry", "getKey", "()Ljava/lang/Object;", true);
        mv.visitTypeInsn(Opcodes.CHECKCAST, "net/minecraft/core/component/DataComponentType");
        mv.visitVarInsn(Opcodes.ASTORE, 7);

        mv.visitVarInsn(Opcodes.ALOAD, 7);
        mv.visitMethodInsn(Opcodes.INVOKESTATIC, "net/minecraft/core/component/DataComponentPatch$1", "isVanilla", "(Lnet/minecraft/core/component/DataComponentType;)Z", false);
        mv.visitJumpInsn(Opcodes.IFEQ, loop3Start); // Skip non-vanilla!

        // DataComponentType.STREAM_CODEC.encode(buffer, type);
        mv.visitFieldInsn(Opcodes.GETSTATIC, "net/minecraft/core/component/DataComponentType", "STREAM_CODEC", "Lnet/minecraft/network/codec/StreamCodec;");
        mv.visitVarInsn(Opcodes.ALOAD, 1);
        mv.visitVarInsn(Opcodes.ALOAD, 7);
        mv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "net/minecraft/network/codec/StreamCodec", "encode", "(Ljava/lang/Object;Ljava/lang/Object;)V", true);
        mv.visitJumpInsn(Opcodes.GOTO, loop3Start);

        mv.visitLabel(loop3End);

        mv.visitLabel(endLabel);
        mv.visitInsn(Opcodes.RETURN);

        mv.visitMaxs(0, 0);
        mv.visitEnd();
    }
}
