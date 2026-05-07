import os
from groq import Groq


class LLMService:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY no está definida")

        self.client = Groq(api_key=api_key.strip())

    def generate(self, text: str) -> str:
        completion = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres TresPi, un agente conversacional por voz en español. "
                        "Tu nombre es TresPi. "
                        "Si el usuario te pregunta cómo te llamas, responde claramente que te llamas TresPi. "
                        "Eres un asistente conversacional en español. "
                        "Responde de forma breve, natural y directa. "
                        "No des explicaciones largas salvo que el usuario lo pida. "
                        "Máximo 2 o 3 frases."
                    )
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.4,
            max_tokens=120,
        )

        return completion.choices[0].message.content.strip()