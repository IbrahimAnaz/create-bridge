import subprocess

java_code = """import com.viaversion.viabackwards.protocol.v1_21_2to1_21.Protocol1_21_2To1_21;

public class TestMapping {
    public static void main(String[] args) {
        System.out.println("MAPPINGS: " + Protocol1_21_2To1_21.MAPPINGS);
        if (Protocol1_21_2To1_21.MAPPINGS != null) {
            System.out.println("item mappings: " + Protocol1_21_2To1_21.MAPPINGS.getItemMappings());
            try {
                System.out.println("getNewItemId(1680): " + Protocol1_21_2To1_21.MAPPINGS.getNewItemId(1680));
                System.out.println("getOldItemId(1680): " + Protocol1_21_2To1_21.MAPPINGS.getOldItemId(1680));
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }
}
"""

with open("TestMapping.java", "w") as f:
    f.write(java_code)

res = subprocess.run(["C:\\Program Files\\Java\\jdk-21.0.12\\bin\\javac.exe", "-cp", "headless_server/viaproxy/ViaProxy.jar", "TestMapping.java"], capture_output=True, text=True)
print("javac:", res.returncode, res.stderr)

res2 = subprocess.run(["java", "-cp", ".;headless_server/viaproxy/ViaProxy.jar", "TestMapping"], capture_output=True, text=True)
print("STDOUT:\n" + res2.stdout)
print("STDERR:\n" + res2.stderr)
