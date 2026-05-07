import asyncio
import json
import websockets

from app.pipeline import Pipeline
from app.services.vad_service import VADService

HOST = "0.0.0.0"
PORT = 8770

pipeline = Pipeline()
vad = VADService()

# Parámetros de detección de turno
MIN_SPEECH_CHUNKS = 3
MIN_SILENCE_CHUNKS = 40
MIN_TURN_CHUNKS = 12

RMS_SPEECH_THRESHOLD = 350
RMS_SILENCE_THRESHOLD = 180


async def handler(websocket):
    print("Cliente conectado")

    await websocket.send(json.dumps({
        "type": "ready"
    }))

    audio_buffer = bytearray()

    speaking = False
    speech_streak = 0
    silence_streak = 0
    turn_chunks = 0

    try:
        async for message in websocket:

            # Audio recibido desde el navegador
            if isinstance(message, bytes):

                info = vad.analyze(message)

                vad_speech = info["vad_speech"]
                rms = info["rms"]

                chunk_has_speech = vad_speech or rms > RMS_SPEECH_THRESHOLD
                chunk_is_silence = (not vad_speech) and rms < RMS_SILENCE_THRESHOLD

                if chunk_has_speech:
                    speech_streak += 1
                    silence_streak = 0
                else:
                    silence_streak += 1

                # Inicio de turno
                if not speaking and speech_streak >= MIN_SPEECH_CHUNKS:
                    print("🎙️ Inicio de turno detectado")

                    speaking = True
                    audio_buffer.clear()
                    turn_chunks = 0

                    await websocket.send(json.dumps({
                        "type": "listening"
                    }))

                # Guardar audio mientras estamos en turno
                if speaking:
                    audio_buffer.extend(message)
                    turn_chunks += 1

                # Fin de turno
                if speaking and chunk_is_silence and silence_streak >= MIN_SILENCE_CHUNKS:

                    if turn_chunks < MIN_TURN_CHUNKS:
                        print("Turno descartado por ser demasiado corto")

                        audio_buffer.clear()
                        speaking = False
                        speech_streak = 0
                        silence_streak = 0
                        turn_chunks = 0
                        continue

                    print("Fin de turno detectado. Procesando...")


                    result, tts_audio = await asyncio.to_thread(
                        pipeline.process_audio,
                        bytes(audio_buffer)
                    )

                    audio_buffer.clear()
                    speaking = False
                    speech_streak = 0
                    silence_streak = 0
                    turn_chunks = 0

                    input_text = result.get("input_text", "")
                    response_text = result.get("response_text", "")

                    if not input_text.strip():
                        print("Turno vacío ignorado")

                        await websocket.send(json.dumps({
                            "type": "listening"
                        }))

                        continue

                    print("Usuario:", input_text)
                    print("TresPi:", response_text)

                    # Transcripción del usuario para que aparezca en la interfaz
                    await websocket.send(json.dumps({
                        "type": "user_transcript",
                        "text": input_text
                    }))

                    # Respuesta del LLM para que aparezca en la interfaz
                    await websocket.send(json.dumps({
                        "type": "assistant_text",
                        "text": response_text
                    }))

                    # Audio TTS
                    if tts_audio:
                        await websocket.send(json.dumps({
                            "type": "assistant_started"
                        }))

                        await websocket.send(tts_audio)

                        await websocket.send(json.dumps({
                            "type": "assistant_finished"
                        }))
                    else:
                        await websocket.send(json.dumps({
                            "type": "assistant_finished"
                        }))

            # Mensajes JSON recibidos desde el HTML
            else:
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    print("Mensaje no JSON recibido:", message)
                    continue

                message_type = data.get("type")

                if message_type in ["interrupt", "interrupted"]:
                    print("🛑 Interrupción recibida del cliente")

                    audio_buffer.clear()
                    speaking = False
                    speech_streak = 0
                    silence_streak = 0
                    turn_chunks = 0

                    await websocket.send(json.dumps({
                        "type": "interrupted"
                    }))

                elif message_type in ["stop", "stop_conversation"]:
                    print("Conversación detenida por el cliente")

                    audio_buffer.clear()
                    speaking = False
                    speech_streak = 0
                    silence_streak = 0
                    turn_chunks = 0

                    await websocket.send(json.dumps({
                        "type": "assistant_finished"
                    }))

                    break

    except websockets.exceptions.ConnectionClosed:
        print("Cliente desconectado")

    except Exception as e:
        print("Error en handler:", e)

        try:
            await websocket.send(json.dumps({
                "type": "error",
                "message": str(e)
            }))
        except Exception:
            pass


async def main():
    async with websockets.serve(handler, HOST, PORT, max_size=None):
        print(f"Servidor escuchando en ws://{HOST}:{PORT}")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())