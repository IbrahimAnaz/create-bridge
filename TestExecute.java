import java.lang.reflect.Method;
import java.io.File;
import java.nio.file.Files;

public class TestExecute {
    public static void main(String[] args) throws Exception {
        byte[] bytes = Files.readAllBytes(new File("MappingDataBase_patched.class").toPath());
        Method def = ClassLoader.class.getDeclaredMethod("defineClass", String.class, byte[].class, int.class, int.class);
        def.setAccessible(true);
        Class<?> clazz = (Class<?>) def.invoke(ClassLoader.getSystemClassLoader(), "com.viaversion.viaversion.api.data.MappingDataBase", bytes, 0, bytes.length);

        // Find checkValidity
        Method cv = clazz.getDeclaredMethod("checkValidity", int.class, int.class, String.class);
        cv.setAccessible(true);

        // Create an instance using sun.misc.Unsafe or objenesis
        sun.misc.Unsafe unsafe;
        java.lang.reflect.Field f = sun.misc.Unsafe.class.getDeclaredField("theUnsafe");
        f.setAccessible(true);
        unsafe = (sun.misc.Unsafe) f.get(null);
        Object obj = unsafe.allocateInstance(clazz);

        // Test with mappedId != -1
        int r1 = (int) cv.invoke(obj, 10, 42, "blockstate");
        System.out.println("Test mappedId != -1 (expected 42): " + r1);

        // Test with mappedId == -1, id = 32328
        int r2 = (int) cv.invoke(obj, 32328, -1, "blockstate");
        System.out.println("Test unmapped id 32328 (expected 132328): " + r2);

        // Test with mappedId == -1, id = 27289
        int r3 = (int) cv.invoke(obj, 27289, -1, "blockstate");
        System.out.println("Test unmapped id 27289 (expected 127289): " + r3);

        // Test with mappedId == -1, id = 500
        int r4 = (int) cv.invoke(obj, 500, -1, "item");
        System.out.println("Test unmapped id 500 (expected 500): " + r4);
    }
}
