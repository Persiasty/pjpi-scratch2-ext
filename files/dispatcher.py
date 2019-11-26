import subprocess
import bluetooth
import signal
import sys
import os
import time
import re
import socket
import threading
import RPi.GPIO as GPIO

#/etc/systemd/system/dbus-org.bluez.service
#ExecStart=/usr/lib/bluetooth/bluetoothd
#to
#ExecStart=/usr/lib/bluetooth/bluetoothd -C
#sudo sdptool add SP
#sudo systemctl daemon-reload
#sudo service bluetooth restart


uuid = "00001101-0000-1000-8000-00805F9B34FB"
is_running = True
is_connected = False

bt_server = None
bt_client = None

scratch = None


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
gpios = {}

def fnc_btsend(data):
    if bt_client is not None:
        bt_client.sendall(data)
            
def fnc_pwmstart(gpio, freq, duty):
    global gpios
    print(gpios)
    gpio = int(gpio)
    gentry = None
    if gpio not in gpios:
        gpios[gpio] = {"freq": int(freq), "duty": float(duty), "state": False, "pwm": None}
        GPIO.setup(gpio, GPIO.OUT)
    else:
        gpios[gpio]["freq"] = int(freq)
        gpios[gpio]["duty"] = float(duty)
    
    gentry = gpios[gpio]
    if gentry["pwm"] is None:
        p = GPIO.PWM(gpio, gentry["freq"])
        gpios[gpio]["pwm"] = p
    else:
        gpios[gpio]["pwm"].ChangeFrequency(gentry["freq"])
    
    if not gentry["state"]:
        gpios[gpio]["pwm"].start(gentry["duty"])
        gpios[gpio]["state"] = True
    else:
        gpios[gpio]["pwm"].ChangeDutyCycle(gentry["duty"])
        
def fnc_pwmstop(gpio):
    gpio = int(gpio)
    if gpio in gpios:
        gpios[gpio]["pwm"].stop()
        gpios[gpio]["state"] = False
    
def setup_bt_server():
    global bt_server
    bt_server = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    bt_server.bind(("", 1))
    bt_server.listen(1)

    bluetooth.advertise_service(bt_server, "Raspberry Pi",
                                service_id = uuid,
                                service_classes = [uuid, bluetooth.SERIAL_PORT_CLASS],
                                profiles = [bluetooth.SERIAL_PORT_PROFILE])

def setup_scratch_client():
    global scratch
    scratch = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def connect_to_scratch(host="127.0.0.1", port=54321):
    global scratch
    scratch.connect((host, port))

def scratch_recv():
    global scratch, bt_client, is_running
    while is_running:
        data = scratch.recv(1024)
        if data == b'':
            shutdown()
        
        if data is not None and len(data) > 0:
            args = data.decode('utf-8').split(";")
            fnc = "fnc_" + args[0]
            args = args[1:]
            globals()[fnc](*args)
            print(fnc, *args)

def bt_recv():
    global scratch, bt_client
    try:
        data = bt_client.recv(1024)
        print(data[:-1])
        if data is not None and len(data) > 0 and scratch is not None:
            scratch.sendall(data[:-1])
    except:
        print("Error while receiving data from BT")


def signal_kill(signal, frame):
    shutdown()
    
def shutdown():
    global is_running, is_connected
    global bt_server, bt_client, scratch
    print("Exiting...")
    is_running = False
    is_connected = False

    if bt_client is not None:
        bt_client.close()
    bt_server.close()
    
    if scratch is not None:
        scratch.close()
        
    GPIO.cleanup()
    os._exit(0)


def main():
    global is_running, is_connected
    global bt_client, bt_server
    
    port = 54321
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    signal.signal(signal.SIGINT, signal_kill)
    
    setup_bt_server()
    setup_scratch_client()
    connect_to_scratch(port=port)
    threading.Thread(target=scratch_recv).start()
    
    while is_running:
        print("Waiting for connection...")

        try:
            bt_client, address = bt_server.accept()
        except:
            break

        print("Accepted connection from ", address)
        is_connected = True

        while is_connected:
            bt_recv()
            
if __name__ == "__main__":
    main()

