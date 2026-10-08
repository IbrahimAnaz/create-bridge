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
        ClassWriter cw = new ClassWriter(cr, ClassWriter.COMPUTE_MAXS | ClassWriter.COMPUTE_FRAMES);
        ClassVisitor cv = new ClassVisitor(Opcodes.ASM9, cw) {
            @Override
            public MethodVisitor visitMethod(int access, String name, String descriptor, String signature, String[] exceptions) {
                MethodVisitor mv = super.visitMethod(access, name, descriptor, signature, exceptions);

                if ("checkValidity".equals(name) && "(IILjava/lang/String;)I".equals(descriptor)) {
                    return new MethodVisitor(Opcodes.ASM9, mv) {
                        @Override
                        public void visitCode() {
                            super.visitCode();
                            Label notUnmapped = new Label();
                            Label checkItem = new Label();
                            Label defaultReturn = new Label();

                            // if (mappedId != -1) goto notUnmapped
                            super.visitVarInsn(Opcodes.ILOAD, 2);
                            super.visitInsn(Opcodes.ICONST_M1);
                            super.visitJumpInsn(Opcodes.IF_ICMPNE, notUnmapped);

                            // if (!"blockstate".equals(type)) goto checkItem
                            super.visitLdcInsn("blockstate");
                            super.visitVarInsn(Opcodes.ALOAD, 3);
                            super.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "java/lang/String", "equals", "(Ljava/lang/Object;)Z", false);
                            super.visitJumpInsn(Opcodes.IFEQ, checkItem);

                            // if (id >= 100000) return id;
                            super.visitVarInsn(Opcodes.ILOAD, 1);
                            super.visitLdcInsn(100000);
                            Label notAlreadyShiftedBlock = new Label();
                            super.visitJumpInsn(Opcodes.IF_ICMPLT, notAlreadyShiftedBlock);
                            super.visitVarInsn(Opcodes.ILOAD, 1);
                            super.visitInsn(Opcodes.IRETURN);

                            // notAlreadyShiftedBlock: if (id >= 25000) return 100000 + id;
                            super.visitLabel(notAlreadyShiftedBlock);
                            super.visitVarInsn(Opcodes.ILOAD, 1);
                            super.visitLdcInsn(25000);
                            super.visitJumpInsn(Opcodes.IF_ICMPLT, defaultReturn);
                            super.visitLdcInsn(100000);
                            super.visitVarInsn(Opcodes.ILOAD, 1);
                            super.visitInsn(Opcodes.IADD);
                            super.visitInsn(Opcodes.IRETURN);

                            // checkItem: if (!"item".equals(type)) goto defaultReturn
                            super.visitLabel(checkItem);
                            super.visitLdcInsn("item");
                            super.visitVarInsn(Opcodes.ALOAD, 3);
                            super.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "java/lang/String", "equals", "(Ljava/lang/Object;)Z", false);
                            super.visitJumpInsn(Opcodes.IFEQ, defaultReturn);

                            // if (id >= 10000) return id;
                            super.visitVarInsn(Opcodes.ILOAD, 1);
                            super.visitLdcInsn(10000);
                            Label notAlreadyShiftedItem = new Label();
                            super.visitJumpInsn(Opcodes.IF_ICMPLT, notAlreadyShiftedItem);
                            super.visitVarInsn(Opcodes.ILOAD, 1);
                            super.visitInsn(Opcodes.IRETURN);

                            // notAlreadyShiftedItem: if (id >= 1000) return 10000 + id;
                            super.visitLabel(notAlreadyShiftedItem);
                            super.visitVarInsn(Opcodes.ILOAD, 1);
                            super.visitLdcInsn(1000);
                            super.visitJumpInsn(Opcodes.IF_ICMPLT, defaultReturn);
                            super.visitLdcInsn(10000);
                            super.visitVarInsn(Opcodes.ILOAD, 1);
                            super.visitInsn(Opcodes.IADD);
                            super.visitInsn(Opcodes.IRETURN);

                            // defaultReturn: return id;
                            super.visitLabel(defaultReturn);
                            super.visitVarInsn(Opcodes.ILOAD, 1);
                            super.visitInsn(Opcodes.IRETURN);

                            // notUnmapped: return mappedId;
                            super.visitLabel(notUnmapped);
                            super.visitVarInsn(Opcodes.ILOAD, 2);
                            super.visitInsn(Opcodes.IRETURN);

                            super.visitMaxs(4, 4);
                            super.visitEnd();
                        }

                        @Override public void visitLineNumber(int line, Label start) {}
                        @Override public void visitLabel(Label label) {}
                        @Override public void visitLocalVariable(String n, String d, String s, Label st, Label e, int i) {}
                        @Override public void visitInsn(int op) {}
                        @Override public void visitVarInsn(int op, int v) {}
                        @Override public void visitFieldInsn(int op, String o, String n, String d) {}
                        @Override public void visitMethodInsn(int op, String o, String n, String d, boolean itf) {}
                        @Override public void visitLdcInsn(Object val) {}
                        @Override public void visitJumpInsn(int op, Label l) {}
                    };
                }

                if ("getOldItemId".equals(name) && "(I)I".equals(descriptor)) {
                    return new MethodVisitor(Opcodes.ASM9, mv) {
                        @Override
                        public void visitCode() {
                            super.visitCode();
                            Label notShifted = new Label();
                            super.visitVarInsn(Opcodes.ILOAD, 1);
                            super.visitLdcInsn(10000);
                            super.visitJumpInsn(Opcodes.IF_ICMPLT, notShifted);
                            super.visitVarInsn(Opcodes.ILOAD, 1);
                            super.visitLdcInsn(10000);
                            super.visitInsn(Opcodes.ISUB);
                            super.visitInsn(Opcodes.IRETURN);

                            super.visitLabel(notShifted);
                            super.visitVarInsn(Opcodes.ALOAD, 0);
                            super.visitFieldInsn(Opcodes.GETFIELD, "com/viaversion/viaversion/api/data/MappingDataBase", "itemMappings", "Lcom/viaversion/viaversion/api/data/BiMappings;");
                            super.visitMethodInsn(Opcodes.INVOKEINTERFACE, "com/viaversion/viaversion/api/data/BiMappings", "inverse", "()Lcom/viaversion/viaversion/api/data/BiMappings;", true);
                            super.visitVarInsn(Opcodes.ILOAD, 1);
                            super.visitVarInsn(Opcodes.ILOAD, 1);
                            super.visitMethodInsn(Opcodes.INVOKEINTERFACE, "com/viaversion/viaversion/api/data/BiMappings", "getNewIdOrDefault", "(II)I", true);
                            super.visitInsn(Opcodes.IRETURN);
                            super.visitMaxs(3, 2);
                            super.visitEnd();
                        }

                        @Override public void visitLineNumber(int line, Label start) {}
                        @Override public void visitLabel(Label label) {}
                        @Override public void visitLocalVariable(String n, String d, String s, Label st, Label e, int i) {}
                        @Override public void visitInsn(int op) {}
                        @Override public void visitVarInsn(int op, int v) {}
                        @Override public void visitFieldInsn(int op, String o, String n, String d) {}
                        @Override public void visitMethodInsn(int op, String o, String n, String d, boolean itf) {}
                        @Override public void visitLdcInsn(Object val) {}
                        @Override public void visitJumpInsn(int op, Label l) {}
                    };
                }

                if ("getOldBlockId".equals(name) && "(I)I".equals(descriptor)) {
                    return new MethodVisitor(Opcodes.ASM9, mv) {
                        @Override
                        public void visitCode() {
                            super.visitCode();
                            Label notShifted = new Label();
                            super.visitVarInsn(Opcodes.ILOAD, 1);
                            super.visitLdcInsn(100000);
                            super.visitJumpInsn(Opcodes.IF_ICMPLT, notShifted);
                            super.visitVarInsn(Opcodes.ILOAD, 1);
                            super.visitLdcInsn(100000);
                            super.visitInsn(Opcodes.ISUB);
                            super.visitInsn(Opcodes.IRETURN);

                            super.visitLabel(notShifted);
                            super.visitVarInsn(Opcodes.ALOAD, 0);
                            super.visitFieldInsn(Opcodes.GETFIELD, "com/viaversion/viaversion/api/data/MappingDataBase", "blockMappings", "Lcom/viaversion/viaversion/api/data/BiMappings;");
                            super.visitMethodInsn(Opcodes.INVOKEINTERFACE, "com/viaversion/viaversion/api/data/BiMappings", "inverse", "()Lcom/viaversion/viaversion/api/data/BiMappings;", true);
                            super.visitVarInsn(Opcodes.ILOAD, 1);
                            super.visitVarInsn(Opcodes.ILOAD, 1);
                            super.visitMethodInsn(Opcodes.INVOKEINTERFACE, "com/viaversion/viaversion/api/data/BiMappings", "getNewIdOrDefault", "(II)I", true);
                            super.visitInsn(Opcodes.IRETURN);
                            super.visitMaxs(3, 2);
                            super.visitEnd();
                        }

                        @Override public void visitLineNumber(int line, Label start) {}
                        @Override public void visitLabel(Label label) {}
                        @Override public void visitLocalVariable(String n, String d, String s, Label st, Label e, int i) {}
                        @Override public void visitInsn(int op) {}
                        @Override public void visitVarInsn(int op, int v) {}
                        @Override public void visitFieldInsn(int op, String o, String n, String d) {}
                        @Override public void visitMethodInsn(int op, String o, String n, String d, boolean itf) {}
                        @Override public void visitLdcInsn(Object val) {}
                        @Override public void visitJumpInsn(int op, Label l) {}
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
