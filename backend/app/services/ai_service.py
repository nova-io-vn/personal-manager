import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal
from typing import Callable, Protocol

from google import genai
from google.genai import types
from pydantic import BaseModel, Field, TypeAdapter, model_validator


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


class ProposedAction(BaseModel):
    kind: Literal["schedule", "expense", "income", "task"]
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    amount: Decimal | None = Field(default=None, gt=0)
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    category: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def validate_action(self):
        if self.kind == "schedule":
            if self.start_datetime is None:
                raise ValueError("schedule action requires start_datetime")
            if self.end_datetime is None:
                raise ValueError("schedule action requires end_datetime")
            if self.end_datetime <= self.start_datetime:
                raise ValueError("schedule end must be after start")
        if self.kind in {"expense", "income"} and self.amount is None:
            raise ValueError("finance action requires amount")
        return self


@dataclass(frozen=True)
class AIActionResult:
    success: bool
    actions: tuple[ProposedAction, ...] = ()
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

    def interpret_actions(
        self,
        api_key: str,
        model: str,
        message: str,
        now: datetime,
        context: dict,
    ) -> AIActionResult:
        """Convert natural language into drafts; callers must still ask for confirmation."""
        if not api_key or not model:
            return AIActionResult(False, error="Gemini chưa được cấu hình.")
        client = self.client_factory(api_key)
        try:
            response = client.models.generate_content(
                model=model,
                contents=(
                    f"Thời gian hiện tại: {now.isoformat()}\n"
                    f"Tin nhắn: {message}\n"
                    "Dữ liệu chọn tài khoản/danh mục:\n"
                    f"{json.dumps(context, ensure_ascii=False)}"
                ),
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "Bạn chuyển tin nhắn tiếng Việt thành tối đa 5 hành động Personal Manager. "
                        "Chỉ dùng kind schedule, expense, income hoặc task. Không tự suy diễn số tiền hay thời gian "
                        "nếu người dùng không nêu đủ. Với lịch, dùng múi giờ trong thời gian hiện tại; nếu thiếu giờ "
                        "thì tạo task thay vì schedule. Trả về duy nhất mảng JSON. Đây chỉ là bản nháp chờ xác nhận."
                    ),
                    temperature=0,
                    max_output_tokens=1200,
                    response_mime_type="application/json",
                    response_schema=list[ProposedAction],
                ),
            )
            raw = response.parsed if getattr(response, "parsed", None) is not None else json.loads(response.text or "[]")
            actions = TypeAdapter(list[ProposedAction]).validate_python(raw)
            if not actions:
                return AIActionResult(False, error="Không nhận ra hành động cần tạo.")
            return AIActionResult(True, tuple(actions[:5]))
        except Exception:
            return AIActionResult(False, error="Gemini chưa hiểu yêu cầu này. Hãy thêm số tiền hoặc thời gian cụ thể.")
        finally:
            client.close()
