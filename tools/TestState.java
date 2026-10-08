package tools;
import org.geysermc.geyser.api.block.custom.nonvanilla.JavaBlockState;

public class TestState {
    public static void main(String[] args) {
        JavaBlockState state = JavaBlockState.builder()
            .identifier("create:andesite_casing")
            .javaId(32328)
            .stateGroupId(32328)
            .build();
        System.out.println("Built state: " + state.identifier() + " id=" + state.javaId());
    }
}
