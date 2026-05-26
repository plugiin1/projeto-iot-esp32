# 🏡 Projeto IoT: Automação Residencial

![Status](https://img.shields.io/badge/Status-Concluído-success)
![MicroPython](https://img.shields.io/badge/MicroPython-v1.28.0-blue)
![Simulador](https://img.shields.io/badge/Simulador-Wokwi-orange)

Este repositório contém o código-fonte e as configurações de um projeto acadêmico de Internet das Coisas (IoT). O sistema simula um ambiente residencial inteligente, integrando coleta de dados de sensores, atuação física, comunicação na nuvem e registro automatizado em banco de dados.

---

## 📋 Arquitetura do Sistema

O projeto foi construído utilizando uma arquitetura distribuída, garantindo leveza no processamento do microcontrolador e robustez no servidor de aplicação.

1. **Edge (Microcontrolador):** Um ESP32 programado em MicroPython é responsável por ler os sensores físicos, exibir dados em um painel OLED local, consultar o clima atual de Mogi das Cruzes via API e publicar as métricas em um Broker MQTT. Ele também hospeda um Servidor Web local para comandos diretos.
2. **Servidor (Node-RED):** Atua como o "cérebro" da integração. Recebe os pacotes JSON via MQTT, gerencia o limite de taxa de requisições (Rate Limiting) e formata os dados para armazenamento.
3. **Banco de Dados (Nuvem):** Uma aplicação Google Apps Script (JavaScript) recebe via requisição HTTP GET os dados formatados pelo Node-RED e os insere sequencialmente em uma planilha do Google Sheets.

---

## 🛠️ Hardware Simulado (Wokwi)

A maquete eletrônica foi montada e testada no simulador Wokwi com os seguintes componentes:

* **Placa Base:** ESP32
* **Display:** OLED SSD1306 (I2C) para interface visual local em grid.
* **Sensores:**
    * `DHT22`: Temperatura e Umidade.
    * `LDR`: Luminosidade ambiente.
    * `MQ2`: Detecção de nível de gases (Sistema de Alarme).
    * `HC-SR04`: Sensor Ultrassônico para medição de distância.
* **Atuadores:**
    * `LED Vermelho`: Indicador de status de Gás.
    * `LED Amarelo`: Iluminação da Sala.
    * `LED Azul`: Status do Ar Condicionado.
    * `Servo Motor`: Controle da porta/portão de acesso.

---

## 💻 Softwares e Protocolos Utilizados

* **Linguagens:** Python (MicroPython) e JavaScript.
* **Protocolos:** MQTT (Publish/Subscribe via HiveMQ), HTTP (GET/POST), e Wi-Fi (STA_IF).
* **Ferramentas:**
    * `VS Code` + Extensão do Wokwi
    * `Node-RED` para o fluxo de dados e Dashboard UI.
    * `Google Apps Script` para a API de gravação em nuvem.
    * `OpenWeather API` para captura climática externa.

---

## 🚀 Como Executar o Projeto

### 1. Simulação do ESP32
1. Instale a extensão do Wokwi no VS Code.
2. Abra o arquivo `diagram.json` para visualizar o circuito.
3. Execute o ambiente de simulação. O ESP32 conectará automaticamente ao Wi-Fi virtual (`Wokwi-GUEST`) e iniciará a publicação no Broker MQTT.

### 2. Node-RED (Dashboard e Integração)
1. Importe o arquivo `flows.json` (disponível neste repositório) para o seu ambiente Node-RED local.
2. O fluxo configurado escutará automaticamente o tópico `residencia/sensores`.
3. Acesse a interface visual (Dashboard) através de `http://localhost:1880/ui`.

### 3. Banco de Dados (Google Sheets)
A estrutura enviada pelo Node-RED espera uma planilha configurada com as seguintes colunas:
`Data/Hora` | `Tipo` | `Temp (°C)` | `Umid (%)` | `Luz (LDR)` | `Gás (MQ2)` | `Dist (cm)`

---

## 👨‍💻 Autor

Felipe Barbosa Miranda