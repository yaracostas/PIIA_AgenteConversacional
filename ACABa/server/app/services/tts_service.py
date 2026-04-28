import os
from TTS.api import TTS


class TTSService:
    def __init__(self):
        """
        Inicializa el modelo de síntesis de voz.
        Utiliza GPU si está disponible y configurada.
        """
        use_gpu = os.getenv("USE_GPU", "false").lower() == "true"

        print(f"Inicializando TTS... GPU habilitada: {use_gpu}")

        # Modelo en español
        self.model_name = "tts_models/es/css10/vits"

        # Cargar el modelo
        self.tts = TTS(
            model_name=self.model_name,
            gpu=use_gpu
        )

    def synthesize(self, text: str, output_path: str) -> str:
        """
        Genera un archivo de audio a partir de un texto.

        Args:
            text (str): Texto a sintetizar.
            output_path (str): Ruta del archivo de salida.

        Returns:
            str: Ruta del archivo de audio generado.
        """
        if not text.strip():
            raise ValueError("El texto para TTS está vacío.")

        print(f"Generando audio para: {text}")

        self.tts.tts_to_file(
            text=text,
            file_path=output_path
        )
        #speaker="female"
        return output_path