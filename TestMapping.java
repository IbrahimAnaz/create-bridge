import com.viaversion.viabackwards.protocol.v1_21_2to1_21.Protocol1_21_2To1_21;

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
