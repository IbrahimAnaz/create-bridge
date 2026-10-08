import subprocess

jdk = r"C:\Program Files\Java\jdk-21.0.12\bin"
javac = f"{jdk}\\javac.exe"
java = f"{jdk}\\java.exe"

code = """
import com.viaversion.viabackwards.protocol.v1_21_2to1_21.Protocol1_21_2To1_21;
import com.viaversion.viaversion.protocols.v1_21to1_21_2.Protocol1_21To1_21_2;
import com.viaversion.viaversion.api.data.MappingData;

public class TestDirectMappings {
    public static void main(String[] args) {
        System.out.println("Testing Backwards (1.21.2 to 1.21):");
        MappingData back = Protocol1_21_2To1_21.MAPPINGS;
        back.load();
        System.out.println("  32328 -> " + back.getNewBlockStateId(32328));
        System.out.println("  132328 -> " + back.getNewBlockStateId(132328));

        System.out.println("Testing Forward (1.21 to 1.21.2):");
        Protocol1_21To1_21_2 proto = new Protocol1_21To1_21_2();
        MappingData fwd = proto.getMappingData();
        if (fwd != null) {
            fwd.load();
            System.out.println("  fwd loaded, 32328 -> " + fwd.getNewBlockStateId(32328));
            System.out.println("  fwd 100 -> " + fwd.getNewBlockStateId(100));
        } else {
            System.out.println("  fwd mappingData is null");
        }
    }
}
"""

with open("tools/TestDirectMappings.java", "w") as f:
    f.write(code)

res = subprocess.run([javac, "-cp", "headless_server/viaproxy/ViaProxy.jar", "tools/TestDirectMappings.java"], capture_output=True, text=True)
print("javac returncode:", res.returncode)
if res.stderr:
    print("javac stderr:", res.stderr)
if res.returncode == 0:
    res2 = subprocess.run([java, "-cp", "tools;headless_server/viaproxy/ViaProxy.jar", "TestDirectMappings"], capture_output=True, text=True)
    print("java stdout:\n" + res2.stdout)
    if res2.stderr:
        print("java stderr:\n" + res2.stderr)
