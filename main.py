from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import mqtt_config
import json
import time

# MQTT Setup
thing_name = mqtt_config.thing_name
root_ca_path = mqtt_config.root_ca_path
certificate_path = mqtt_config.certificate_path
private_key_path = mqtt_config.private_key_path
cloud_endpoint = mqtt_config.cloud_endpoint

myMQTTClient = AWSIoTMQTTClient("python_display")
myMQTTClient.configureEndpoint(cloud_endpoint, 8883)
myMQTTClient.configureCredentials(root_ca_path,
                                  private_key_path,
                                  certificate_path)
myMQTTClient.configureOfflinePublishQueueing(-1)
myMQTTClient.configureDrainingFrequency(2)
myMQTTClient.configureConnectDisconnectTimeout(7)
myMQTTClient.configureMQTTOperationTimeout(5)

myMQTTClient.connect()

initialized = False


def set_status(status):
    print(status)


def get_callback(client, userdata, message):
    msg_json = json.loads(message.payload)
    global initialized
    try:
        state = msg_json["state"]
        desired = state["desired"]
        status = desired["display_status"]
        set_status(status)
        report = json.dumps({"state": {"reported": {"display_status": status}}})
        myMQTTClient.publish("$aws/things/{}/shadow/update".format(thing_name), report, 0)
        initialized = True
    except Exception as e:
        initialized = False



def callback(client, userdata, message):
    try:
        msg_json = json.loads(message.payload)
        state = msg_json["state"]
        status = state["display_status"]
        set_status(status)
        report = json.dumps({"state": {"reported": {"display_status": status}}})
        myMQTTClient.publish("$aws/things/{}/shadow/update".format(thing_name), report, 0)
    except Exception as e:
        print("Error")


if not myMQTTClient.subscribe("$aws/things/{}/shadow/get/accepted".format(thing_name), 1, get_callback):
    print("Failed to subscribe for get")
    exit(1)

if not myMQTTClient.subscribe("$aws/things/{}/shadow/update/delta".format(thing_name), 1, callback):
    print("Failed to subscribe for update")
    exit(1)

myMQTTClient.publish("$aws/things/{}/shadow/get".format(thing_name), "", 1)

# Wait to get status
while not initialized:
    time.sleep(1)

print("Unsubscribing from Get topic")
myMQTTClient.unsubscribe("$aws/things/{}/shadow/get/accepted".format(thing_name))

# Loop till the end of time (i.e. our clock dies because we've run out of power)
while True:
    time.sleep(1)
