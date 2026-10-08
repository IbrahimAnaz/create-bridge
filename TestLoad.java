import java.io.File;
import java.nio.file.Files;
import java.lang.reflect.Method;

public class TestLoad {
    public static void main(String[] args) throws Exception {
        byte[] bytes = Files.readAllBytes(new File("MappingDataBase_patched.class").toPath());
        Method m = ClassLoader.class.getDeclaredMethod("defineClass", String.class, byte[].class, int.class, int.class);
        m.setAccessible(true);
        Class<?> clazz = (Class<?>) m.invoke(ClassLoader.getSystemClassLoader(), "com.viaversion.viaversion.api.data.MappingDataBase", bytes, 0, bytes.length);
        System.out.println("SUCCESS: Class defined: " + clazz.getName());
    }
}
