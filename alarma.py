#
# Micropython
#
# Network-enabled alarm light. It's a simple relay controlled by UDP, really.
#
# Prerequisites:
#  * Raspi Pico W
#  * secrets.json containing a list of known wifi networks
#    [ 
#      { "ssid": "network_name", "psk":"secrets"},
#      { "ssid": "another_network", "psk": "public_password"}
#    ]
#
# Connections:
#  GP6: pulled high to enable the external light. Low to disable it.
#
# Usage:
#  LED flashes on boot until a network connection is made.
#  Once a network connection is made, the LED stays on.
#  Send a UDP packet on port 112 (any contents) to light up the alarm
#  LED goes out while alarm light is on, to indicate successful activation.

import sys
import json
import machine
import time
import network
import socket
import select

LED = machine.Pin("LED", machine.Pin.OUT)
BEACON = machine.Pin(6, machine.Pin.OUT)
PORT = 112
ALARM_DURATION = 4
ALARM_MAX_QUEUE = 5
WLAN = network.WLAN(network.STA_IF)


# Indicate on the on-board LED
def flash(on,off):
    LED.on()
    time.sleep(on)
    LED.off()
    time.sleep(off)

# Sound the alarm!!
def alarm(on):
    if on:
        LED.off()
        BEACON.on()
    else:
        LED.on()
        BEACON.off()


# Make a nice human-readable MAC address
def get_mac(wlan):
    macb = wlan.config('mac')
    mac = ":".join( [ f"{b:02X}" for b in macb ] )
    return mac

# Keep trying to connect 
def try_connect(networks):
    WLAN.active(False)
    WLAN.active(True)

    try_time = 10
    while True:
        for net in networks:

            print(f"Attempting connection to {net['ssid']}...")
            WLAN.connect(net["ssid"], net["psk"])

            for wait in range(try_time):
                flash(0.25,0.75)
                if WLAN.isconnected():
                    print(f"Connected to {net['ssid']}!")
                    print(str(WLAN.ifconfig()))
                    return

        if try_time < 30:
            try_time += 5

# Read out and discard all buffered data
def purge_socket(sock):
    sock.setblocking(False)
    data = sock.read()
    #print("Purging data:" + str(data))
    sock.setblocking(True)

def main_loop():
    LED.on()

    local_addr, mask, gw, dns = WLAN.ifconfig()

    # Gimme a UDP server socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((local_addr, PORT))

    while WLAN.isconnected():

        # Poll with a timeout so we can detect network failure
        r,_,_ = select.select([sock], [], [], 1)
    
        if len(r) == 0:
            sys.stdout.write(".")   # Keep the ampy terminal alive, if we're running interactively
            continue

        sys.stdout.write("\n")
        print(f"Alarm triggered!")

        # Something was received on the socket. We don't have to care what.
        purge_socket(sock)

        alarm(True)
        
        # If we keep receiving packets, keep on alarm-ing up to a certain point
        for consecutive in range(ALARM_MAX_QUEUE):
            time.sleep(ALARM_DURATION)
            r,_,_ = select.select([sock], [], [], 0.01)
            if len(r) == 0: break

            print(f"Queued up alarm, triggering number {consecutive+1}")
            purge_socket(sock)
            
        
        alarm(False)

        # But then make sure we keep at most a 50% duty cycle.
        # This is to keep the circuit board from catching fire.
        sys.stdout.write(f"Cooling down")
        for t in range((consecutive+1) * ALARM_DURATION):
            time.sleep(1)
            sys.stdout.write(".")
        sys.stdout.write("\nReady for more")

        # Nothing can be queued up during the cooldown period.
        #purge_socket(sock)
            







networks = json.loads(open("secrets.json", "r").read())

netnames = [ n["ssid"] for n in networks ]
print("Loaded networks: " + str(netnames))
print(f"MAC address: {get_mac(WLAN)}")

while True:
    try_connect(networks)
    main_loop()
    print("Network disconnected. Reconnecting.")