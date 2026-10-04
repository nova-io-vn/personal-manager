import json
from dataclasses import dataclass
from typing import Callable, Protocol

from google import genai
from google.genai import types


SYSTEM_INSTRUCTION = """Bạn là trợ lý Personal Manager. Chỉ phân tích dữ liệu JSON được cung cấp.
Không bịa dữ liệu còn thiếu, không chẩn đoán y khoa, không tuyên bố đã sửa dữ liệu.
Trả lời ngắn gọn, hữu ích bằng tiếng Việt. Các chỉ số sức khỏe chỉ mang tính thông tin."""


class GeminiClient(Protocol):
    @property
    def models(self): ...
    def close(self) -> None: ...


@dataclass(frozen=True)
class AIResult:
    success: bool
    text: str = ""
    error: str = ""


class AIService:
    def __init__(self, client_factory: Callable[[str], GeminiClient] | None = None):
        self.client_factory = client_factory or (lambda api_key: genai.Client(api_key=api_key))

    def generate(self, api_key: str, model: str, question: str, context: dict) -> AIResult:
        if not api_key or not model:
            return AIResult(False, error="Gemini chưa được cấu hình.")
        client = self.client_factory(api_key)
        try:
            response = client.models.generate_content(
                model=model,
                contents=f"Câu hỏi: {question}\n\nDữ liệu ứng dụng:\n{json.dumps(context, ensure_ascii=False)}",
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.2,
                    max_output_tokens=1000,
                ),
            )
            text = (response.text or "").strip()
            if not text:
                return AIResult(False, error="Gemini không trả về nội dung.")
            return AIResult(True, text=text)
        except Exception:
            return AIResult(False, error="Không thể kết nối Gemini. Hãy kiểm tra API key, model và kết nối mạng.")
        finally:
            client.close()
