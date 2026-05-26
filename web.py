from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse, json

try:
    import paho.mqtt.client as mqtt
    MQTT_OK = True
except ImportError:
    MQTT_OK = False

MQTT_BROKER = "broker.hivemq.com"
TOPIC_PUB   = "residencia/atuadores"
TOPIC_SUB   = "residencia/sensores"

sensores = {"temp": None, "umid": None, "luz": None, "gas": None, "dist": None}

mc = None

if MQTT_OK:
    import threading

    def on_message(client, userdata, msg):
        global sensores
        try:
            sensores = json.loads(msg.payload.decode())
        except:
            pass

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(TOPIC_SUB)
            print("   MQTT conectado ao broker.hivemq.com ✅")
        else:
            print(f"   MQTT falhou (rc={rc})")

    def mqtt_connect():
        global mc
        try:
            mc = mqtt.Client(client_id="painel_pc_jcmcs")
            mc.on_message = on_message
            mc.on_connect = on_connect
            mc.connect(MQTT_BROKER, 1883, 60)
            mc.loop_forever()
        except Exception as e:
            print(f"   MQTT erro: {e}")

    threading.Thread(target=mqtt_connect, daemon=True).start()

HTML = """<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ESP32 — Automação Residencial</title>
<style>
:root {
  --bg: #0f1117;
  --surface: #1a1d27;
  --surface2: #222537;
  --border: #2e3148;
  --accent: #6c63ff;
  --accent2: #00d4aa;
  --text: #e8eaf0;
  --muted: #6b7280;
  --red: #ff4d6d;
  --red-bg: #2a1220;
  --yellow: #fbbf24;
  --yellow-bg: #271f0e;
  --blue: #38bdf8;
  --blue-bg: #0d1f2d;
  --green: #4ade80;
  --green-bg: #0d2018;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Segoe UI', sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  padding: 1.5rem 1rem 3rem;
}
.header {
  text-align: center;
  margin-bottom: 2rem;
}
.header h1 {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #6c63ff, #00d4aa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: .25rem;
}
.header p { font-size: .8rem; color: var(--muted); }
.mqtt-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 4px 12px;
  font-size: .75rem;
  color: var(--muted);
  margin-top: .5rem;
}
.mqtt-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: #ef4444;
  transition: background .3s;
}
.mqtt-dot.online { background: var(--green); box-shadow: 0 0 6px var(--green); }

.sensors-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
  max-width: 600px;
  margin: 0 auto 1.5rem;
}
.sensor-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: .75rem .5rem;
  text-align: center;
  transition: border-color .3s, transform .2s;
}
.sensor-card:hover { border-color: var(--accent); transform: translateY(-2px); }
.sensor-icon { font-size: 1.2rem; margin-bottom: .25rem; }
.sensor-val {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text);
  font-variant-numeric: tabular-nums;
  transition: color .3s;
}
.sensor-label { font-size: .6rem; color: var(--muted); margin-top: 2px; text-transform: uppercase; letter-spacing: .05em; }
.sensor-val.updated { color: var(--accent2); }

.section-title {
  font-size: .7rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: .1em;
  margin-bottom: .75rem;
  padding-left: .25rem;
}

.actuators {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  max-width: 600px;
  margin: 0 auto 12px;
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.1rem;
  transition: border-color .3s, box-shadow .3s;
  position: relative;
  overflow: hidden;
}
.card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: var(--card-color, var(--accent));
  border-radius: 16px 16px 0 0;
  opacity: 0;
  transition: opacity .3s;
}
.card.active::before { opacity: 1; }
.card.active { border-color: var(--card-color, var(--accent)); box-shadow: 0 0 20px -5px var(--card-color, var(--accent)); }

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 1rem;
}
.led-indicator {
  width: 14px; height: 14px;
  border-radius: 50%;
  background: #374151;
  transition: background .3s, box-shadow .3s;
  flex-shrink: 0;
}
.led-indicator.on-red   { background: var(--red);    box-shadow: 0 0 10px var(--red); }
.led-indicator.on-yellow{ background: var(--yellow);  box-shadow: 0 0 10px var(--yellow); }
.led-indicator.on-blue  { background: var(--blue);   box-shadow: 0 0 10px var(--blue); }

.card-name { font-size: .9rem; font-weight: 600; }
.card-desc { font-size: .7rem; color: var(--muted); margin-top: 1px; }

.toggle-wrap {
  display: flex;
  background: var(--surface2);
  border-radius: 10px;
  padding: 3px;
  gap: 3px;
}
.toggle-btn {
  flex: 1;
  padding: 7px 0;
  border: none;
  border-radius: 8px;
  font-size: .8rem;
  font-weight: 600;
  cursor: pointer;
  background: transparent;
  color: var(--muted);
  transition: background .2s, color .2s, transform .1s;
}
.toggle-btn:active { transform: scale(.96); }
.toggle-btn.selected-on {
  background: var(--green-bg);
  color: var(--green);
  border: 1px solid rgba(74,222,128,.3);
}
.toggle-btn.selected-off {
  background: #1f1318;
  color: #f87171;
  border: 1px solid rgba(248,113,113,.3);
}

.servo-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.25rem;
  max-width: 600px;
  margin: 0 auto;
  --card-color: var(--accent2);
  transition: border-color .3s, box-shadow .3s;
}
.servo-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.1rem;
}
.servo-title { font-size: .95rem; font-weight: 600; }
.servo-subtitle { font-size: .7rem; color: var(--muted); }
.duty-badge {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 4px 12px;
  font-size: 1rem;
  font-weight: 700;
  color: var(--accent2);
  font-variant-numeric: tabular-nums;
  min-width: 70px;
  text-align: center;
}
.servo-presets {
  display: flex;
  gap: 8px;
  margin-bottom: 1rem;
}
.preset-btn {
  flex: 1;
  padding: 8px 0;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--surface2);
  color: var(--muted);
  font-size: .8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all .2s;
}
.preset-btn:hover { border-color: var(--accent2); color: var(--accent2); background: rgba(0,212,170,.08); }
.preset-btn.active-preset { background: rgba(0,212,170,.15); color: var(--accent2); border-color: var(--accent2); }
.preset-btn:active { transform: scale(.97); }

.slider-wrap { position: relative; padding: 0 2px; }
input[type=range] {
  -webkit-appearance: none;
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: var(--border);
  outline: none;
  cursor: pointer;
}
input[type=range]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px; height: 20px;
  border-radius: 50%;
  background: var(--accent2);
  box-shadow: 0 0 8px rgba(0,212,170,.5);
  cursor: pointer;
  transition: transform .1s;
}
input[type=range]::-webkit-slider-thumb:active { transform: scale(1.2); }
.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: .65rem;
  color: var(--muted);
  margin-top: 6px;
}

.door-visual {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin: .75rem 0;
}
.door-frame {
  width: 50px; height: 60px;
  border: 2px solid var(--border);
  border-radius: 4px 4px 0 0;
  position: relative;
  overflow: hidden;
}
.door-panel {
  position: absolute;
  top: 2px; left: 2px;
  width: calc(100% - 4px);
  height: calc(100% - 2px);
  background: var(--surface2);
  border-radius: 2px;
  transform-origin: left center;
  transition: transform .5s cubic-bezier(.4,0,.2,1);
  border-right: 2px solid var(--border);
}
.door-status-text {
  font-size: .75rem;
  color: var(--muted);
  text-align: center;
}
.door-status-text span { color: var(--accent2); font-weight: 600; }

.toast {
  position: fixed;
  bottom: 1.5rem; left: 50%;
  transform: translateX(-50%) translateY(20px);
  background: var(--surface2);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 10px 20px;
  border-radius: 20px;
  font-size: .8rem;
  opacity: 0;
  transition: opacity .25s, transform .25s;
  pointer-events: none;
  white-space: nowrap;
  z-index: 99;
}
.toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }

@media(max-width:400px){
  .actuators { grid-template-columns: 1fr; }
  .sensors-grid { grid-template-columns: repeat(3,1fr); }
}
</style>
</head>
<body>

<div class="header">
  <h1>Automação Residencial</h1>
  <p>ESP32 · MicroPython · Wokwi Simulator</p>
  <div class="mqtt-badge">
    <div class="mqtt-dot" id="mqtt-dot"></div>
    <span id="mqtt-label">Conectando ao MQTT...</span>
  </div>
</div>

<div class="sensors-grid">
  <div class="sensor-card">
    <div class="sensor-icon">🌡️</div>
    <div class="sensor-val" id="s-temp">--</div>
    <div class="sensor-label">Temp °C</div>
  </div>
  <div class="sensor-card">
    <div class="sensor-icon">💧</div>
    <div class="sensor-val" id="s-umid">--</div>
    <div class="sensor-label">Umid %</div>
  </div>
  <div class="sensor-card">
    <div class="sensor-icon">☀️</div>
    <div class="sensor-val" id="s-luz">--</div>
    <div class="sensor-label">Luz LDR</div>
  </div>
  <div class="sensor-card">
    <div class="sensor-icon">💨</div>
    <div class="sensor-val" id="s-gas">--</div>
    <div class="sensor-label">Gás MQ2</div>
  </div>
  <div class="sensor-card">
    <div class="sensor-icon">📡</div>
    <div class="sensor-val" id="s-dist">--</div>
    <div class="sensor-label">Dist cm</div>
  </div>
</div>

<div style="max-width:600px;margin:0 auto 1.5rem">
  <div class="section-title">Atuadores — LEDs</div>
  <div class="actuators">

    <div class="card" id="card-red" style="--card-color: var(--red)">
      <div class="card-header">
        <div class="led-indicator" id="dot-red"></div>
        <div>
          <div class="card-name">LED Vermelho</div>
          <div class="card-desc">Alarme de gás</div>
        </div>
      </div>
      <div class="toggle-wrap">
        <button class="toggle-btn" id="btn-red-on" onclick="setLed('red','on')">Ligar</button>
        <button class="toggle-btn" id="btn-red-off" onclick="setLed('red','off')">Desligar</button>
      </div>
    </div>

    <div class="card" id="card-yellow" style="--card-color: var(--yellow)">
      <div class="card-header">
        <div class="led-indicator" id="dot-yellow"></div>
        <div>
          <div class="card-name">LED Amarelo</div>
          <div class="card-desc">Iluminação sala</div>
        </div>
      </div>
      <div class="toggle-wrap">
        <button class="toggle-btn" id="btn-yellow-on" onclick="setLed('yellow','on')">Ligar</button>
        <button class="toggle-btn" id="btn-yellow-off" onclick="setLed('yellow','off')">Desligar</button>
      </div>
    </div>

    <div class="card" id="card-blue" style="--card-color: var(--blue)">
      <div class="card-header">
        <div class="led-indicator" id="dot-blue"></div>
        <div>
          <div class="card-name">LED Azul</div>
          <div class="card-desc">Ar-condicionado</div>
        </div>
      </div>
      <div class="toggle-wrap">
        <button class="toggle-btn" id="btn-blue-on" onclick="setLed('blue','on')">Ligar</button>
        <button class="toggle-btn" id="btn-blue-off" onclick="setLed('blue','off')">Desligar</button>
      </div>
    </div>

    <div class="card" style="--card-color:#a78bfa; display:flex; flex-direction:column; justify-content:center; align-items:center; gap:6px; border-style:dashed; opacity:.5">
      <div style="font-size:1.5rem">＋</div>
      <div style="font-size:.75rem; color:var(--muted)">Novo atuador</div>
    </div>

  </div>
</div>

<div style="max-width:600px;margin:0 auto">
  <div class="section-title">Atuadores — Servo Motor</div>
  <div class="servo-card" id="servo-card">
    <div class="servo-header">
      <div>
        <div class="servo-title">Porta / Portão</div>
        <div class="servo-subtitle">Controle de posição por duty cycle</div>
      </div>
      <div class="duty-badge" id="duty-badge">40</div>
    </div>

    <div class="door-visual">
      <div class="door-frame">
        <div class="door-panel" id="door-panel"></div>
      </div>
      <div class="door-status-text">Status: <span id="door-status-text">Fechado</span></div>
    </div>

    <div class="servo-presets">
      <button class="preset-btn active-preset" id="preset-close" onclick="applyPreset(40,'close')">🔒 Fechar porta</button>
      <button class="preset-btn" id="preset-open"  onclick="applyPreset(115,'open')">🔓 Abrir porta</button>
    </div>

    <div class="slider-wrap">
      <input type="range" id="servo-slider" min="40" max="115" step="1" value="40" oninput="onSlider(this.value)">
      <div class="slider-labels"><span>Fechado (40)</span><span>Aberto (115)</span></div>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
let mqttOnline = false;
let lastServo = 40;
let activePreset = 'close';

function toast(msg, color){
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.borderColor = color || '';
  t.classList.add('show');
  clearTimeout(t._t);
  t._t = setTimeout(()=> t.classList.remove('show'), 2200);
}

function setLed(color, action){
  const map = {red:'vermelho', yellow:'amarelo', blue:'azul'};
  const payload = map[color]+'_'+(action==='on'?'on':'off');
  fetch('/mqtt?cmd='+encodeURIComponent(payload))
    .then(r=>r.text()).then(()=>{
      const dot  = document.getElementById('dot-'+color);
      const card = document.getElementById('card-'+color);
      const bon  = document.getElementById('btn-'+color+'-on');
      const boff = document.getElementById('btn-'+color+'-off');
      if(action==='on'){
        dot.className  = 'led-indicator on-'+color;
        card.classList.add('active');
        bon.className  = 'toggle-btn selected-on';
        boff.className = 'toggle-btn';
        toast('✅ LED '+color+' ligado');
      } else {
        dot.className  = 'led-indicator';
        card.classList.remove('active');
        bon.className  = 'toggle-btn';
        boff.className = 'toggle-btn selected-off';
        toast('⭕ LED '+color+' desligado');
      }
    }).catch(()=> toast('❌ Erro de conexão','#ef4444'));
}

function updateDoor(val){
  val = parseInt(val);
  const pct = (val-40)/(115-40);
  const deg = -pct * 75;
  document.getElementById('door-panel').style.transform = 'perspective(200px) rotateY('+deg+'deg)';
  document.getElementById('duty-badge').textContent = val;
  document.getElementById('servo-slider').value = val;
  const txt = val >= 110 ? 'Aberto' : 'Fechado';
  document.getElementById('door-status-text').textContent = txt;
}

function applyPreset(val, preset){
  ['close','open'].forEach(p=>{
    document.getElementById('preset-'+p).classList.remove('active-preset');
  });
  document.getElementById('preset-'+preset).classList.add('active-preset');
  activePreset = preset;
  updateDoor(val);
  const payload = val>=110 ? 'porta_abrir' : 'porta_fechar';
  fetch('/mqtt?cmd='+encodeURIComponent(payload))
    .then(()=> toast('🚪 Porta '+(val<=45?'fechada':'aberta')));
}

function onSlider(val){
  val = parseInt(val);
  const snapped = val > 77 ? 115 : 40;
  updateDoor(snapped);
  document.getElementById('servo-slider').value = snapped;
  ['close','open'].forEach(p=>{
    document.getElementById('preset-'+p).classList.remove('active-preset');
  });
  document.getElementById(snapped>=110?'preset-open':'preset-close').classList.add('active-preset');
  clearTimeout(window._sliderT);
  window._sliderT = setTimeout(()=>{
    const payload = snapped>=110 ? 'porta_abrir' : 'porta_fechar';
    fetch('/mqtt?cmd='+encodeURIComponent(payload))
      .then(()=> toast('🚪 Porta '+(snapped>=110?'aberta':'fechada')));
  }, 300);
}

function flashVal(el){
  el.classList.add('updated');
  setTimeout(()=> el.classList.remove('updated'), 800);
}

function atualizaSensores(){
  fetch('/sensores').then(r=>r.json()).then(d=>{
    const ids = {temp:'s-temp', umid:'s-umid', luz:'s-luz', gas:'s-gas', dist:'s-dist'};
    const fmt = {
      temp: v=> v!=null? v+'°':'--',
      umid: v=> v!=null? v+'%':'--',
      luz:  v=> v!=null? v:'--',
      gas:  v=> v!=null? v:'--',
      dist: v=> v!=null? parseFloat(v).toFixed(1):'--'
    };
    Object.keys(ids).forEach(k=>{
      const el = document.getElementById(ids[k]);
      const nv = fmt[k](d[k]);
      if(el.textContent !== nv){ el.textContent = nv; flashVal(el); }
    });
    const online = d.temp != null;
    document.getElementById('mqtt-dot').className = 'mqtt-dot'+(online?' online':'');
    document.getElementById('mqtt-label').textContent = online?'MQTT conectado · broker.hivemq.com':'Aguardando dados do ESP32...';
  }).catch(()=>{});
}

setInterval(atualizaSensores, 3000);
atualizaSensores();
</script>
</body>
</html>"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path == '/mqtt':
            payload = params.get('cmd', [''])[0]
            if MQTT_OK and payload:
                mc.publish(TOPIC_PUB, payload)
            self.send_response(200)
            self.send_header('Content-Type','text/plain')
            self.send_header('Access-Control-Allow-Origin','*')
            self.end_headers()
            self.wfile.write(b'ok')

        elif parsed.path == '/sensores':
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_header('Access-Control-Allow-Origin','*')
            self.end_headers()
            self.wfile.write(json.dumps(sensores).encode())

        else:
            self.send_response(200)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML.encode('utf-8'))

if __name__ == '__main__':
    porta = 8080
    print(f"\n✅ Servidor rodando em: http://localhost:{porta}")
    print(f"   MQTT: {'conectado a ' + MQTT_BROKER if MQTT_OK else 'ERRO — rode: pip install paho-mqtt'}\n")
    HTTPServer(('', porta), Handler).serve_forever()