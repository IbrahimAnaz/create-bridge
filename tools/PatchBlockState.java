import org.objectweb.asm.*;
import java.io.File;
import java.nio.file.Files;

public class PatchBlockState {
    public static void main(String[] args) throws Exception {
        byte[] bytes = Files.readAllBytes(new File("tools/BlockState.class").toPath());
        ClassReader cr = new ClassReader(bytes);
        ClassWriter cw = new ClassWriter(cr, ClassWriter.COMPUTE_MAXS);
        ClassVisitor cv = new ClassVisitor(Opcodes.ASM7, cw) {
            @Override
            public MethodVisitor visitMethod(int access, String name, String descriptor, String signature, String[] exceptions) {
                MethodVisitor mv = super.visitMethod(access, name, descriptor, signature, exceptions);
                if ("of".equals(name) && "(I)Lorg/geysermc/geyser/level/block/type/BlockState;".equals(descriptor)) {
                    return new MethodVisitor(Opcodes.ASM7, mv) {
                        @Override
                        public void visitCode() {
                            super.visitCode();
                            Label l0 = new Label();
                            super.visitLabel(l0);
                            super.visitLineNumber(196, l0);
                            super.visitVarInsn(Opcodes.ILOAD, 0);
                            super.visitMethodInsn(Opcodes.INVOKESTATIC,
                                "org/geysermc/geyser/level/block/type/BlockStateHelper",
                                "of",
                                "(I)Lorg/geysermc/geyser/level/block/type/BlockState;",
                                false);
                            super.visitInsn(Opcodes.ARETURN);
                            super.visitMaxs(1, 1);
                            super.visitEnd();
                        }
                        @Override public void visitLineNumber(int line, Label start) {}
                        @Override public void visitLocalVariable(String name, String descriptor, String signature, Label start, Label end, int index) {}
                        @Override public void visitInsn(int opcode) {}

                        @Override public void visitVarInsn(int opcode, int var) {}
                        @Override public void visitFieldInsn(int opcode, String owner, String name, String descriptor) {}
                        @Override public void visitMethodInsn(int opcode, String owner, String name, String descriptor, boolean isInterface) {}
                        @Override public void visitTypeInsn(int opcode, String type) {}
                    };

                }
                return mv;
            }
        };
        cr.accept(cv, 0);
        Files.write(new File("tools/BlockState_patched.class").toPath(), cw.toByteArray());
        System.out.println("Successfully patched BlockState.class with ASM!");
    }
}
