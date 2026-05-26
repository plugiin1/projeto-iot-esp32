# 🏡 Projeto IoT: Automação Residencial

![Status](https://img.shields.io/badge/Status-Concluído-success)
![MicroPython](https://img.shields.io/badge/MicroPython-v1.28.0-blue)
![Simulador](https://img.shields.io/badge/Simulador-Wokwi-orange)
![MQTT](https://img.shields.io/badge/MQTT-HiveMQ-purple)
![Python](https://img.shields.io/badge/Painel-Python%203-yellow)

Este repositório contém o código-fonte e as configurações de um projeto acadêmico de Internet das Coisas (IoT). O sistema simula um ambiente residencial inteligente, integrando coleta de dados de sensores, atuação física, comunicação na nuvem, registro automatizado em banco de dados e um painel web local de controle em tempo real.

---

## 📋 Arquitetura do Sistema

O projeto foi construído utilizando uma arquitetura distribuída em quatro camadas:

1. **Edge (Microcontrolador):** Um ESP32 programado em MicroPython lê os sensores físicos, exibe dados em um painel OLED local, consulta o clima atual de Mogi das Cruzes via API e publica as métricas em um Broker MQTT. Também hospeda um servidor web interno para comandos diretos.

2. **Painel Web Local (`web.py`):** Um servidor Python rodando no PC do operador que serve uma interface web dark-mode com tema profissional. Comunica-se com o ESP32 via MQTT usando o mesmo broker, permitindo controle em tempo real dos atuadores e visualização dos sensores, sem depender da rede interna do simulador Wokwi.

3. **Servidor (Node-RED):** Atua como o "cérebro" da integração. Recebe os pacotes JSON via MQTT, gerencia o limite de taxa de requisições (Rate Limiting) e formata os dados para armazenamento.

4. **Banco de Dados (Nuvem):** Uma aplicação Google Apps Script (JavaScript) recebe via requisição HTTP GET os dados formatados pelo Node-RED e os insere sequencialmente em uma planilha do Google Sheets.

```
ESP32 (Wokwi)
    │
    ├─ MQTT publish ──► broker.hivemq.com ◄── MQTT subscribe ── web.py (PC)
    │                         │                                      │
    │                    Node-RED                             Navegador (localhost:8080)
    │                         │
    │                  Google Sheets (Apps Script)
    │
    └─ OLED Display (local)
```

---

## 🛠️ Hardware Simulado (Wokwi)

| Componente | Tipo | Função |
|---|---|---|
| ESP32 DevKit C v4 | Microcontrolador | Processamento central |
| SSD1306 (I2C) | Display OLED 128x64 | Painel de dados local |
| DHT22 | Sensor | Temperatura e umidade |
| LDR | Sensor analógico | Luminosidade ambiente |
| MQ2 | Sensor analógico | Detecção de gás |
| HC-SR04 | Sensor ultrassônico | Medição de distância |
| LED Vermelho | Atuador | Indicador de alarme de gás |
| LED Amarelo | Atuador | Iluminação da sala |
| LED Azul | Atuador | Status do ar-condicionado |
| Servo Motor | Atuador | Controle da porta/portão |

**Pinagem:**

| Componente | Pinos ESP32 |
|---|---|
| OLED SSD1306 | SCL→22, SDA→21 |
| DHT22 | DATA→15 |
| LDR | AO→34 |
| MQ2 | A0→35 |
| HC-SR04 | TRIG→5, ECHO→18 |
| LED Vermelho | 2 |
| LED Amarelo | 4 |
| LED Azul | 16 |
| Servo Motor | PWM→17 |

---

## 💻 Softwares, Protocolos e Dependências

**Linguagens:** MicroPython (ESP32) · Python 3 (painel local) · JavaScript (Node-RED / Apps Script)

**Protocolos:** MQTT (HiveMQ) · HTTP GET/POST · Wi-Fi STA · I2C · PWM

**Ferramentas:**
- VS Code + Extensão Wokwi
- Node-RED com node-red-dashboard
- Google Apps Script
- OpenWeather API
- paho-mqtt (dependência do painel local)

**Tópicos MQTT:**

| Tópico | Direção | Conteúdo |
|---|---|---|
| `residencia/sensores` | ESP32 → Nuvem | JSON com temp, umid, luz, gas, dist |
| `residencia/atuadores` | Nuvem → ESP32 | Comandos de texto (ex: `vermelho_on`) |

**Comandos MQTT disponíveis:**
`vermelho_on` · `vermelho_off` · `amarelo_on` · `amarelo_off` · `azul_on` · `azul_off` · `porta_abrir` · `porta_fechar`

---

## 🚀 Como Executar o Projeto

### 1. Simulação do ESP32 (Wokwi + VS Code)

1. Instale a extensão do Wokwi no VS Code.
2. Abra o `diagram.json` para visualizar o circuito.
3. Inicie a simulação — o ESP32 conectará automaticamente ao Wi-Fi virtual (`Wokwi-GUEST`) e começará a publicar no broker MQTT a cada 5 segundos.

### 2. Painel Web Local (`web.py`)

Pré-requisito: Python 3 instalado.

```bash
# Instalar dependência
pip install paho-mqtt

# Rodar o painel
python web.py
```

Acesse `http://localhost:8080` no navegador. O painel sobe imediatamente e o MQTT conecta em background — a bolinha no topo fica verde quando a conexão for estabelecida.

> **Nota:** Não renomeie o arquivo para `html.py` — conflita com o módulo interno do Python.

### 3. Node-RED (Dashboard e Integração)

1. Instale o Node-RED: `npm install -g node-red`
2. Importe o arquivo `flows.json` na interface do Node-RED.
3. O fluxo escutará o tópico `residencia/sensores` automaticamente.
4. Acesse o dashboard em `http://localhost:1880/ui`.

### 4. Banco de Dados (Google Sheets)

A planilha deve ter as colunas:

`Data/Hora` | `Tipo` | `Temp (°C)` | `Umid (%)` | `Luz (LDR)` | `Gás (MQ2)` | `Dist (cm)`

O Apps Script recebe os dados via HTTP GET a partir do Node-RED com rate limiting de 1 requisição a cada 15 segundos.

---

## 📁 Estrutura de Arquivos

```
IOT/
├── main.py                             # Firmware MicroPython do ESP32
├── web.py                              # Painel web local (Python 3 + MQTT)
├── diagram.json                        # Diagrama do simulador Wokwi
├── flows.json                          # Fluxo Node-RED
├── wokwi.toml                          # Configuração do simulador
├── ssd1306.py                          # Driver do display OLED
├── umqtt_simple.py                     # Cliente MQTT para MicroPython
├── requirements.txt                    # Dependências MicroPython
├── ESP32_GENERIC-20260406-v1.28.0.bin  # Firmware MicroPython
└── README.md
```

---

## 👨‍💻 Autor

Desenvolvido como **Requisito de Avaliação Acadêmica:**

**Felipe Barbosa Miranda**

---

<p align="center">
  <sub> Automação Residencial &copy; 2026 — Disciplina de Internet das Coisas (IoT)</sub>
</p>

