import webrtcvad


class VADService:
    def __init__(self, aggressiveness=2):
        self.vad = webrtcvad.Vad(aggressiveness)

    def is_speech(self, audio_chunk: bytes, sample_rate=16000):
        return self.vad.is_speech(audio_chunk, sample_rate)