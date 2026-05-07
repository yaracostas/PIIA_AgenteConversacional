import os
import re
import wave
import subprocess
from TTS.api import TTS
from num2words import num2words


class TTSService:
    def __init__(self):
        use_gpu = os.getenv("USE_GPU", "false").lower() == "true"

        print(f"Inicializando TTS... GPU habilitada: {use_gpu}")

        self.model_name = "tts_models/es/css10/vits"

        self.tts = TTS(
            model_name=self.model_name,
            gpu=use_gpu
        )

        # 1.0 = voz original
        # 1.15 = un poco más aguda
        # 1.25 = más tipo dibujo animado
        self.pitch_factor = float(os.getenv("TTS_PITCH_FACTOR", "1.45"))

    def normalize_text_for_tts(self, text: str) -> str:
        """
        Convierte números y símbolos frecuentes a texto para que el TTS los lea mejor.
        """

        text = text.replace("%", " por ciento")
        text = text.replace("€", " euros")
        text = text.replace("$", " dólares")

        # 1.000.000 -> 1000000
        text = re.sub(r"(?<=\d)\.(?=\d{3}\b)", "", text)

        # 3,5 -> tres coma cinco
        def replace_decimal(match):
            number = match.group(0).replace(",", ".")
            integer, decimal = number.split(".")
            return (
                num2words(int(integer), lang="es")
                + " coma "
                + " ".join(num2words(int(d), lang="es") for d in decimal)
            )

        text = re.sub(r"\b\d+[,.]\d+\b", replace_decimal, text)

        # números enteros
        def replace_integer(match):
            number = int(match.group(0))
            return num2words(number, lang="es")

        text = re.sub(r"\b\d+\b", replace_integer, text)

        return text

    def get_wav_sample_rate(self, wav_path: str) -> int:
        with wave.open(wav_path, "rb") as wav_file:
            return wav_file.getframerate()

    def make_voice_higher(self, input_path: str, output_path: str):
        """
        Sube el tono de la voz usando ffmpeg.
        Mantiene aproximadamente la duración original.
        """

        sample_rate = self.get_wav_sample_rate(input_path)

        # Para subir tono sin acelerar demasiado:
        # 1. asetrate cambia el tono y velocidad
        # 2. aresample vuelve al sample rate original
        # 3. atempo compensa la velocidad
        atempo = 1 / self.pitch_factor

        ffmpeg_filter = (
            f"asetrate={sample_rate}*{self.pitch_factor},"
            f"aresample={sample_rate},"
            f"atempo={atempo}"
        )

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", input_path,
                "-filter:a", ffmpeg_filter,
                output_path
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def synthesize(self, text: str, output_path: str) -> str:
        if not text.strip():
            raise ValueError("El texto para TTS está vacío.")

        text_for_tts = self.normalize_text_for_tts(text)

        print(f"Texto original: {text}")
        print(f"Texto normalizado para TTS: {text_for_tts}")

        temp_output_path = output_path.replace(".wav", "_normal.wav")

        self.tts.tts_to_file(
            text=text_for_tts,
            file_path=temp_output_path
        )

        if self.pitch_factor != 1.0:
            self.make_voice_higher(temp_output_path, output_path)

            try:
                os.remove(temp_output_path)
            except OSError:
                pass
        else:
            os.replace(temp_output_path, output_path)

        return output_path