import os
import subprocess

cp = open('headless_server/compile_cp.txt', 'r', encoding='utf-8').read().strip()
test_src = """package test;
import net.neoforged.fml.common.Mod;
import org.spongepowered.asm.mixin.Mixin;
import com.simibubi.create.content.logistics.depot.DepotBehaviour;
@Mod("testmod")
public class TestMod {
    public TestMod() {
        System.out.println("TestMod init");
    }
}
"""
os.makedirs('headless_server/test_temp/src/test', exist_ok=True)
os.makedirs('headless_server/test_temp/bin', exist_ok=True)
with open('headless_server/test_temp/src/test/TestMod.java', 'w') as f:
    f.write(test_src)
cmd = [
    r"C:\Program Files\Java\jdk-21.0.12\bin\javac.exe",
    "-cp", cp,
    "-d", "headless_server/test_temp/bin",
    "headless_server/test_temp/src/test/TestMod.java"
]
res = subprocess.run(cmd, capture_output=True, text=True)
print('Return code:', res.returncode)
if res.stderr:
    print('Stderr:', res.stderr)
if res.stdout:
    print('Stdout:', res.stdout)
