import hashlib

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
    assert callback_data == f"expense_confirm:{account['id']}:{food['id']}:50000"

    confirmed = client.post('/api/telegram/webhook', headers={'X-Telegram-Bot-Api-Secret-Token': secret}, json={
        'callback_query': {'id': 'callback-2', 'data': callback_data, 'message': {'chat': {'id': 12345}}},
    })
    assert confirmed.status_code == 200
    current = next(item for item in client.get('/api/accounts').json() if item['id'] == account['id'])
    assert current['current_balance'] == '50000.00'


def test_telegram_rejects_unsigned_webhook(client):
    _configure(client)
    assert client.post('/api/telegram/webhook', json={'message': {'chat': {'id': 12345}, 'text': '/tasks'}}).status_code == 403
