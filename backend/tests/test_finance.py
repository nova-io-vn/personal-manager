from datetime import date


def category_id(client, name: str) -> int:
    return next(item["id"] for item in client.get("/api/transaction-categories").json() if item["name"] == name)


def test_health_and_default_categories(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    names = {item["name"] for item in client.get("/api/transaction-categories").json()}
    assert {"Food", "Salary", "Other Income"}.issubset(names)


def test_balance_consistency_through_crud(client):
    account = client.post("/api/accounts", json={"name": "Main", "type": "BANK", "initial_balance": "100.00"}).json()
    account_id = account["id"]
    income = client.post("/api/transactions", json={
        "account_id": account_id, "category_id": category_id(client, "Salary"), "type": "INCOME",
        "amount": "50.25", "transaction_date": str(date.today()),
    }).json()
    assert client.get(f"/api/accounts/{account_id}").json()["current_balance"] == "150.25"

    updated = client.patch(f"/api/transactions/{income['id']}", json={"amount": "20.25"}).json()
    assert updated["amount"] == "20.25"
    assert client.get(f"/api/accounts/{account_id}").json()["current_balance"] == "120.25"

    assert client.delete(f"/api/transactions/{income['id']}").status_code == 204
    assert client.get(f"/api/accounts/{account_id}").json()["current_balance"] == "100.00"


def test_expense_transfer_filter_and_validation(client):
    first = client.post("/api/accounts", json={"name": "Cash", "type": "CASH"}).json()
    second = client.post("/api/accounts", json={"name": "Wallet", "type": "EWALLET", "initial_balance": "200"}).json()
    expense = client.post("/api/transactions", json={
        "account_id": first["id"], "category_id": category_id(client, "Food"), "type": "EXPENSE",
        "amount": "10", "transaction_date": "2026-01-01",
    })
    assert expense.status_code == 201
    transfer = client.post("/api/transactions", json={
        "account_id": second["id"], "related_account_id": first["id"], "type": "TRANSFER",
        "amount": "50", "transaction_date": "2026-01-02",
    })
    assert transfer.status_code == 201
    assert client.get(f"/api/accounts/{first['id']}").json()["current_balance"] == "40.00"
    assert client.get(f"/api/accounts/{second['id']}").json()["current_balance"] == "150.00"
    assert len(client.get("/api/transactions", params={"type": "EXPENSE"}).json()) == 1
    assert client.post("/api/transactions", json={
        "account_id": first["id"], "category_id": category_id(client, "Food"), "type": "EXPENSE",
        "amount": "0", "transaction_date": "2026-01-01",
    }).status_code == 422


def test_budget_crud(client):
    food_id = category_id(client, "Food")
    response = client.post("/api/budgets", json={
        "category_id": food_id, "amount": "300", "start_date": "2026-01-01", "end_date": "2026-01-31",
    })
    assert response.status_code == 201
    budget_id = response.json()["id"]
    assert client.patch(f"/api/budgets/{budget_id}", json={"amount": "350"}).json()["amount"] == "350.00"
    assert client.delete(f"/api/budgets/{budget_id}").status_code == 204
