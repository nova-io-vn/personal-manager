from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class DeliveryResult:
    success: bool
    error: str | None = None


class TelegramService:
    def __init__(self, client: httpx.Client | None = None):
        self._client = client

    def send_text(self, token: str, chat_id: str, text: str) -> DeliveryResult:
        if not token or not chat_id:
            return DeliveryResult(False, "Telegram configuration is incomplete")
        try:
            client = self._client or httpx.Client(timeout=10.0)
            response = client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text},
            )
            if self._client is None:
                client.close()
            if response.status_code >= 400:
                return DeliveryResult(False, f"Telegram returned HTTP {response.status_code}")
            payload = response.json()
            if not payload.get("ok"):
                return DeliveryResult(False, "Telegram rejected the message")
            return DeliveryResult(True)
        except (httpx.HTTPError, ValueError):
            return DeliveryResult(False, "Unable to reach Telegram")
