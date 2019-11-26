import json, shutil, os

try:
    import bluetooth
except ImportError:
    os.system("apt-get -y install bluetooth bluez python3-bluez")

try:
    import RPi.GPIO
except ImportError:
    os.system("apt-get -y install python3-rpi.gpio")

dir_path = "/usr/lib/scratch2/scratch_extensions/"
file_path = dir_path + "extensions.json"

files = ["pjpi.js", "dispatcher.py"]
for file in files:
    shutil.copyfile("./files/" + file, dir_path + file)

with open(file_path) as file:
    exts = json.loads(file.read())

new_row = { "name":"PJ Pi", "type":"extension", "file":"pjpi.js", "md5":"pigpio.png", "url":"", "tags":["hardware"] }
exts.append(new_row)

with open(file_path, "w") as file:
    file.write(json.dumps(exts, sort_keys=True, indent=4, separators=(',', ': ')))

content = ""
with open("/etc/systemd/system/dbus-org.bluez.service") as file:
    content = file.read()

phrase = "ExecStart=/usr/lib/bluetooth/bluetoothd"
if content.find(phrase + " -C") == -1:
    content.replace(phrase, phrase + " -C")

with open("/etc/systemd/system/dbus-org.bluez.service", "w") as file:
    ile.write(content)

os.system("sdptool add SP")
os.system("systemctl daemon-reload")
os.system("service bluetooth restart")
