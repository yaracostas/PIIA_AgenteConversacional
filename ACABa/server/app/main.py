import asyncio
import json
import websockets

from app.pipeline import Pipeline
from app.services.vad_service import VADService

HOST = "0.0.0.0"
PORT = 8770

pipeline = Pipeline()
vad = VADService()

# Parámetros
SILENCE_LIMIT = 15  # número de chunks de silencio antes de procesar (ajustar si hace falta)



async def handler(websocket):
    print("Cliente conectado")

    await websocket.send(json.dumps({"type": "ready"}))

    audio_buffer = bytearray()
    silence_counter = 0
    speaking = False

    try:
        async for message in websocket:
            if isinstance(message, bytes):

                is_speech = vad.is_speech(message)

                if is_speech:
                    if not speaking:
                        print("🎙️ Detectada voz")
                    speaking = True
                    silence_counter = 0
                    audio_buffer.extend(message)

                else:
                    if speaking:
                        silence_counter += 1
                        audio_buffer.extend(message)

                # detectar fin de turno
                if speaking and silence_counter > SILENCE_LIMIT:
                    print("Fin de turno detectado. Procesando...")

                    result, tts_audio = await asyncio.to_thread(
                        pipeline.process_audio,
                        bytes(audio_buffer)
                    )

                    # reset
                    audio_buffer.clear()
                    silence_counter = 0
                    speaking = False

                    # enviar respuesta
                    await websocket.send(json.dumps({
                        "type": "asr.final",
                        "text": result["input_text"]
                    }))

                    await websocket.send(json.dumps({
                        "type": "llm.final",
                        "text": result["response_text"]
                    }))

                    await websocket.send(json.dumps({"type": "tts.start"}))
                    await websocket.send(tts_audio)
                    await websocket.send(json.dumps({"type": "tts.end"}))

            else:
                # ignoramos mensajes JSON (ya no usamos start/stop)
                pass

    except websockets.exceptions.ConnectionClosed:
        print("Cliente desconectado")


async def main():
    async with websockets.serve(handler, HOST, PORT, max_size=None):
        print(f"Servidor escuchando en ws://{HOST}:{PORT}")
        await asyncio.Future()



if __name__ == "__main__":
    asyncio.run(main())