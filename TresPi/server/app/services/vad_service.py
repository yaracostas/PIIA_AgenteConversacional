import webrtcvad
import numpy as np


class VADService:
    def __init__(self, aggressiveness=2):
        self.vad = webrtcvad.Vad(aggressiveness)

    def analyze(self, audio_chunk: bytes, sample_rate=16000):
        """
        Devuelve información más rica del chunk:
        - vad_speech: decisión de WebRTC VAD
        - cms: energía media del audio
        - peak: pico máximo
        """
        vad_speech = self.vad.is_speech(audio_chunk, sample_rate)

        audio = np.frombuffer(audio_chunk, dtype=np.int16)

        if len(audio) == 0:
            rms = 0.0
            peak = 0
        else:
            rms = float(np.sqrt(np.mean(audio.astype(np.float32) ** 2)))
            peak = int(np.max(np.abs(audio)))

        return {
            "vad_speech": vad_speech,
            "rms": rms,
            "peak": peak,
        }