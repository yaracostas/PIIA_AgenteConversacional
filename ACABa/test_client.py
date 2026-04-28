import asyncio
import websockets
import json


async def test():
    uri = "ws://localhost:8770"

    # ⚠️ Pon aquí un audio WAV corto (2–5 segundos)
    with open("upslasprisas.wav", "rb") as f:
        audio_data = f.read()

    async with websockets.connect(uri, max_size=None) as ws:
        print("Conectado al servidor")

        # Mensaje inicial
        msg = await ws.recv()
        print("Servidor:", msg)

        # Iniciar grabación
        await ws.send(json.dumps({"type": "start"}))

        # Enviar audio
        await ws.send(audio_data)

        # Finalizar
        await ws.send(json.dumps({"type": "stop"}))

        print("Audio enviado, esperando respuesta...\n")

        while True:
            response = await ws.recv()

            if isinstance(response, bytes):
                # Guardar audio TTS
                with open("response.wav", "wb") as f:
                    f.write(response)
                print("🎧 Audio recibido -> response.wav")
                break
            else:
                print("Servidor:", response)


asyncio.run(test())