import com.viaversion.nbt.io.NBTIO;
import com.viaversion.nbt.tag.*;
import java.io.InputStream;


public class DumpViaData {
    public static void main(String[] args) throws Exception {
        InputStream in = DumpViaData.class.getResourceAsStream("/assets/viaversion/data/identifiers-1.21.nbt");
        CompoundTag tag121 = NBTIO.read(in);

        System.out.println("tag121 keys: " + tag121.keySet());
        for (String k : tag121.keySet()) {
            Tag t = tag121.get(k);
            System.out.println("Key: " + k + " -> type: " + t.getClass().getSimpleName());
            if (t instanceof ListTag list) {
                System.out.println("  size: " + list.size() + ", first 5: ");
                for (int i = 0; i < Math.min(5, list.size()); i++) {
                    System.out.println("    " + i + ": " + list.get(i).getValue());
                }
            } else if (t instanceof CompoundTag comp) {
                System.out.println("  compound keys size: " + comp.size());
            }
        }
    }
}
