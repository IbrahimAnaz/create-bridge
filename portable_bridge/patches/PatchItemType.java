package tools;

import org.objectweb.asm.*;
import org.objectweb.asm.tree.*;

import java.io.*;
import java.nio.file.*;
import java.util.*;

public class PatchItemType {
    public static void main(String[] args) throws Exception {
        byte[] originalBytes = Files.readAllBytes(Paths.get("tools/ItemType1_20_5.class"));
        ClassReader cr = new ClassReader(originalBytes);
        ClassNode cn = new ClassNode();
        cr.accept(cn, 0);

        for (MethodNode mn : cn.methods) {
            if ("readData".equals(mn.name)) {
                System.out.println("Found readData method, analyzing instructions...");

                // Find the two iinc 5, 1 instructions (loop continue points)
                List<IincInsnNode> iincs = new ArrayList<>();
                for (AbstractInsnNode insn : mn.instructions) {
                    if (insn instanceof IincInsnNode iinc && iinc.var == 5 && iinc.incr == 1) {
                        iincs.add(iinc);
                    }
                }
                System.out.println("Found iinc instructions: " + iincs.size());

                if (iincs.size() >= 2) {
                    IincInsnNode iinc1 = iincs.get(0);
                    IincInsnNode iinc2 = iincs.get(1);

                    // Create labels before iinc1 and iinc2
                    LabelNode lbl1 = new LabelNode();
                    LabelNode lbl2 = new LabelNode();
                    mn.instructions.insertBefore(iinc1, lbl1);
                    mn.instructions.insertBefore(iinc2, lbl2);

                    // Find astore 7 instructions
                    List<VarInsnNode> astores = new ArrayList<>();
                    for (AbstractInsnNode insn : mn.instructions) {
                        if (insn.getOpcode() == Opcodes.ASTORE && ((VarInsnNode) insn).var == 7) {
                            astores.add((VarInsnNode) insn);
                        }
                    }
                    System.out.println("Found astore 7 instructions: " + astores.size());

                    if (astores.size() >= 2) {
                        VarInsnNode astore1 = astores.get(0);
                        VarInsnNode astore2 = astores.get(1);

                        // After astore1 (key in slot 7):
                        // if key == null -> goto lbl1 (continue loop 1)
                        InsnList patch1 = new InsnList();
                        patch1.add(new VarInsnNode(Opcodes.ALOAD, 7));
                        patch1.add(new JumpInsnNode(Opcodes.IFNULL, lbl1));
                        mn.instructions.insert(astore1, patch1);

                        // After astore2 (key in slot 7):
                        // if key == null -> goto lbl2 (continue loop 2)
                        InsnList patch2 = new InsnList();
                        patch2.add(new VarInsnNode(Opcodes.ALOAD, 7));
                        patch2.add(new JumpInsnNode(Opcodes.IFNULL, lbl2));
                        mn.instructions.insert(astore2, patch2);

                        System.out.println("Successfully injected null-skip jumps into readData!");
                    }
                }
            }
        }

        // Write class with COMPUTE_FRAMES
        ClassWriter cw = new ClassWriter(ClassWriter.COMPUTE_FRAMES | ClassWriter.COMPUTE_MAXS) {
            @Override
            protected String getCommonSuperClass(String type1, String type2) {
                return "java/lang/Object";
            }
        };
        cn.accept(cw);
        byte[] patchedBytes = cw.toByteArray();
        Files.write(Paths.get("tools/ItemType1_20_5.class.patched"), patchedBytes);
        System.out.println("Patched class written to tools/ItemType1_20_5.class.patched (" + patchedBytes.length + " bytes)");
    }
}
