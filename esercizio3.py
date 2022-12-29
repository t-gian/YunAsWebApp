import time

import requests
import uuid as uuid
import paho.mqtt.client as PahoMQTT


def myOnConnect(paho_mqtt, userdata, flags, rc):
    if rc != 0:
        exit(-1)

def creaJson(val):
    return '{"bn": "Yun", "e": [{"n": "Led", "t":'+time.time().__str__()+', "v":'+ val.__str__()+', "u": null}]}'

if __name__ == "__main__":
    #paramentri del service
    endpoint = "end"
    descr = "sonoUnMQTTSubscriber"
    uuid = uuid.uuid1().__str__()
    #ottengo le info relative al catalog
    get = requests.get("http://127.0.0.1:8097/")
    get = get.json()
    #mi iscrivo come service
    requests.post(get["subscriptions"]["REST"]["service"],
                  json={"uid": uuid, "end-points": endpoint, "description": descr})
    #ottengo la lista dei devices connessi al catalog
    dispositivi = requests.get(get["subscriptions"]["REST"]["device"])
    dispositivi = dispositivi.json()
    #definisco il publisher MQTT
    uid = ""
    topic = ""
    mqtt = PahoMQTT.Client(uuid)
    mqtt.on_connect = myOnConnect
    mqtt.connect(get["subscriptions"]["MQTT"]["device"]["hostname"],
                 int(get["subscriptions"]["MQTT"]["device"]["port"]))
    listaTopic = []
    #ottengo i topic di tutti i device che hanno un Led
    for i in dispositivi:
        if "Led" in i["resources"]:
            topic = i["end-point"]
            listaTopic.append(topic)
    val = 0
    while True:
        for i in listaTopic:
            mqtt.publish(i,creaJson(val))#pubblico in TUTTI i topic ottenuti il valore 0 o 1 alternativamente ogni 15s
        time.sleep(15)
        if val == 0:
            val = 1
        else:
            val = 0
