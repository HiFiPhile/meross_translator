Lightweight Meross MQTT translator to deal with `messageId`, `timestamp` and `sign`

# Setup

Node version may need be changed:

https://github.com/bytespider/Meross/issues/87

```
Getting info about device with IP 10.10.10.1. Error unable to connect to device. Cannot read properties of undefined (reading 'system')
```

- Install and use 20.0.0
```

wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash

nvm install v20.0.0
nvm use v20.0.0
nvm ls
```

- Setup MQTT server witl TLS:

https://github.com/bytespider/Meross/wiki/MQTT

- Setup WiFi
```
npm install meross@beta
bin/meross setup --wifi-ssid <SSID> --wifi-pass <PWD> --mqtt mqtts://<IP>:8883
```

- Get info:
```
Setting up device with IP 192.168.2.158
┌──────────────────────────────────────────────────┬──────────────────────────────────────────┐
│Primary MQTT broker                               │192.168.2.30:1883                         │
├──────────────────────────────────────────────────┼──────────────────────────────────────────┤
│Failover MQTT broker                              │192.168.2.30:1883                         │
└──────────────────────────────────────────────────┴──────────────────────────────────────────┘
┌────────────────────┬────────────────────────────────────────────────────────────────────────┐
│Device              │msl120d eu mt7682 (hardware:2.0.0 firmware:2.1.5)                       │
├────────────────────┼────────────────────────────────────────────────────────────────────────┤
│UUID                │2304253613440052050a48e1e9c4b296                                        │
├────────────────────┼────────────────────────────────────────────────────────────────────────┤
│Mac address         │48:e1:e9:c4:b2:96                                                       │
├────────────────────┼────────────────────────────────────────────────────────────────────────┤
│IP address          │192.168.2.158                                                           │
├────────────────────┼────────────────────────────────────────────────────────────────────────┤
│Current MQTT broker │192.168.2.30:1883                                                       │
├────────────────────┼────────────────────────────────────────────────────────────────────────┤
│Credentials         │User: 48:e1:e9:c4:b2:96                                                 │
│                    │Password: 0_91f361352132ac055af19fb0c65b8d57                            │
├────────────────────┼────────────────────────────────────────────────────────────────────────┤
│MQTT topics         │Publishes to: /appliance/2304253613440052050a48e1e9c4b296/publish       │
│                    │Subscribes to: /appliance/2304253613440052050a48e1e9c4b296/subscribe    │
└────────────────────┴────────────────────────────────────────────────────────────────────────┘
```

- Check connection:
```
mosquitto_sub -h 192.168.2.30 -p 8883 -t /appliance/2304253613440052050a48e1e9c4b296/publish --cafile /etc/mosquitto/certs/ca.crt 
{"header":{"messageId":"cb880734276481d52c0dbbd256de61c6","namespace":"Appliance.System.Report","method":"PUSH","payloadVersion":1,"from":"/appliance/2304253613440052050a48e1e9c4b296/publish","timestamp":1736632755,"timestampMs":760,"sign":"069b65b2ea63e23935841384d43bf173"},"payload":{"report":[{"type":"1","value":"0","timestamp":1736632755}]}}
{"header":{"messageId":"211bd3bf4aa95002cff1f7e78702fbb0","namespace":"Appliance.Control.Bind","method":"SET","payloadVersion":1,"from":"/appliance/2304253613440052050a48e1e9c4b296/subscribe","timestamp":1736629512,"timestampMs":662,"sign":"606cad9a2c99ac8b976eaa8e302a1cb0"},"payload":{"bind":{"bindTime":1736629512,"time":{"timestamp":1736629512,"timezone":"","timeRule":[]},"hardware":{"type":"msl120d","subType":"eu","version":"2.0.0","chipType":"mt7682","uuid":"2304253613440052050a48e1e9c4b296","macAddress":"48:e1:e9:c4:b2:96"},"firmware":{"version":"2.1.5","compileTime":"2022/09/14 16:42:00 GMT +08:00","encrypt":1,"wifiMac":"02:0c:43:26:60:00","innerIp":"192.168.2.158","server":"192.168.2.30","port":8883,"userId":0}}}}
```

- `BIND` need to be confirmed with `SETACK`:

https://github.com/bytespider/Meross/issues/57#issuecomment-1416789185

```
/appliance/<appliance_id>/subscribe {
  header: {
    messageId: <same as the one received in the 'SET' incoming message>,
    namespace: 'Appliance.Control.Bind',
    timestamp: <same as the one received in the 'SET' incoming message>,
    method: 'SETACK',
    sign: <same as the one received in the 'SET' incoming message>,
    from: '/cloud/hook/subscribe' // don't know if required, kept it just in case
  },
  payload: {}
}

mosquitto_pub -h 192.168.2.30 -p 8883 --cafile /etc/mosquitto/certs/ca2.crt -t /appliance/2304253613440052050a48e1e9c4b296/subscribe -m '{"header":{"messageId":"211bd3bf4aa95002cff1f7e78702fbb0","namespace":"Appliance.Control.Bind","method":"SETACK","payloadVersion":1,"from":"/appliance/2304253613440052050a48e1e9c4b296/subscribe","timestamp":1736629512,"timestampMs":662,"sign":"606cad9a2c99ac8b976eaa8e302a1cb0"},"payload":{}}'
```

# Usage
Launch `/meross_translator.py -a <IP> -c ./ca.crt`

Data sent to `meross/translator` topic will be forwarded to devices:
```jsonc
{
  "uuid": "2304253613440052050a48e1e9c4b296", # Device UUID
  "namespace": "Appliance.Control.Light",     # Command namespace
  "payload": {                                # Raw payload
    "light": {
      "capacity": 6,
      "channel": 0,
      "rgb": 16753920,
      "temperature": 50,
      "luminance": 100,
      "transform": 0
    }
  }
}

mosquitto_pub -h 192.168.2.30 -p 8883 --cafile /etc/mosquitto/certs/ca.crt -t meross/raw -m '{"uuid":"2304253613440052050a48e1e9c4b296","namespace":"Appliance.Control.Light","payload":{"light":{"capacity":6,"channel":0,"rgb":16753920,"temperature":100,"luminance":100,"transform":0}}}'
```
