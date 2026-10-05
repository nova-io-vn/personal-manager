from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class DeliveryResult:
    success: bool
    error: str | None = None


class TelegramService:
    def __init__(self, client: httpx.Client | None = None):
        self._client = client

    def send_text(self, token: str, chat_id: str, text: str, reply_markup: dict | None = None) -> DeliveryResult:
        if not token or not chat_id:
            return DeliveryResult(False, "Telegram configuration is incomplete")
        try:
            client = self._client or httpx.Client(timeout=10.0)
            response = client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text, **({"reply_markup": reply_markup} if reply_markup else {})},
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

    def set_webhook(self, token: str, url: str, secret_token: str) -> DeliveryResult:
        return self._call(token, "setWebhook", {"url": url, "secret_token": secret_token, "drop_pending_updates": False})

    def answer_callback(self, token: str, callback_query_id: str, text: str) -> DeliveryResult:
        return self._call(token, "answerCallbackQuery", {"callback_query_id": callback_query_id, "text": text})

    def _call(self, token: str, method: str, payload: dict) -> DeliveryResult:
        if not token:
            return DeliveryResult(False, "Telegram configuration is incomplete")
        try:
            client = self._client or httpx.Client(timeout=10.0)
            response = client.post(f"https://api.telegram.org/bot{token}/{method}", json=payload)
            if self._client is None:
                client.close()
            if response.status_code >= 400 or not response.json().get("ok"):
                return DeliveryResult(False, f"Telegram returned HTTP {response.status_code}")
            return DeliveryResult(True)
        except (httpx.HTTPError, ValueError):
            return DeliveryResult(False, "Unable to reach Telegram")
