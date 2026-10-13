
import org.objectweb.asm.*;
import java.io.File;
import java.nio.file.Files;

public class TestPatch {
    public static void main(String[] args) throws Exception {
        byte[] bytes = Files.readAllBytes(new File("tools/staging/MappingDataBase.class").toPath());
        ClassReader cr = new ClassReader(bytes);
        ClassWriter cw = new ClassWriter(ClassWriter.COMPUTE_MAXS | ClassWriter.COMPUTE_FRAMES);
        ClassVisitor cv = new ClassVisitor(Opcodes.ASM9, cw) {
            @Override
            public MethodVisitor visitMethod(int access, String name, String descriptor, String signature, String[] exceptions) {
                MethodVisitor targetMv = super.visitMethod(access, name, descriptor, signature, exceptions);
                if ("checkValidity".equals(name) && "(IILjava/lang/String;)I".equals(descriptor)) {
                    targetMv.visitCode();
                    Label notUnmapped = new Label();
                    Label checkBlock = new Label();
                    Label checkItem = new Label();
                    Label defaultReturn = new Label();

                    targetMv.visitVarInsn(Opcodes.ILOAD, 2);
                    targetMv.visitInsn(Opcodes.ICONST_M1);
                    targetMv.visitJumpInsn(Opcodes.IF_ICMPNE, notUnmapped);

                    // BLOCKSTATE
                    targetMv.visitLdcInsn("blockstate");
                    targetMv.visitVarInsn(Opcodes.ALOAD, 3);
                    targetMv.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "java/lang/String", "equals", "(Ljava/lang/Object;)Z", false);
                    targetMv.visitJumpInsn(Opcodes.IFEQ, checkBlock);

                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(100000);
                    Label notShiftedState = new Label();
                    targetMv.visitJumpInsn(Opcodes.IF_ICMPLT, notShiftedState);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    targetMv.visitLabel(notShiftedState);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(25000);
                    targetMv.visitJumpInsn(Opcodes.IF_ICMPLT, defaultReturn);
                    targetMv.visitLdcInsn(100000);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitInsn(Opcodes.IADD);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    // BLOCK
                    targetMv.visitLabel(checkBlock);
                    targetMv.visitLdcInsn("block");
                    targetMv.visitVarInsn(Opcodes.ALOAD, 3);
                    targetMv.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "java/lang/String", "equals", "(Ljava/lang/Object;)Z", false);
                    targetMv.visitJumpInsn(Opcodes.IFEQ, checkItem);

                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(100000);
                    Label notShiftedBlock = new Label();
                    targetMv.visitJumpInsn(Opcodes.IF_ICMPLT, notShiftedBlock);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    targetMv.visitLabel(notShiftedBlock);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(1000);
                    targetMv.visitJumpInsn(Opcodes.IF_ICMPLT, defaultReturn);
                    targetMv.visitLdcInsn(100000);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitInsn(Opcodes.IADD);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    // ITEM
                    targetMv.visitLabel(checkItem);
                    targetMv.visitLdcInsn("item");
                    targetMv.visitVarInsn(Opcodes.ALOAD, 3);
                    targetMv.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "java/lang/String", "equals", "(Ljava/lang/Object;)Z", false);
                    targetMv.visitJumpInsn(Opcodes.IFEQ, defaultReturn);

                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(10000);
                    Label notShiftedItem = new Label();
                    targetMv.visitJumpInsn(Opcodes.IF_ICMPLT, notShiftedItem);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    targetMv.visitLabel(notShiftedItem);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitLdcInsn(1000);
                    targetMv.visitJumpInsn(Opcodes.IF_ICMPLT, defaultReturn);
                    targetMv.visitLdcInsn(10000);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitInsn(Opcodes.IADD);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    targetMv.visitLabel(defaultReturn);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 1);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    targetMv.visitLabel(notUnmapped);
                    targetMv.visitVarInsn(Opcodes.ILOAD, 2);
                    targetMv.visitInsn(Opcodes.IRETURN);

                    targetMv.visitMaxs(0, 0);
                    targetMv.visitEnd();
                    return null;
                }
                return targetMv;
            }
        };
        cr.accept(cv, ClassReader.SKIP_FRAMES);
        Files.write(new File("tools/staging/TestMappingDataBase.class").toPath(), cw.toByteArray());
        System.out.println("SUCCESS!");
    }
}
