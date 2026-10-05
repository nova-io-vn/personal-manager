from datetime import date


def test_task_without_time_can_be_completed(client):
    created = client.post('/api/tasks', json={'title': 'Mua thuốc', 'note': 'Khi rảnh'}).json()
    assert created['due_date'] is None
    completed = client.patch(f"/api/tasks/{created['id']}", json={'completed': True})
    assert completed.status_code == 200
    assert completed.json()['completed'] is True


def test_debt_tracks_paid_amount_and_rejects_overpayment(client):
    created = client.post('/api/debts', json={'person': 'An', 'direction': 'OWED_BY_ME', 'amount': '100000', 'paid_amount': '25000'})
    assert created.status_code == 201
    assert created.json()['paid_amount'] == '25000.00'
    assert client.post('/api/debts', json={'person': 'An', 'direction': 'OWED_BY_ME', 'amount': '100', 'paid_amount': '101'}).status_code == 422


def test_journal_drawing_round_trip(client):
    response = client.put('/api/journals/2026-10-05', json={'mood': 'GOOD', 'content': 'Vẽ hôm nay', 'drawing_data': 'data:image/png;base64,abc', 'tag_ids': []})
    assert response.status_code == 200
    assert response.json()['drawing_data'] == 'data:image/png;base64,abc'
    assert client.get('/api/journals/2026-10-05').json()['drawing_data'] == 'data:image/png;base64,abc'


def test_personal_item_crud(client):
    created = client.post('/api/belongings', json={
        'name': 'Laptop', 'category': 'Điện tử', 'condition': 'GOOD',
        'purchase_price': '25000000', 'warranty_until': '2028-10-06',
    })
    assert created.status_code == 201
    item_id = created.json()['id']
    assert created.json()['purchase_price'] == '25000000.00'

    updated = client.patch(f'/api/belongings/{item_id}', json={'condition': 'NEEDS_SERVICE'})
    assert updated.status_code == 200
    assert updated.json()['condition'] == 'NEEDS_SERVICE'
    assert len(client.get('/api/belongings', params={'category': 'Điện tử'}).json()) == 1
    assert client.delete(f'/api/belongings/{item_id}').status_code == 204
