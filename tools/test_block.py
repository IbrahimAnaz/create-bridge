import subprocess

code = """
public class TestBlock {
    public static void main(String[] args) {
        org.geysermc.geyser.level.block.type.BlockState state = org.geysermc.geyser.level.block.type.BlockState.of(20840);
        System.out.println("BlockState 20840: " + state.toString());
        System.out.println("Block: " + state.block().toString());
    }
}
"""
with open("TestBlock.java", "w") as f:
    f.write(code)

subprocess.run(["javac", "-cp", "portable_bridge/geyser/Geyser-Standalone.jar", "TestBlock.java"], check=True)
res = subprocess.run(["java", "-cp", ".;portable_bridge/geyser/Geyser-Standalone.jar", "TestBlock"], capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
