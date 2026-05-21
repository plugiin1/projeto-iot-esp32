import usocket as socket
import ustruct as struct
from ubinascii import hexlify

class MQTTException(Exception): pass

class MQTTClient:
    def __init__(self, client_id, server, port=0, user=None, password=None, keepalive=0, ssl=False, ssl_params={}):
        if port == 0: port = 8883 if ssl else 1883
        self.client_id = client_id; self.sock = None; self.server = server; self.port = port
        self.ssl = ssl; self.ssl_params = ssl_params; self.pid = 0; self.cb = None
        self.user = user; self.pswd = password; self.keepalive = keepalive

    def _send_str(self, s): self.sock.write(struct.pack("!H", len(s))); self.sock.write(s)
    def _recv_len(self):
        n = 0; sh = 0
        while 1:
            b = self.sock.read(1)[0]; n |= (b & 0x7F) << sh
            if not b & 0x80: return n
            sh += 7

    def set_callback(self, f): self.cb = f
    def connect(self, clean_session=True):
        self.sock = socket.socket(); ai = socket.getaddrinfo(self.server, self.port)[0]
        self.sock.connect(ai[-1])
        if self.ssl: import ussl; self.sock = ussl.wrap_socket(self.sock, **self.ssl_params)
        premsg = bytearray(b"\x10\0\0\4MQTT\x04\x02\0\0")
        msg = bytearray([0x10, 0, 0, 4, 0x4D, 0x51, 0x54, 0x54, 4, 0, 0, 0])
        msg[9] = clean_session << 1
        if self.user: msg[9] |= 0x80; msg[10] |= 0x40
        if self.keepalive: msg[11] = self.keepalive
        self._send_str(self.client_id)
        self.sock.write(msg[1:12])
        if self.user: self._send_str(self.user); self._send_str(self.pswd)
        res = self.sock.read(4)
        return res[3] & 1

    def disconnect(self): self.sock.write(b"\xe0\0"); self.sock.close()
    def ping(self): self.sock.write(b"\xc0\0")
    def publish(self, topic, msg, retain=False, qos=0):
        pkt = bytearray([0x30 | (qos << 1) | retain, 0])
        self.sock.write(pkt[0:1])
        self._send_str(topic); self.sock.write(msg)

    def subscribe(self, topic, qos=0):
        self.sock.write(b"\x82"); self.pid += 1
        self.sock.write(struct.pack("!H", len(topic) + 5))
        self.sock.write(struct.pack("!H", self.pid))
        self._send_str(topic); self.sock.write(bytes([qos]))

    def check_msg(self):
        self.sock.setblocking(False)
        try: res = self.sock.read(1)
        except OSError: return None
        self.sock.setblocking(True)
        if res is None: return None
        if res == b"": return None
        if res == b"\xd0": self.sock.read(1); return None
        op = res[0]
        if op & 0xF0 != 0x30: return None
        sz = self._recv_len()
        topic_len = struct.unpack("!H", self.sock.read(2))[0]
        topic = self.sock.read(topic_len)
        sz -= topic_len + 2
        if op & 6: self.sock.read(2); sz -= 2
        msg = self.sock.read(sz)
        self.cb(topic, msg)