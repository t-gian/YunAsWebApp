import paho.mqtt.client as mqtt
import json
import time
import requests

MESSAGE = {
    "bn": "YunGroup13",
    "e": []
}
MEASURE = {
    "n": "temperature",
    "u": "Cel",
    "t": 0,
    "v": 0.0
}


if __name__ == "__main__":
    client = mqtt.Client()
    uuid = "ArduinoYun"
    get = requests.get("http://127.0.0.1:8097/")
    get = get.json()
    requests.post(get["subscriptions"]["REST"]["device"],
                  json={"uid": uuid, "end-points": "temperature", "description": "SonoUnPublisher"})
    topic = get["subscriptions"]["MQTT"]["device"]["hostname"]
    mqtt.connect(topic,
                 int(get["subscriptions"]["MQTT"]["device"]["port"]))
    client.loop_start()
    while True:
        msg = input()
        msg = msg.split(':')
        if msg[0] == 'T':
            try:
                val = float(msg[1].strip())
            except:
                print("E:1")
                continue
            MEASURE["t"] = time.time()
            MEASURE["v"] = val
            MESSAGE["e"] = [MEASURE]
            json_data = json.dumps(MESSAGE).encode('utf-8')
            client.publish( "/tiot/13", json_data)
        else:
            print("E:2")
