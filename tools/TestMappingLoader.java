import com.viaversion.nbt.tag.*;
import com.viaversion.viaversion.api.data.*;

public class TestMappingLoader {
    public static void main(String[] args) throws Exception {
        MappingDataBase data = new MappingDataBase("1.21", "1.21.2");
        data.load();
        System.out.println("Item mappings size: " + data.getItemMappings().size());
        System.out.println("Item mappings mappedSize: " + data.getItemMappings().mappedSize());
        for (int id : new int[]{1336, 1337, 1359, 1430}) {
            int newId = data.getNewItemId(id);
            int oldId = data.getOldItemId(newId);
            System.out.println("ID " + id + " -> newId: " + newId + " -> oldId: " + oldId);
        }
    }
}
