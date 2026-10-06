import hashlib
from datetime import datetime
from decimal import Decimal

from app.services.ai_service import AIActionResult, AIService, ProposedAction
from app.services.telegram_service import DeliveryResult, TelegramService


def _configure(client):
    response = client.patch('/api/settings', json={
        'telegram_enabled': True,
        'telegram_bot_token': 'test-token',
        'telegram_chat_id': '12345',
    })
    assert response.status_code == 200
    return hashlib.sha256(b'personal-manager:test-token').hexdigest()


def test_telegram_task_button_completes_task(client, monkeypatch):
    secret = _configure(client)
    task = client.post('/api/tasks', json={'title': 'Gọi điện'}).json()
    monkeypatch.setattr(TelegramService, 'answer_callback', lambda *args, **kwargs: DeliveryResult(True))

    response = client.post('/api/telegram/webhook', headers={'X-Telegram-Bot-Api-Secret-Token': secret}, json={
        'callback_query': {'id': 'callback-1', 'data': f"task_done:{task['id']}", 'message': {'chat': {'id': 12345}}},
    })
    assert response.status_code == 200
    tasks = client.get('/api/tasks').json()
    assert next(item for item in tasks if item['id'] == task['id'])['completed'] is True


def test_telegram_expense_requires_confirmation_and_updates_balance(client, monkeypatch):
    secret = _configure(client)
    account = client.post('/api/accounts', json={'name': 'Ví Telegram', 'type': 'CASH', 'initial_balance': '100000'}).json()
    food = next(item for item in client.get('/api/transaction-categories').json() if item['name'] == 'Food')
    sent = []
    monkeypatch.setattr(TelegramService, 'send_text', lambda self, token, chat_id, text, reply_markup=None: sent.append((text, reply_markup)) or DeliveryResult(True))
    monkeypatch.setattr(TelegramService, 'answer_callback', lambda *args, **kwargs: DeliveryResult(True))

    proposed = client.post('/api/telegram/webhook', headers={'X-Telegram-Bot-Api-Secret-Token': secret}, json={
        'message': {'chat': {'id': 12345}, 'text': 'Đã ăn mất 50 nghìn'},
    })
    assert proposed.status_code == 200
    callback_data = sent[0][1]['inline_keyboard'][0][0]['callback_data']
    assert callback_data.startswith("draft_ok:")

    confirmed = client.post('/api/telegram/webhook', headers={'X-Telegram-Bot-Api-Secret-Token': secret}, json={
        'callback_query': {'id': 'callback-2', 'data': callback_data, 'message': {'chat': {'id': 12345}}},
    })
    assert confirmed.status_code == 200
    current = next(item for item in client.get('/api/accounts').json() if item['id'] == account['id'])
    assert current['current_balance'] == '50000.00'


def test_telegram_gemini_proposes_schedule_and_income_then_waits_for_confirmation(client, monkeypatch):
    secret = _configure(client)
    client.patch('/api/settings', json={'gemini_enabled': True, 'gemini_api_key': 'fake-key'})
    client.post('/api/accounts', json={'name': 'Ví chính', 'type': 'BANK', 'initial_balance': '0'})
    sent = []
    monkeypatch.setattr(TelegramService, 'send_text', lambda self, token, chat_id, text, reply_markup=None: sent.append((text, reply_markup)) or DeliveryResult(True))
    monkeypatch.setattr(TelegramService, 'answer_callback', lambda *args, **kwargs: DeliveryResult(True))
    monkeypatch.setattr(AIService, 'interpret_actions', lambda *args, **kwargs: AIActionResult(True, (
        ProposedAction(kind='schedule', title='Workshop', start_datetime=datetime(2026, 10, 7, 14), end_datetime=datetime(2026, 10, 7, 16)),
        ProposedAction(kind='income', title='Tiền thưởng', amount=Decimal('500000')),
    )))

    response = client.post('/api/telegram/webhook', headers={'X-Telegram-Bot-Api-Secret-Token': secret}, json={
        'message': {'chat': {'id': 12345}, 'text': 'Mai có workshop lúc 14h, cộng thêm 500k tiền thưởng'},
    })
    assert response.status_code == 200
    assert len(sent) == 2
    assert client.get('/api/schedules').json() == []
    assert client.get('/api/transactions').json() == []

    for _, markup in list(sent):
        callback_data = markup['inline_keyboard'][0][0]['callback_data']
        confirmed = client.post('/api/telegram/webhook', headers={'X-Telegram-Bot-Api-Secret-Token': secret}, json={
            'callback_query': {'id': callback_data, 'data': callback_data, 'message': {'chat': {'id': 12345}}},
        })
        assert confirmed.status_code == 200
    assert client.get('/api/schedules').json()[0]['title'] == 'Workshop'
    assert client.get('/api/transactions').json()[0]['amount'] == '500000.00'


def test_telegram_menu_and_calendar_commands_render_inline_choices(client, monkeypatch):
    secret = _configure(client)
    sent = []
    monkeypatch.setattr(TelegramService, 'send_text', lambda self, token, chat_id, text, reply_markup=None: sent.append((text, reply_markup)) or DeliveryResult(True))

    for command in ('/menu', '/calendar', '/fee'):
        response = client.post('/api/telegram/webhook', headers={'X-Telegram-Bot-Api-Secret-Token': secret}, json={
            'message': {'chat': {'id': 12345}, 'text': command},
        })
        assert response.status_code == 200
    assert any(markup and markup.get('inline_keyboard') for _, markup in sent)


def test_telegram_rejects_unsigned_webhook(client):
    _configure(client)
    assert client.post('/api/telegram/webhook', json={'message': {'chat': {'id': 12345}, 'text': '/tasks'}}).status_code == 403
