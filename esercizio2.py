import json
import uuid

import paho.mqtt.client as PahoMQTT
import time

import requests


def myOnConnect(paho_mqtt, userdata, flags, rc):
    if rc != 0:
        exit(-1)

#quando ricevo un messaggio scrivo il topic da cui deriva e il valore della temperatura ottenuta
def myOnMessageReceived(paho_mqtt, userdata, message):
    msg=message.payload.decode('utf-8')
    msg=json.loads(msg)
    print("Dal Topic: "+message.topic+" ricevo: "+msg["e"][0]["v"].__str__()+" "+msg["e"][0]["u"])


if __name__ == "__main__":
    #valori del mio service
    endpoint = "end"
    descr = "sonoUnMQTTPublisher"
    uuid = uuid.uuid1().__str__()
    #ottengo le informazioni relative al catalog
    get = requests.get("http://127.0.0.1:8097/")
    get = get.json()
    #mi iscrivo come servizio
    requests.post(get["subscriptions"]["REST"]["service"],
                  json={"uid": uuid, "end-points": endpoint, "description": descr})
    #ottengo la lista dei devices connessi al catalog
    dispositivi = requests.get(get["subscriptions"]["REST"]["device"])
    dispositivi = dispositivi.json()
    uid = ""
    topic=""
    #definisco il publisher MQTT
    mqtt = PahoMQTT.Client(uuid)
    mqtt.on_connect = myOnConnect
    mqtt.on_message = myOnMessageReceived
    mqtt.connect(get["subscriptions"]["MQTT"]["device"]["hostname"], int(get["subscriptions"]["MQTT"]["device"]["port"]))
    #seleziono i topic di tutti i device che si occupano di temperatura e mi iscrivo ad ognuno di esso
    for i in dispositivi:
        if "Temperature" in i["resources"]:
            topic = i["end-point"]
            print("mi sottoscrivo a: " + topic)
            mqtt.subscribe(topic, 2)
    mqtt.loop_forever()

