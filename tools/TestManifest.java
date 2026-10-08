package tools;

import java.io.*;
import java.util.zip.*;
import org.geysermc.geyser.pack.GeyserResourcePackManifest;
import org.geysermc.geyser.util.FileUtils;

public class TestManifest {
    public static void main(String[] args) {
        try (ZipFile zf = new ZipFile("headless_server/geyser/packs/CreateKineticPack.zip")) {
            ZipEntry entry = zf.getEntry("manifest.json");
            System.out.println("Found entry: " + entry);
            GeyserResourcePackManifest obj = FileUtils.loadJson(zf.getInputStream(entry), GeyserResourcePackManifest.class);
            System.out.println("Loaded manifest: " + obj);
            System.out.println("Header UUID: " + obj.header().uuid());
            System.out.println("Modules: " + obj.modules());
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
