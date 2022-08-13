# Alarma

A very simple wifi-controlled relay based on Raspberry Pi Pico W.

## How to install
1. Connect an alarm indicator (say, a cool beacon light) to pin 6
2. Install [micropython](https://www.raspberrypi.com/documentation/microcontrollers/micropython.html) on your raspi pico
3. Install `ampy` on your computer
```
$ pip3 install --user adafruit-ampy
```

4. Create `secrets.json` with your wifi information
```json
[
    {
        "ssid": "MyFi",
        "psk": "SuperCoolPassword"
    },
    {
        "ssid": "Pretty Fly for a WiFi",
        "psk": "Uno Dos Tres"
    }
]
```

5. Put `secrets.json` on the raspi. (Change the serial device below to match your system)
```
$ ampy --port /dev/ttyACM0 put secrets.json
```

6. Put `alarma.py` on the raspi, with the name `main.py`:
```
$ ampy --port /dev/ttyACM0 put alarma.py main.py
```

7. Verify that files were transferred and named properly:
```
$ ampy --port /dev/ttyACM0 ls
/main.py
/secrets.json
```

Done! The pico will run the program on every boot.

## How to troubleshoot
You can run the script while connected to your computer, to test your wifi settings and show the received IP address, etc.

```
$ ampy --port /dev/ttyACM0 run alarma.py
Loaded networks: ['MyFi', "Pretty Fly for a WiFi"]
MAC address: 28:CD:C1:01:74:6C
Attempting connection to MyFi...
Connected to MyFi!
('192.168.1.33', '255.255.255.0', '192.168.1.1', '1.1.1.1')
```

## How to use

Send a single UDP packet to the device on port 112 to turn on the alarm relay for a while. The content of the packet has no importance. That's it.

The pi will flash the LED while attempting to connect to one of your configured WiFi networks. Once you get a solid light, it has connected. Figure out its IP address (or see `How to troubleshoot` above.)



The examples below use the hostname `sirene` as a placeholder for the IP address of the device.

### bash
`echo "beep" > /dev/udp/sirene/112`

### netcat (GNU or OpenBSD)
`echo "beep" | nc -q 0 -u sirene 112`

### Windows Powershell
`powershell "(New-Object System.Net.Sockets.UdpClient).Send('', 0, (New-Object System.Net.IPEndPoint([System.Net.IPAddress]::Parse('192.168.52.33'), 112)))"`

### socat
`echo "beep" | socat - UDP4-DATAGRAM:sirene:112`