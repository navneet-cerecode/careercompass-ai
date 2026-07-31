"""
Groq Client.
"""

import json

from groq import Groq

from core.config import settings


class GroqClient:
    def __init__(self):

        if settings.groq_api_key is None:
            raise RuntimeError("Missing GROQ_API_KEY.")

        self.client = Groq(
            api_key=settings.groq_api_key.get_secret_value(),
        )

        self.model = settings.groq_model

        self.temperature = settings.temperature

        self.max_tokens = settings.max_tokens

    def chat(
        self,
        prompt: str,
    ) -> dict:

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return json.loads(response.choices[0].message.content)
