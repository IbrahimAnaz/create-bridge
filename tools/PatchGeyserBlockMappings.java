package tools;

import org.objectweb.asm.*;
import org.objectweb.asm.tree.*;

import java.io.File;
import java.nio.file.Files;

public class PatchGeyserBlockMappings {
    public static void main(String[] args) throws Exception {
        byte[] originalBytes = Files.readAllBytes(new File("tools/geyser_staging/BlockMappings.class").toPath());
        ClassReader cr = new ClassReader(originalBytes);
        ClassNode cn = new ClassNode();
        cr.accept(cn, 0);

        for (MethodNode mn : cn.methods) {
            if ("getBedrockBlock".equals(mn.name) && "(I)Lorg/geysermc/geyser/registry/type/GeyserBedrockBlock;".equals(mn.desc)) {
                System.out.println("Patching getBedrockBlock(int)...");
                for (AbstractInsnNode insn : mn.instructions.toArray()) {
                    if (insn.getOpcode() == Opcodes.ARETURN && insn.getPrevious().getOpcode() == Opcodes.AALOAD) {
                        InsnList patch = new InsnList();
                        LabelNode label = new LabelNode();
                        patch.add(new InsnNode(Opcodes.DUP));
                        patch.add(new JumpInsnNode(Opcodes.IFNONNULL, label));
                        patch.add(new InsnNode(Opcodes.POP));
                        patch.add(new VarInsnNode(Opcodes.ALOAD, 0));
                        patch.add(new FieldInsnNode(Opcodes.GETFIELD,
                            "org/geysermc/geyser/registry/type/BlockMappings",
                            "bedrockAir",
                            "Lorg/geysermc/geyser/registry/type/GeyserBedrockBlock;"));
                        patch.add(label);
                        mn.instructions.insertBefore(insn, patch);
                        System.out.println("Injected null-fallback in getBedrockBlock(int)!");
                        break;
                    }
                }
            }

            if ("getBedrockBlockId".equals(mn.name) && "(I)I".equals(mn.desc)) {
                System.out.println("Patching getBedrockBlockId(int)...");
                for (AbstractInsnNode insn : mn.instructions.toArray()) {
                    if (insn.getOpcode() == Opcodes.INVOKEVIRTUAL &&
                        ((MethodInsnNode) insn).name.equals("getRuntimeId")) {
                        InsnList patch = new InsnList();
                        LabelNode label = new LabelNode();
                        patch.add(new InsnNode(Opcodes.DUP));
                        patch.add(new JumpInsnNode(Opcodes.IFNONNULL, label));
                        patch.add(new InsnNode(Opcodes.POP));
                        patch.add(new VarInsnNode(Opcodes.ALOAD, 0));
                        patch.add(new FieldInsnNode(Opcodes.GETFIELD,
                            "org/geysermc/geyser/registry/type/BlockMappings",
                            "bedrockAir",
                            "Lorg/geysermc/geyser/registry/type/GeyserBedrockBlock;"));
                        patch.add(label);
                        mn.instructions.insertBefore(insn, patch);
                        System.out.println("Injected null-fallback in getBedrockBlockId(int)!");
                        break;
                    }
                }
            }
        }

        ClassWriter cw = new ClassWriter(ClassWriter.COMPUTE_MAXS | ClassWriter.COMPUTE_FRAMES) {
            @Override
            protected String getCommonSuperClass(String type1, String type2) {
                return "java/lang/Object";
            }
        };
        cn.accept(cw);
        byte[] patched = cw.toByteArray();
        Files.write(new File("tools/geyser_staging/BlockMappings_patched.class").toPath(), patched);
        System.out.println("Wrote patched BlockMappings_patched.class (" + patched.length + " bytes)!");
    }
}
