from app.services.asr_service import ASRService
from app.services.llm_service import LLMService
from app.services.tts_service import TTSService

import tempfile
import os
import wave


class Pipeline:
    def __init__(self):
        self.asr = ASRService()
        self.llm = LLMService()
        self.tts = TTSService()

    def run(self, input_audio: str, output_audio: str):
        text = self.asr.transcribe(input_audio)
        response = self.llm.generate(text)
        self.tts.synthesize(response, output_audio)

        return {
            "input_text": text,
            "response_text": response,
            "audio_path": output_audio,
        }
    

    def process_audio(self, audio_bytes: bytes):
        # guardar audio temporal

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            input_path = f.name

            with wave.open(f, "wb") as wf:
                wf.setnchannels(1)        # mono
                wf.setsampwidth(2)        # int16 = 2 bytes
                wf.setframerate(16000)    # 16kHz
                wf.writeframes(audio_bytes)

        output_path = input_path.replace(".wav", "_out.wav")

        try:
            #ASR
            text = self.asr.transcribe(input_path)

            #LLM
            response = self.llm.generate(text)

            #TTS
            self.tts.synthesize(response, output_path)

            #Leer audio generado
            with open(output_path, "rb") as f:
                tts_audio = f.read()

            result = {
                "input_text": text,
                "response_text": response,
            }

            return result, tts_audio

        finally:
            # limpiar archivos
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)