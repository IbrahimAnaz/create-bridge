import com.viaversion.viaversion.api.data.MappingDataBase;

public class TestCasing {
    public static void main(String[] args) {
        MappingDataBase data = new MappingDataBase("1.21", "1.21.2");
        data.load();
        int casingId = 29091;
        System.out.println("getNewBlockStateId(" + casingId + ") -> " + data.getNewBlockStateId(casingId));
        System.out.println("blockStateMappings.getNewId(" + casingId + ") -> " + data.getBlockStateMappings().getNewId(casingId));
        System.out.println("blockStateMappings.size() -> " + data.getBlockStateMappings().size());
        System.out.println("blockStateMappings.mappedSize() -> " + data.getBlockStateMappings().mappedSize());
    }
}
