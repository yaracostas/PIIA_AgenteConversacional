import asyncio
import json
import websockets
import sounddevice as sd
import numpy as np

SAMPLE_RATE = 16000
CHUNK_SIZE = 320  # 20 ms a 16 kHz

# Estado global
assistant_speaking = False
stop_playback = False
interrupt_sent = False

# Umbral de volumen para detectar que el usuario habla encima del TTS
INTERRUPT_VOLUME_THRESHOLD = 6000
INTERRUPT_MIN_CHUNKS = 8
TTS_GRACE_CHUNKS = 20

interrupt_streak = 0
tts_chunks_since_start = 0


async def send_audio(ws):
    global assistant_speaking, stop_playback, interrupt_sent

    print("🎙️ Cliente listo. Habla cuando quieras...")

    loop = asyncio.get_running_loop()

    def callback(indata, frames, time, status):
        global assistant_speaking, stop_playback, interrupt_sent, interrupt_streak, tts_chunks_since_start

        if status:
            print("⚠️", status)

        audio_chunk = np.squeeze(indata)

        # float32 [-1,1] -> int16
        audio_chunk = (audio_chunk * 32767).clip(-32768, 32767).astype(np.int16)
        audio_bytes = audio_chunk.tobytes()

        volume = np.abs(audio_chunk).mean()

        # Si el asistente está hablando y el usuario empieza a hablar:
        if assistant_speaking:
            if volume > INTERRUPT_VOLUME_THRESHOLD:
                stop_playback = True

                if not interrupt_sent:
                    interrupt_sent = True
                    print("🛑 Interrumpiendo al asistente...")

                    asyncio.run_coroutine_threadsafe(
                        ws.send(json.dumps({"type": "interrupt"})),
                        loop
                    )

                # Este chunk ya cuenta como inicio del nuevo turno del usuario
                asyncio.run_coroutine_threadsafe(
                    ws.send(audio_bytes),
                    loop
                )

            return

        # Si el asistente NO está hablando, enviamos audio normal
        asyncio.run_coroutine_threadsafe(
            ws.send(audio_bytes),
            loop
        )

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=CHUNK_SIZE,
        callback=callback,
    ):
        await asyncio.Future()


async def receive(ws):
    global assistant_speaking, stop_playback, interrupt_sent, interrupt_streak, tts_chunks_since_start

    while True:
        msg = await ws.recv()

        if isinstance(msg, bytes):
            print("🎧 Reproduciendo respuesta...")

            assistant_speaking = True
            stop_playback = False
            interrupt_sent = False
            interrupt_streak = 0
            tts_chunks_since_start = 0

            audio = np.frombuffer(msg, dtype=np.int16)

            # El TTS que usáis parece salir a 22050 Hz
            sd.play(audio, samplerate=22050)

            while True:
                await asyncio.sleep(0.05)

                if stop_playback:
                    sd.stop()
                    print("✅ Respuesta cortada. Escuchando nuevo turno...")
                    break

                # Si ya terminó la reproducción
                try:
                    if not sd.get_stream().active:
                        break
                except Exception:
                    break

            assistant_speaking = False
            stop_playback = False
            interrupt_sent = False

        else:
            data = json.loads(msg)

            if data.get("type") == "ready":
                print("✅ Servidor listo")

            elif data.get("type") == "asr.final":
                print(f"👤 Usuario: {data['text']}")

            elif data.get("type") == "llm.final":
                print(f"🦔 Erizo: {data['text']}")

            elif data.get("type") == "tts.start":
                print("🔊 Empieza TTS")

            elif data.get("type") == "tts.end":
                print("🔇 Termina TTS")

            elif data.get("type") == "interrupted":
                print("📩 Servidor ha recibido la interrupción")

            else:
                print("Servidor:", data)


async def main():
    uri = "ws://localhost:8770"

    async with websockets.connect(uri, max_size=None) as ws:
        print("🔌 Conectado al servidor")

        await asyncio.gather(
            send_audio(ws),
            receive(ws)
        )


if __name__ == "__main__":
    asyncio.run(main())