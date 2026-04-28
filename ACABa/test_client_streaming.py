import asyncio
import websockets
import sounddevice as sd
import numpy as np

SAMPLE_RATE = 16000
CHUNK_SIZE = 320   # 20 ms exactos


async def send_audio(ws):
    print("🎙️ Habla...")

    loop = asyncio.get_running_loop()

    def callback(indata, frames, time, status):
        if status:
            print("⚠️", status)

        audio_chunk = np.squeeze(indata)

        # float32 → int16
        audio_chunk = (audio_chunk * 32767).clip(-32768, 32767).astype(np.int16)

        asyncio.run_coroutine_threadsafe(
            ws.send(audio_chunk.tobytes()),
            loop
        )

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=CHUNK_SIZE,
        callback=callback,
    ):
        await asyncio.Future()  # mantener abierto


async def receive(ws):
    while True:
        msg = await ws.recv()

        if isinstance(msg, bytes):
            print("🎧 Reproduciendo respuesta...")

            # convertir bytes → numpy int16
            audio = np.frombuffer(msg, dtype=np.int16)

            # reproducir (16kHz mono)
            sd.play(audio, samplerate=22050) #, blocking=False
            sd.wait()

        else:
            print("Servidor:", msg)


async def main():
    uri = "ws://localhost:8770"

    async with websockets.connect(uri, max_size=None) as ws:
        print("Conectado al servidor")

        await asyncio.gather(
            send_audio(ws),
            receive(ws)
        )


if __name__ == "__main__":
    asyncio.run(main())