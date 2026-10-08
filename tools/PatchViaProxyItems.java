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
        ClassWriter cw = new ClassWriter(cr, 0);
        ClassVisitor cv = new ClassVisitor(Opcodes.ASM9, cw) {
            @Override
            public MethodVisitor visitMethod(int access, String name, String descriptor, String signature, String[] exceptions) {
                MethodVisitor mv = super.visitMethod(access, name, descriptor, signature, exceptions);
                if (("getOldItemId".equals(name) || "getOldBlockId".equals(name)) && "(I)I".equals(descriptor)) {
                    return new MethodVisitor(Opcodes.ASM9, mv) {
                        @Override
                        public void visitInsn(int opcode) {
                            if (opcode == Opcodes.ICONST_1) {
                                // Replace iconst_1 with iload_1 (default to id instead of 1 [STONE])
                                super.visitVarInsn(Opcodes.ILOAD, 1);
                                return;
                            }
                            super.visitInsn(opcode);
                        }
                    };
                }
                return mv;
            }
        };
        cr.accept(cv, 0);
        Files.write(new File("tools/staging/MappingDataBase_patched.class").toPath(), cw.toByteArray());
        System.out.println("Patched MappingDataBase.class successfully!");
    }

    private static void patchBackwardsMappingData() throws Exception {
        byte[] bytes = Files.readAllBytes(new File("tools/staging/BackwardsMappingData.class").toPath());
        ClassReader cr = new ClassReader(bytes);
        ClassWriter cw = new ClassWriter(cr, ClassWriter.COMPUTE_MAXS | ClassWriter.COMPUTE_FRAMES);
        ClassVisitor cv = new ClassVisitor(Opcodes.ASM9, cw) {
            @Override
            public MethodVisitor visitMethod(int access, String name, String descriptor, String signature, String[] exceptions) {
                MethodVisitor mv = super.visitMethod(access, name, descriptor, signature, exceptions);
                if ("getNewItemId".equals(name) && "(I)I".equals(descriptor)) {
                    return new MethodVisitor(Opcodes.ASM9, mv) {
                        @Override
                        public void visitCode() {
                            super.visitCode();
                            // aload_0
                            super.visitVarInsn(Opcodes.ALOAD, 0);
                            // iload_1
                            super.visitVarInsn(Opcodes.ILOAD, 1);
                            // aload_0
                            super.visitVarInsn(Opcodes.ALOAD, 0);
                            // getfield itemMappings
                            super.visitFieldInsn(Opcodes.GETFIELD,
                                "com/viaversion/viabackwards/api/data/BackwardsMappingData",
                                "itemMappings",
                                "Lcom/viaversion/viaversion/api/data/BiMappings;");
                            // iload_1
                            super.visitVarInsn(Opcodes.ILOAD, 1);
                            // invokeinterface BiMappings.getNewId(I)I
                            super.visitMethodInsn(Opcodes.INVOKEINTERFACE,
                                "com/viaversion/viaversion/api/data/BiMappings",
                                "getNewId",
                                "(I)I",
                                true);
                            // ldc "item"
                            super.visitLdcInsn("item");
                            // invokevirtual checkValidity:(IILjava/lang/String;)I
                            super.visitMethodInsn(Opcodes.INVOKEVIRTUAL,
                                "com/viaversion/viabackwards/api/data/BackwardsMappingData",
                                "checkValidity",
                                "(IILjava/lang/String;)I",
                                false);
                            // ireturn
                            super.visitInsn(Opcodes.IRETURN);
                            super.visitMaxs(4, 2);
                            super.visitEnd();
                        }

                        // Ignore original instructions
                        @Override public void visitLineNumber(int line, Label start) {}
                        @Override public void visitLabel(Label label) {}
                        @Override public void visitLocalVariable(String name, String descriptor, String signature, Label start, Label end, int index) {}
                        @Override public void visitInsn(int opcode) {}
                        @Override public void visitVarInsn(int opcode, int var) {}
                        @Override public void visitFieldInsn(int opcode, String owner, String name, String desc) {}
                        @Override public void visitMethodInsn(int opcode, String owner, String name, String desc, boolean itf) {}
                        @Override public void visitLdcInsn(Object value) {}
                    };
                }

                if ("getNewBlockId".equals(name) && "(I)I".equals(descriptor)) {
                    return new MethodVisitor(Opcodes.ASM9, mv) {
                        @Override
                        public void visitCode() {
                            super.visitCode();
                            // aload_0
                            super.visitVarInsn(Opcodes.ALOAD, 0);
                            // iload_1
                            super.visitVarInsn(Opcodes.ILOAD, 1);
                            // aload_0
                            super.visitVarInsn(Opcodes.ALOAD, 0);
                            // getfield blockMappings
                            super.visitFieldInsn(Opcodes.GETFIELD,
                                "com/viaversion/viabackwards/api/data/BackwardsMappingData",
                                "blockMappings",
                                "Lcom/viaversion/viaversion/api/data/BiMappings;");
                            // iload_1
                            super.visitVarInsn(Opcodes.ILOAD, 1);
                            // invokeinterface BiMappings.getNewId(I)I
                            super.visitMethodInsn(Opcodes.INVOKEINTERFACE,
                                "com/viaversion/viaversion/api/data/BiMappings",
                                "getNewId",
                                "(I)I",
                                true);
                            // ldc "block"
                            super.visitLdcInsn("block");
                            // invokevirtual checkValidity:(IILjava/lang/String;)I
                            super.visitMethodInsn(Opcodes.INVOKEVIRTUAL,
                                "com/viaversion/viabackwards/api/data/BackwardsMappingData",
                                "checkValidity",
                                "(IILjava/lang/String;)I",
                                false);
                            // ireturn
                            super.visitInsn(Opcodes.IRETURN);
                            super.visitMaxs(4, 2);
                            super.visitEnd();
                        }

                        // Ignore original instructions
                        @Override public void visitLineNumber(int line, Label start) {}
                        @Override public void visitLabel(Label label) {}
                        @Override public void visitLocalVariable(String name, String descriptor, String signature, Label start, Label end, int index) {}
                        @Override public void visitInsn(int opcode) {}
                        @Override public void visitVarInsn(int opcode, int var) {}
                        @Override public void visitFieldInsn(int opcode, String owner, String name, String desc) {}
                        @Override public void visitMethodInsn(int opcode, String owner, String name, String desc, boolean itf) {}
                        @Override public void visitLdcInsn(Object value) {}
                    };
                }
                return mv;
            }
        };
        cr.accept(cv, 0);
        Files.write(new File("tools/staging/BackwardsMappingData_patched.class").toPath(), cw.toByteArray());
        System.out.println("Patched BackwardsMappingData.class successfully!");
    }
}
