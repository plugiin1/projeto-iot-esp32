import machine, dht, time, network, urequests, json, socket, framebuf
from machine import Pin, SoftI2C, PWM, ADC
import ssd1306
import umqtt_simple

MQTTClient = umqtt_simple.MQTTClient

# ==========================================
# CONFIGURAÇÕES DE REDE E SERVIDORES
# ==========================================
MQTT_BROKER = "broker.hivemq.com"
MQTT_CLIENT_ID = "esp32_mogi_jcmcs_99"

# ==========================================
# CONFIGURAÇÃO DOS PINOS (HARDWARE)
# ==========================================
i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
sensor_dht = dht.DHT22(Pin(15))

ldr = ADC(Pin(34))
ldr.atten(ADC.ATTN_11DB)

mq2 = ADC(Pin(35))
mq2.atten(ADC.ATTN_11DB)

trig = Pin(5, Pin.OUT)
echo = Pin(18, Pin.IN)

led_red = Pin(2, Pin.OUT)
led_yellow = Pin(4, Pin.OUT)
led_blue = Pin(16, Pin.OUT)
servo = PWM(Pin(17), freq=50)

# ==========================================
# FUNÇÕES DO SISTEMA
# ==========================================
def get_dist():
    trig.value(0); time.sleep_us(2); trig.value(1); time.sleep_us(10); trig.value(0)
    t0 = time.ticks_us()
    while echo.value() == 0:
        if time.ticks_diff(time.ticks_us(), t0) > 10000: return 0
    t1 = time.ticks_us()
    while echo.value() == 1:
        if time.ticks_diff(time.ticks_us(), t1) > 25000: return 0
    return (time.ticks_diff(time.ticks_us(), t1) / 2) / 29.1

def get_weather():
    try:
        r = urequests.get('http://api.openweathermap.org/data/2.5/weather?q=Mogi%20das%20Cruzes,BR&appid=4ef098a33622c042a0bc81f164d96554&units=metric')
        t = r.json()['main']['temp']
        r.close()
        return t
    except:
        return 'Erro'

def sub_cb(topic, msg):
    c = msg.decode('utf-8')
    if c == 'vermelho_on': led_red.value(1)
    elif c == 'vermelho_off': led_red.value(0)
    elif c == 'amarelo_on': led_yellow.value(1)
    elif c == 'amarelo_off': led_yellow.value(0)
    elif c == 'azul_on': led_blue.value(1)
    elif c == 'azul_off': led_blue.value(0)
    elif c == 'porta_abrir': servo.duty(115)
    elif c == 'porta_fechar': servo.duty(40)

def web_page():
    return '''
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  body{font-family:sans-serif;padding:1rem;max-width:500px;margin:auto}
  h1{font-size:1.2rem;margin-bottom:1rem}
  .card{border:1px solid #ddd;border-radius:8px;padding:1rem;margin-bottom:.75rem}
  .label{font-size:.75rem;color:#888;margin-bottom:.5rem}
  .row{display:flex;gap:8px;flex-wrap:wrap}
  a{text-decoration:none}
  button{padding:8px 16px;border:1px solid #ccc;border-radius:6px;background:#fff;cursor:pointer;font-size:.9rem}
  button:hover{background:#f0f0f0}
  .on{background:#d4edda;border-color:#28a745;color:#155724}
  .off{background:#f8d7da;border-color:#dc3545;color:#721c24}
</style>
</head>
<body>
<h1>ESP32 Automação Residencial</h1>

<div class="card">
  <div class="label">LED Vermelho — Alarme de gás</div>
  <div class="row">
    <a href="/?led_red=on"><button class="on">Ligar</button></a>
    <a href="/?led_red=off"><button class="off">Desligar</button></a>
  </div>
</div>

<div class="card">
  <div class="label">LED Amarelo — Iluminação sala</div>
  <div class="row">
    <a href="/?led_yellow=on"><button class="on">Ligar</button></a>
    <a href="/?led_yellow=off"><button class="off">Desligar</button></a>
  </div>
</div>

<div class="card">
  <div class="label">LED Azul — Ar-condicionado</div>
  <div class="row">
    <a href="/?led_blue=on"><button class="on">Ligar</button></a>
    <a href="/?led_blue=off"><button class="off">Desligar</button></a>
  </div>
</div>

<div class="card">
  <div class="label">Servo Motor — Porta / Portão</div>
  <div class="row">
    <a href="/?servo=open"><button class="on">Abrir (duty 115)</button></a>
    <a href="/?servo=half"><button>Meio aberto (duty 77)</button></a>
    <a href="/?servo=close"><button class="off">Fechar (duty 40)</button></a>
  </div>
</div>

</body>
</html>'''

# ==========================================
# INICIALIZAÇÃO (WIFI E MQTT)
# ==========================================
oled.fill(0); oled.text('Conectando...', 0, 0); oled.show()
w = network.WLAN(network.STA_IF); w.active(True); w.connect('Wokwi-GUEST', '')
while not w.isconnected(): time.sleep(0.5)
print('IP Local:', w.ifconfig()[0])

clima_mogi = get_weather()
client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
client.set_callback(sub_cb)

try:
    client.connect()
    client.subscribe(b'residencia/atuadores')
    print('MQTT Conectado!')
except:
    pass

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80)); s.listen(5); s.setblocking(False)

# ==========================================
# LOOP PRINCIPAL
# ==========================================
last_pub = time.ticks_ms()

while True:
    try:
        # 1. Checa mensagens MQTT
        client.check_msg()
        
        # 2. Checa servidor Web Local
        try:
            conn, addr = s.accept()
            req = conn.recv(1024).decode('utf-8')
            if '/?led_red=on' in req: led_red.value(1)
            elif '/?led_red=off' in req: led_red.value(0)
            elif '/?led_yellow=on' in req: led_yellow.value(1)
            elif '/?led_yellow=off' in req: led_yellow.value(0)
            elif '/?led_blue=on' in req: led_blue.value(1)
            elif '/?led_blue=off' in req: led_blue.value(0)
            elif '/?servo=open' in req: servo.duty(115)
            elif '/?servo=half' in req: servo.duty(77)
            elif '/?servo=close' in req: servo.duty(40)
            conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\nConnection: close\n\n' + web_page())
            conn.close()
        except OSError:
            pass

        # 3. Lê sensores e publica MQTT (A cada 5 segundos)
        if time.ticks_diff(time.ticks_ms(), last_pub) >= 5000:
            sensor_dht.measure()
            t = sensor_dht.temperature()
            u = sensor_dht.humidity()
            l = ldr.read()
            g = mq2.read()
            d = get_dist()
            
            # Atualiza Display OLED (Grid)
            oled.fill(0)
            fb = framebuf.FrameBuffer(oled.buffer, 128, 64, framebuf.MONO_VLSB)
            fb.fill_rect(0, 0, 128, 12, 1)
            fb.text('MOGI: {}C'.format(clima_mogi), 16, 2, 0)
            fb.vline(64, 12, 38, 1)
            fb.text('T:{}C'.format(t), 4, 18, 1)
            fb.text('U:{}%'.format(u), 4, 34, 1)
            fb.text('G:{}'.format(g), 70, 18, 1)
            fb.text('L:{}'.format(l), 70, 34, 1)
            fb.hline(0, 50, 128, 1)
            fb.text('DIST: {:.1f}cm'.format(d), 12, 54, 1)
            oled.show()
            
            # Publica no Node-RED
            client.publish(b'residencia/sensores', json.dumps({'temp': t, 'umid': u, 'luz': l, 'gas': g, 'dist': d}))
            print('PUB OK')
            last_pub = time.ticks_ms()

        time.sleep_ms(10)

    except Exception as e:
        print('Erro no Loop:', e)
        time.sleep(2)
        try:
            client.connect()
            client.subscribe(b'residencia/atuadores')
        except:
            pass