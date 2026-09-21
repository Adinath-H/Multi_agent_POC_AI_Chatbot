"""Optional Groq vision helper.

Tesseract remains the local OCR fallback. When GROQ_API_KEY is configured,
this helper can also send an image to Groq's multimodal model for content and
layout understanding.
"""
import base64
from pathlib import Path

from groq import Groq

from ..config import GROQ_API_KEY, GROQ_VISION_MODEL


def describe_image(path: str) -> str:
    if not GROQ_API_KEY:
        return ""

    p = Path(path)
    suffix = p.suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    mime = mime_map.get(suffix, "image/jpeg")
    data = base64.b64encode(p.read_bytes()).decode("utf-8")

    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=GROQ_VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Describe this document/image for template analysis. "
                            "Identify visible text, headings, layout, colors, tables, "
                            "and other useful visual formatting details."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{data}"},
                    },
                ],
            }
        ],
        temperature=0.2,
        max_completion_tokens=2048,
    )
    return response.choices[0].message.content or ""
