import subprocess
import glob

javac = r"C:\Program Files\Java\jdk-21.0.12\bin\javac.exe"

# Gather libraries for classpath
jars = glob.glob("headless_server/libraries/**/*.jar", recursive=True)
cp = ";".join(jars)
print(f"Total jars in classpath: {len(jars)}")
