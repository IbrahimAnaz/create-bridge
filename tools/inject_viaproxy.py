import zipfile, os, shutil

jar_path = 'headless_server/viaproxy/ViaProxy.jar'
backup_path = 'headless_server/viaproxy/ViaProxy.jar.bak2'

if not os.path.exists(backup_path):
    shutil.copyfile(jar_path, backup_path)

temp_jar = 'headless_server/viaproxy/ViaProxy_temp.jar'

with zipfile.ZipFile(jar_path, 'r') as zin, zipfile.ZipFile(temp_jar, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        if item.filename == 'com/viaversion/viaversion/api/data/MappingDataBase.class':
            print("Replacing MappingDataBase.class")
            with open('tools/staging/MappingDataBase_patched.class', 'rb') as f:
                zout.writestr(item, f.read())
        elif item.filename == 'com/viaversion/viabackwards/api/data/BackwardsMappingData.class':
            print("Replacing BackwardsMappingData.class")
            with open('tools/staging/BackwardsMappingData_patched.class', 'rb') as f:
                zout.writestr(item, f.read())
        else:
            zout.writestr(item, zin.read(item.filename))

shutil.move(temp_jar, jar_path)
print("Successfully injected patched classes into ViaProxy.jar!")
