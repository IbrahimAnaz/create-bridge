package tools.agent;

import com.sun.tools.attach.VirtualMachine;
import java.io.File;

public class Attach {
    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.out.println("Usage: Attach <pid> <agentJarPath>");
            return;
        }
        String pid = args[0];
        String agentJar = new File(args[1]).getAbsolutePath();
        System.out.println("Attaching agent " + agentJar + " to PID " + pid + "...");
        VirtualMachine vm = VirtualMachine.attach(pid);
        vm.loadAgent(agentJar);
        vm.detach();
        System.out.println("Agent successfully loaded and detached!");
    }
}
