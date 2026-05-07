import os
from faster_whisper import WhisperModel


class ASRService:
    def __init__(self):
        use_gpu = os.getenv("USE_GPU", "false").lower() == "true"

        if use_gpu:
            device = "cuda"
            compute_type = "float16"
        else:
            device = "cpu"
            compute_type = "int8"

        print(f"ASR usando device: {device}, compute_type: {compute_type}")

        self.model = WhisperModel(
            "base",
            device=device,
            compute_type=compute_type
        )

    def transcribe(self, audio_path: str) -> str:
        segments, _ = self.model.transcribe(
            audio_path,
            language="es",
            beam_size=1,
            vad_filter=True
        )

        return " ".join(s.text for s in segments).strip()