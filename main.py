import os 

import sys 

import sounddevice as sd 

import queue 

import numpy as np 

import json 

import pyttsx3 

from vosk import Model, KaldiRecognizer 

import gpt4all 

import RPi.GPIO as GPIO 

import time 

 

# ---------------- CONFIGURACIÓN ---------------- 

MODEL_PATH = "model" 

if not os.path.exists(MODEL_PATH): 

    print("❌ Modelo de voz no encontrado. Descárgalo desde https://alphacephei.com/vosk/models y descomprímelo en 'model'") 

    sys.exit(1) 

 

model = Model(MODEL_PATH) 

tts = pyttsx3.init() 

tts.setProperty('rate', 160) 

gpt = gpt4all.GPT4All("ggml-gpt4all-j-v1.3-groovy.bin") 

 

# Índices de los dos micrófonos Genius (ajusta según tu Pi) 

MIC_IZQ = 2 

MIC_DER = 3 

 

# Pines L298N 

IN3 = 17 

IN4 = 27 

IN1 = 24 

IN2 = 23 

 

GPIO.setmode(GPIO.BCM) 

GPIO.setup(IN1, GPIO.OUT) 

GPIO.setup(IN2, GPIO.OUT) 

GPIO.setup(IN3, GPIO.OUT) 

GPIO.setup(IN4, GPIO.OUT) 

 

def motor_adelante(): 

    GPIO.output(IN1, True) 

    GPIO.output(IN2, False) 

    GPIO.output(IN3, True) 

    GPIO.output(IN4, False) 

 

def motor_parar(): 

    GPIO.output(IN1, False) 

    GPIO.output(IN2, False) 

    GPIO.output(IN3, False) 

    GPIO.output(IN4, False) 

 

def motor_girar_izquierda(): 

    GPIO.output(IN1, False) 

    GPIO.output(IN2, True) 

    GPIO.output(IN3, True) 

    GPIO.output(IN4, False) 

 

def motor_girar_derecha(): 

    GPIO.output(IN1, True) 

    GPIO.output(IN2, False) 

    GPIO.output(IN3, False) 

    GPIO.output(IN4, True) 

 

# ---------------- FUNCIONES ---------------- 

def get_rms(data): 

    """Calcula el volumen RMS de un array de bytes""" 

    audio = np.frombuffer(data, dtype=np.int16) 

    return np.sqrt(np.mean(audio**2)) 

 

def escuchar(): 

    rec = KaldiRecognizer(model, 16000) 

 

    # Streams para los dos micrófonos 

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', 

                           channels=1, device=MIC_IZQ) as stream_izq, \ 

         sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', 

                           channels=1, device=MIC_DER) as stream_der: 

 

        print("🎤 Escuchando comandos y detectando dirección del sonido...") 

 

        while True: 

            data_izq, _ = stream_izq.read(8000) 

            data_der, _ = stream_der.read(8000) 

 

            # Calcular RMS 

            rms_izq = get_rms(data_izq) 

            rms_der = get_rms(data_der) 

 

            # Decidir dirección 

            diff = rms_izq - rms_der 

            if abs(diff) > 200:  # Umbral de diferencia 

                if diff > 0: 

                    motor_girar_izquierda() 

                    print("↩ Girando a la IZQUIERDA") 

                else: 

                    motor_girar_derecha() 

                    print("↪ Girando a la DERECHA") 

            else: 

                motor_adelante() 

                print("⬆ Avanzando") 

 

            # Reconocimiento de voz (solo con micrófono izquierdo por ejemplo) 

            if rec.AcceptWaveform(data_izq): 

                resultado = json.loads(rec.Result()) 

                comando = resultado.get('text', '').lower() 

                if comando: 

                    print(f"📢 Escuchado: {comando}") 

 

                    if "vencat detente" in comando: 

                        motor_parar() 

                        tts.say("Detenido") 

                        tts.runAndWait() 

 

                    elif "vencat" in comando and "detente" not in comando: 

                        motor_adelante() 

                        tts.say("Avanzando") 

                        tts.runAndWait() 

 

                    elif comando.startswith("pregunta"): 

                        pregunta = comando.replace("pregunta", "").strip() 

                        respuesta = gpt.chat_completion([{"role": "user", "content": pregunta}]) 

                        tts.say(respuesta) 

                        tts.runAndWait() 

 

if __name__ == "__main__": 

    try: 

        escuchar() 

    except KeyboardInterrupt: 

        print("\n🛑 Saliendo...") 

        GPIO.cleanup() 

 
 
