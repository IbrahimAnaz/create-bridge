import com.viaversion.viaversion.api.data.MappingDataBase;
import com.viaversion.viabackwards.api.data.BackwardsMappingData;

public class TestFwd {
    public static void main(String[] args) {
        MappingDataBase data = new MappingDataBase("1.21", "1.21.2");
        System.out.println("Item 1420 (saw) -> " + data.getNewItemId(1420));
        System.out.println("Item 1345 (clutch) -> " + data.getNewItemId(1345));
        System.out.println("Block 28863 (saw state) -> " + data.getNewBlockStateId(28863));
        System.out.println("Block 26764 (clutch state) -> " + data.getNewBlockStateId(26764));

        BackwardsMappingData back = new BackwardsMappingData("1.21.2", "1.21");
        System.out.println("Backwards Item 11420 (saw) -> " + back.getNewItemId(11420));
        System.out.println("Backwards Item 11345 (clutch) -> " + back.getNewItemId(11345));
        System.out.println("Backwards Item 1420 (raw saw from client) -> " + back.getNewItemId(1420));
    }
}
