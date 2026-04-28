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
                    "content": "Eres un asistente útil y conciso. Responde en español."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.5,
            max_tokens=512,
        )

        return completion.choices[0].message.content.strip()