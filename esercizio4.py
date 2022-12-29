import time
import uuid as uuid
import json
import requests
import paho.mqtt.client as PahoMQTT

# definisco i valori di temperatura minimi e massimi del ventilatore e del riscaldamento

Tmin_vent_nessuno = 15
Tmax_vent_nessuno = 30
Tmin_vent_qualcuno = 20
Tmax_vent_qualcuno = 35

Tmin_risc_nessuno = 20
Tmax_risc_nessuno = 10
Tmin_risc_qualcuno = 25
Tmax_risc_qualcuno = 15

timeout_pir = 30 * 60
delayStart_pir = 0

delayStart_sm = 0
timeout_sm = 60 * 60
n_sound_events = 50
n_sound_events_rilevati = 0
sound_interval = 10 * 60
contatoreTempoSM = 0
forse = 0

presence = 0
topics = []
mqtt = ""


def myOnConnect(paho_mqtt, userdata, flags, rc):
    if rc != 0:
        exit(-1)


# funzione che serve a calcolare il valore da impostare al fan
def fan(temperature):
    T = temperature
    if presence == 0:
        if temperature < Tmin_vent_nessuno:
            T = Tmin_vent_nessuno
        elif T > Tmax_vent_nessuno:
            T = Tmax_vent_nessuno
        current_speed = 255 * ((T - Tmin_vent_nessuno) / (Tmax_vent_nessuno - Tmin_vent_nessuno))
    else:
        if T < Tmin_vent_qualcuno:
            T = Tmin_vent_qualcuno
        elif T > Tmax_vent_qualcuno:
            T = Tmax_vent_qualcuno
        current_speed = 255 * ((T - Tmin_vent_qualcuno) / (Tmax_vent_qualcuno - Tmin_vent_qualcuno))
    return current_speed


# funzione che serve a calcolare il valore da impostare al riscaldamento
def heat(temperature):
    T = temperature
    if presence == 0:
        if T > Tmin_risc_nessuno:
            T = Tmin_risc_nessuno
        elif T < Tmax_risc_nessuno:
            T = Tmax_risc_nessuno
        intensita = 255 * ((T - Tmin_risc_nessuno) / (Tmax_risc_nessuno - Tmin_risc_nessuno))
    else:
        if T > Tmin_risc_qualcuno:
            T = Tmin_risc_qualcuno
        elif T < Tmax_risc_qualcuno:
            T = Tmax_risc_qualcuno
        intensita = 255 * ((T - Tmin_risc_qualcuno) / (Tmax_risc_qualcuno - Tmin_risc_qualcuno))
    intensita = abs(intensita)
    return intensita


# funzione che serve a modificare i valori della temperatura
def modificaTemp(input, val1):
    val1 = float(val1)
    global Tmin_vent_nessuno, Tmax_vent_nessuno, Tmin_vent_qualcuno, Tmax_vent_qualcuno, Tmin_risc_nessuno, \
        Tmax_risc_nessuno, Tmin_risc_qualcuno, Tmax_risc_qualcuno
    if input == "Am+":
        if presence == 0:
            Tmin_vent_nessuno += val1
        else:
            Tmin_vent_qualcuno += val1
    elif input == "Am-":
        if presence == 0:
            Tmin_vent_nessuno -= val1
        else:
            Tmin_vent_qualcuno -= val1
    elif input == "AM+":
        if presence == 0:
            Tmax_vent_nessuno += val1
        else:
            Tmax_vent_qualcuno += val1
    elif input == "AM-":
        if presence == 0:
            Tmax_vent_nessuno -= val1
        else:
            Tmax_vent_qualcuno -= val1
    elif input == "Hm+":
        if presence == 0:
            Tmin_risc_nessuno += val1
        else:
            Tmin_risc_qualcuno += val1
    elif input == "Hm-":
        if presence == 0:
            Tmin_risc_nessuno -= val1
        else:
            Tmin_risc_qualcuno -= val1
    elif input == "HM+":
        if presence == 0:
            Tmax_risc_nessuno += val1
        else:
            Tmax_risc_qualcuno += val1
    elif input == "HM-":
        if presence == 0:
            Tmax_risc_nessuno -= val1
        else:
            Tmax_risc_qualcuno -= val1


def proporzione(val2):
    return int((val2 * 100) / 255)


def getValues(map, temperature, pir, noise):
    for i in range(3):
        resource = map["e"][i]["n"]
        if resource == "temperature":
            temperature = map["e"][i]["v"]
        elif resource == "presence":
            pir = map["e"][i]["v"]
        elif resource == "noise":
            noise = map["e"][i]["v"]


def daStampare(temp, presence, speed, heat1):
    if presence == 0:
        d1 = {"AC": {"m": Tmin_vent_nessuno, "M": Tmax_vent_nessuno},
              "HT": {"m": Tmin_risc_nessuno, "M": Tmax_risc_nessuno}}
    else:
        d1 = {"AC": {"m": Tmin_vent_qualcuno, "M": Tmax_vent_qualcuno},
              "HT": {"m": Tmin_risc_qualcuno, "M": Tmax_risc_qualcuno}}
    d = {"T": temp, "Pres": presence, "AC": proporzione(speed), "HT": proporzione(heat1)}
    d.update(d1)
    d_json = json.dumps(d)
    mqtt.publish(topics[2], d_json)


# se il PIR ha rilevato delle persone allora presence vieni impostato a 1
def checkPir():
    global presence, delayStart_pir, delayStart_sm
    presence = 1
    delayStart_pir = time.time()
    delayStart_sm = delayStart_pir


# se il soundModule ha rilevato un rumore verifico di aver rilevato abbastanza eventi da poter assumere la presenza
# di persone
def checkSm():
    global presence, forse, n_sound_events_rilevati, contatoreTempoSM, delayStart_pir, delayStart_sm
    if forse != 1:
        contatoreTempoSM = time.time()
    if (time.time() - contatoreTempoSM) <= sound_interval:
        forse = 1
        n_sound_events_rilevati += 1
        if n_sound_events_rilevati > n_sound_events:
            presence = 1
            n_sound_events_rilevati = 0
            delayStart_sm = time.time()
            delayStart_pir = delayStart_sm
    else:
        n_sound_events_rilevati = 0
        forse = 0


def myOnMessageReceived(paho_mqtt, userdata, message):
    if message.topic != topics[0]:
        return
    mappa = message.payload.decode('utf-8')
    mappa = json.loads(mappa)
    temp = pir = noise = 0
    getValues(mappa, temp, pir, noise)
    speedval = fan(temp)
    heatval = heat(temp)
    if pir == 1:
        checkPir()
    if noise == 1:
        checkSm()
    tempo = time.time()
    # verifico che non sia passato troppo tempo dall'ultima rilevazione
    if (tempo - delayStart_pir) > timeout_pir or (tempo - delayStart_sm) > timeout_sm:
        presence = 0
    d = {"bn": uuid, "e": [{"n": "Fan", "t": time.time(), "u": "null", "v": speedval},
                           {"n": "Heat", "t": time.time(), "u": "null", "v": heatval}]}
    print(f"pubblico su {topics[1]}")
    mqtt.publish(topics[1], json.dumps(d))
    print(f"pubblico su {topics[2]}")
    mqtt.publish(topics[2], daStampare(temp, presence, speedval, heatval))


uuid = uuid.uuid1().__str__()

if __name__ == "__main__":
    endpoint = "end"
    descr = "sonoUnMQTTSubscriber"
    risorsedaver = ["Fan", "Heat", "SensorNoise", "PIR", "LCD"]
    get = requests.get("http://127.0.0.1:8097/")
    get = get.json()
    requests.post(get["subscriptions"]["REST"]["service"],
                  json={"uid": uuid, "end-points": endpoint, "description": descr})
    dispositivi = requests.get(get["subscriptions"]["REST"]["device"])
    dispositivi = dispositivi.json()
    for i in dispositivi:
        if "ArduinoYun" == i["uid"] and i["resources"] == risorsedaver:
            topics = i["end-point"]  # la Yun usa 3 topic: il primo in cui comunica i dati nel formato SenML
            # il secondo è il topic in cui inviare i comandi del fan e di heat
            # il terzo è il topic in cui devo inviare il messaggio da stampare sul LCD
            break
    mqtt = PahoMQTT.Client(uuid)
    mqtt.on_connect = myOnConnect
    mqtt.on_message = myOnMessageReceived
    mqtt.connect(get["subscriptions"]["MQTT"]["device"]["hostname"],
                 int(get["subscriptions"]["MQTT"]["device"]["port"]))
    mqtt.subscribe(topics[0], 2)
    mqtt.loop_start()
    while True:
        msg = input(">>Cosa vuoi modificare: ")
        val = input(">>Di quanto: ")
        modificaTemp(msg, val)
        time.sleep(10)
