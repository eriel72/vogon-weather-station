import usocket as socket
import time

class MQTTClient:
    def __init__(self, client_id, server, port=1883):
        self.client_id = client_id
        self.server = server
        self.port = port
        self.sock = None

    def connect(self):
        self.sock = socket.socket()
        self.sock.connect((self.server, self.port))

        # MQTT CONNECT (minimal, men stabil nog för Mosquitto)
        pkt = bytearray()

        pkt += b"\x10"  # CONNECT
        payload = self.client_id.encode()

        remaining = 10 + len(payload)
        pkt += bytes([remaining])

        pkt += b"\x00\x04MQTT\x04\x02\x00\x3C"
        pkt += bytes([0, len(payload)]) + payload

        self.sock.send(pkt)
        time.sleep(0.1)

    def publish(self, topic, msg):
        topic = topic.encode()
        msg = msg.encode()

        pkt = bytearray()
        pkt += b"\x30"

        remaining = 2 + len(topic) + len(msg)
        pkt += bytes([remaining])

        pkt += bytes([0, len(topic)]) + topic + msg

        self.sock.send(pkt)