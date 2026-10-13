import org.objectweb.asm.*;
import java.io.File;
import java.nio.file.Files;

public class PatchViaProxyItems {
    public static void main(String[] args) throws Exception {
        patchMappingDataBase();
        patchBackwardsMappingData();
        System.out.println("ALL PATCHES APPLIED SUCCESSFULLY!");
    }

    private static void patchMappingDataBase() throws Exception {
        byte[] bytes = Files.readAllBytes(new File("tools/staging/MappingDataBase.class").toPath());
        ClassReader cr = new ClassReader(bytes);
        ClassWriter cw = new ClassWriter(ClassWriter.COMPUTE_MAXS | ClassWriter.COMPUTE_FRAMES);
        ClassVisitor cv = new ClassVisitor(Opcodes.ASM9, cw) {
            @Override
            public MethodVisitor visitMethod(int access, String name, String descriptor, String signature, String[] exceptions) {
                MethodVisitor targetMv = super.visitMethod(access, name, descriptor, signature, exceptions);

                // --- getNewItemId(int id) ---
                if ("getNewItemId".equals(name) && "(I)I".equals(descriptor)) {
                    targetMv.visitCode();
                    Label checkCreate = new Label();
                    Label callVanilla = new Label();

                    // if (id >= 10000) return id;
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(10000);
                    targetMv.visitJumpInsn(Opcodes.IF_ICMPLT, checkCreate);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    // checkCreate: if (id >= 1333) return 10000 + id;
                    targetMv.visitLabel(checkCreate);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(1333);
                    targetMv.visitJumpInsn(Opcodes.IF_ICMPLT, callVanilla);
                    targetMv.visitLdcInsn(10000);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitInsn(Opcodes.IADD);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    // callVanilla: return checkValidity(id, itemMappings.getNewId(id), "item");
                    targetMv.visitLabel(callVanilla);
                    targetMv.visitVarInsn(Opcodes.ALOAD, 0);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitVarInsn(Opcodes.ALOAD, 0);
                    targetMv.visitFieldInsn(Opcodes.GETFIELD, "com/viaversion/viaversion/api/data/MappingDataBase", "itemMappings", "Lcom/viaversion/viaversion/api/data/BiMappings;");
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "com/viaversion/viaversion/api/data/BiMappings", "getNewId", "(I)I", true);
                    targetMv.visitLdcInsn("item");
                    targetMv.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "com/viaversion/viaversion/api/data/MappingDataBase", "checkValidity", "(IILjava/lang/String;)I", false);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    targetMv.visitMaxs(0, 0);
                    targetMv.visitEnd();
                    return null;
                }

                // --- getOldItemId(int id) ---
                if ("getOldItemId".equals(name) && "(I)I".equals(descriptor)) {
                    targetMv.visitCode();
                    Label checkCreate = new Label();
                    Label callVanilla = new Label();

                    // if (id >= 10000) return id - 10000;
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(10000);
                    targetMv.visitJumpInsn(Opcodes.IF_ICMPLT, callVanilla);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(10000);
                    targetMv.visitInsn(Opcodes.ISUB);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    // callVanilla: return itemMappings.inverse().getNewIdOrDefault(id, id);
                    targetMv.visitLabel(callVanilla);
                    targetMv.visitVarInsn(Opcodes.ALOAD, 0);
                    targetMv.visitFieldInsn(Opcodes.GETFIELD, "com/viaversion/viaversion/api/data/MappingDataBase", "itemMappings", "Lcom/viaversion/viaversion/api/data/BiMappings;");
                    targetMv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "com/viaversion/viaversion/api/data/BiMappings", "inverse", "()Lcom/viaversion/viaversion/api/data/BiMappings;", true);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "com/viaversion/viaversion/api/data/BiMappings", "getNewIdOrDefault", "(II)I", true);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    targetMv.visitMaxs(0, 0);
                    targetMv.visitEnd();
                    return null;
                }

                // --- getNewBlockStateId(int id) ---
                if ("getNewBlockStateId".equals(name) && "(I)I".equals(descriptor)) {
                    targetMv.visitCode();
                    Label checkCreate = new Label();
                    Label callVanilla = new Label();

                    // if (id >= 100000) return id;
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(100000);
                    targetMv.visitJumpInsn(Opcodes.IF_ICMPLT, checkCreate);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    // checkCreate: if (id >= 26684) return 100000 + id;
                    targetMv.visitLabel(checkCreate);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(26684);
                    targetMv.visitJumpInsn(Opcodes.IF_ICMPLT, callVanilla);
                    targetMv.visitLdcInsn(100000);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitInsn(Opcodes.IADD);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    // callVanilla: return checkValidity(id, blockStateMappings.getNewId(id), "blockstate");
                    targetMv.visitLabel(callVanilla);
                    targetMv.visitVarInsn(Opcodes.ALOAD, 0);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitVarInsn(Opcodes.ALOAD, 0);
                    targetMv.visitFieldInsn(Opcodes.GETFIELD, "com/viaversion/viaversion/api/data/MappingDataBase", "blockStateMappings", "Lcom/viaversion/viaversion/api/data/Mappings;");
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "com/viaversion/viaversion/api/data/Mappings", "getNewId", "(I)I", true);
                    targetMv.visitLdcInsn("blockstate");
                    targetMv.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "com/viaversion/viaversion/api/data/MappingDataBase", "checkValidity", "(IILjava/lang/String;)I", false);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    targetMv.visitMaxs(0, 0);
                    targetMv.visitEnd();
                    return null;
                }

                // --- getNewBlockId(int id) ---
                if ("getNewBlockId".equals(name) && "(I)I".equals(descriptor)) {
                    targetMv.visitCode();
                    Label checkCreate = new Label();
                    Label callVanilla = new Label();

                    // if (id >= 100000) return id;
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(100000);
                    targetMv.visitJumpInsn(Opcodes.IF_ICMPLT, checkCreate);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    // checkCreate: if (id >= 1060) return 100000 + id;
                    targetMv.visitLabel(checkCreate);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(1060);
                    targetMv.visitJumpInsn(Opcodes.IF_ICMPLT, callVanilla);
                    targetMv.visitLdcInsn(100000);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitInsn(Opcodes.IADD);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    // callVanilla: return checkValidity(id, blockMappings.getNewId(id), "block");
                    targetMv.visitLabel(callVanilla);
                    targetMv.visitVarInsn(Opcodes.ALOAD, 0);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitVarInsn(Opcodes.ALOAD, 0);
                    targetMv.visitFieldInsn(Opcodes.GETFIELD, "com/viaversion/viaversion/api/data/MappingDataBase", "blockMappings", "Lcom/viaversion/viaversion/api/data/BiMappings;");
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "com/viaversion/viaversion/api/data/BiMappings", "getNewId", "(I)I", true);
                    targetMv.visitLdcInsn("block");
                    targetMv.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "com/viaversion/viaversion/api/data/MappingDataBase", "checkValidity", "(IILjava/lang/String;)I", false);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    targetMv.visitMaxs(0, 0);
                    targetMv.visitEnd();
                    return null;
                }

                // --- getOldBlockId(int id) ---
                if ("getOldBlockId".equals(name) && "(I)I".equals(descriptor)) {
                    targetMv.visitCode();
                    Label callVanilla = new Label();

                    // if (id >= 100000) return id - 100000;
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(100000);
                    targetMv.visitJumpInsn(Opcodes.IF_ICMPLT, callVanilla);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(100000);
                    targetMv.visitInsn(Opcodes.ISUB);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    // callVanilla: return blockMappings.inverse().getNewIdOrDefault(id, id);
                    targetMv.visitLabel(callVanilla);
                    targetMv.visitVarInsn(Opcodes.ALOAD, 0);
                    targetMv.visitFieldInsn(Opcodes.GETFIELD, "com/viaversion/viaversion/api/data/MappingDataBase", "blockMappings", "Lcom/viaversion/viaversion/api/data/BiMappings;");
                    targetMv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "com/viaversion/viaversion/api/data/BiMappings", "inverse", "()Lcom/viaversion/viaversion/api/data/BiMappings;", true);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitMethodInsn(Opcodes.INVOKEINTERFACE, "com/viaversion/viaversion/api/data/BiMappings", "getNewIdOrDefault", "(II)I", true);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    targetMv.visitMaxs(0, 0);
                    targetMv.visitEnd();
                    return null;
                }

                return targetMv;
            }
        };
        cr.accept(cv, ClassReader.SKIP_FRAMES);
        Files.write(new File("tools/staging/MappingDataBase_patched.class").toPath(), cw.toByteArray());
        System.out.println("Patched MappingDataBase.class successfully with ID Firewall!");
    }

    private static void patchBackwardsMappingData() throws Exception {
        byte[] bytes = Files.readAllBytes(new File("tools/staging/BackwardsMappingData.class").toPath());
        ClassReader cr = new ClassReader(bytes);
        ClassWriter cw = new ClassWriter(ClassWriter.COMPUTE_MAXS | ClassWriter.COMPUTE_FRAMES);
        ClassVisitor cv = new ClassVisitor(Opcodes.ASM9, cw) {
            @Override
            public MethodVisitor visitMethod(int access, String name, String descriptor, String signature, String[] exceptions) {
                MethodVisitor targetMv = super.visitMethod(access, name, descriptor, signature, exceptions);

                if ("getNewItemId".equals(name) && "(I)I".equals(descriptor)) {
                    targetMv.visitCode();
                    Label checkCreate = new Label();
                    Label callSuper = new Label();

                    // if (id >= 10000) return id;
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(10000);
                    targetMv.visitJumpInsn(Opcodes.IF_ICMPLT, checkCreate);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    // checkCreate: if (id >= 1333) return 10000 + id;
                    targetMv.visitLabel(checkCreate);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(1333);
                    targetMv.visitJumpInsn(Opcodes.IF_ICMPLT, callSuper);
                    targetMv.visitLdcInsn(10000);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitInsn(Opcodes.IADD);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    // callSuper
                    targetMv.visitLabel(callSuper);
                    targetMv.visitVarInsn(Opcodes.ALOAD, 0);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitMethodInsn(Opcodes.INVOKESPECIAL, "com/viaversion/viaversion/api/data/MappingDataBase", "getNewItemId", "(I)I", false);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    targetMv.visitMaxs(0, 0);
                    targetMv.visitEnd();
                    return null;
                }

                if ("getOldItemId".equals(name) && "(I)I".equals(descriptor)) {
                    targetMv.visitCode();
                    Label callSuper = new Label();

                    // if (id >= 10000) return id - 10000;
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(10000);
                    targetMv.visitJumpInsn(Opcodes.IF_ICMPLT, callSuper);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(10000);
                    targetMv.visitInsn(Opcodes.ISUB);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    // callSuper
                    targetMv.visitLabel(callSuper);
                    targetMv.visitVarInsn(Opcodes.ALOAD, 0);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitMethodInsn(Opcodes.INVOKESPECIAL, "com/viaversion/viaversion/api/data/MappingDataBase", "getOldItemId", "(I)I", false);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    targetMv.visitMaxs(0, 0);
                    targetMv.visitEnd();
                    return null;
                }

                if ("getNewBlockId".equals(name) && "(I)I".equals(descriptor)) {
                    targetMv.visitCode();
                    Label checkCreate = new Label();
                    Label callSuper = new Label();

                    // if (id >= 100000) return id;
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(100000);
                    targetMv.visitJumpInsn(Opcodes.IF_ICMPLT, checkCreate);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    // checkCreate: if (id >= 26684) return 100000 + id;
                    targetMv.visitLabel(checkCreate);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(26684);
                    targetMv.visitJumpInsn(Opcodes.IF_ICMPLT, callSuper);
                    targetMv.visitLdcInsn(100000);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitInsn(Opcodes.IADD);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    // callSuper
                    targetMv.visitLabel(callSuper);
                    targetMv.visitVarInsn(Opcodes.ALOAD, 0);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitMethodInsn(Opcodes.INVOKESPECIAL, "com/viaversion/viaversion/api/data/MappingDataBase", "getNewBlockId", "(I)I", false);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    targetMv.visitMaxs(0, 0);
                    targetMv.visitEnd();
                    return null;
                }

                if ("getOldBlockId".equals(name) && "(I)I".equals(descriptor)) {
                    targetMv.visitCode();
                    Label callSuper = new Label();

                    // if (id >= 100000) return id - 100000;
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(100000);
                    targetMv.visitJumpInsn(Opcodes.IF_ICMPLT, callSuper);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(100000);
                    targetMv.visitInsn(Opcodes.ISUB);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    // callSuper
                    targetMv.visitLabel(callSuper);
                    targetMv.visitVarInsn(Opcodes.ALOAD, 0);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitMethodInsn(Opcodes.INVOKESPECIAL, "com/viaversion/viaversion/api/data/MappingDataBase", "getOldBlockId", "(I)I", false);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    targetMv.visitMaxs(0, 0);
                    targetMv.visitEnd();
                    return null;
                }

                return targetMv;
            }
        };
        cr.accept(cv, ClassReader.SKIP_FRAMES);
        Files.write(new File("tools/staging/BackwardsMappingData_patched.class").toPath(), cw.toByteArray());
        System.out.println("Patched BackwardsMappingData.class successfully with ID Firewall!");
    }
}
