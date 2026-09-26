import pytest
from backend.app import app, in_memory_storage

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['DEBUG'] = False
    in_memory_storage.clear()
    with app.test_client() as client:
        yield client

def test_add_order_api_success(client):
    order_data = {
        "order_id": "API001", "item_name": "API Laptop", "quantity": 1, "customer_id": "APICUST001"
    }
    response = client.post('/api/orders', json=order_data)
    assert response.status_code == 201
    assert response.headers['Location'].endswith('/api/orders/API001')
    assert response.json == {
        "order_id": "API001",
        "item_name": "API Laptop",
        "quantity": 1,
        "customer_id": "APICUST001",
        "status": "pending",
    }


def test_add_order_api_invalid_payload_returns_400_with_error_message(client):
    response = client.post('/api/orders', json={
        "order_id": "BAD001", "item_name": "Broken", "quantity": -1, "customer_id": "C1"
    })

    assert response.status_code == 400
    assert response.json == {
        "error": "quantity must be a positive integer"
    }

def test_get_order_api_success(client):
    client.post('/api/orders', json={
        "order_id": "GET001", "item_name": "Test Item", "quantity": 1, "customer_id": "C1"
    })
    response = client.get('/api/orders/GET001')
    assert response.status_code == 200
    assert response.json == {
        "order_id": "GET001",
        "item_name": "Test Item",
        "quantity": 1,
        "customer_id": "C1",
        "status": "pending",
    }

def test_get_order_api_not_found(client):
    response = client.get('/api/orders/NONEXISTENT')
    assert response.status_code == 404

def test_update_order_status_api_success(client):
    client.post('/api/orders', json={
        "order_id": "UPDATE001", "item_name": "Test Item", "quantity": 1, "customer_id": "C1"
    })
    response = client.put('/api/orders/UPDATE001/status', json={"new_status": "shipped"})
    assert response.status_code == 200
    assert response.json['status'] == "shipped"


def test_update_order_status_api_unknown_order_returns_404(client):
    response = client.put('/api/orders/MISSING001/status', json={"new_status": "shipped"})

    assert response.status_code == 404
    assert response.json == {"error": "order not found"}


def test_update_order_status_api_unsupported_status_returns_400(client):
    client.post('/api/orders', json={
        "order_id": "UPDATE002", "item_name": "Test Item", "quantity": 1, "customer_id": "C1"
    })

    response = client.put('/api/orders/UPDATE002/status', json={"new_status": "frozen"})

    assert response.status_code == 400
    assert response.json["error"].startswith("status must be one of:")


def test_update_order_status_api_accepts_status_fallback_but_prefers_new_status(client):
    client.post('/api/orders', json={
        "order_id": "UPDATE003", "item_name": "Test Item", "quantity": 1, "customer_id": "C1"
    })

    fallback_response = client.put('/api/orders/UPDATE003/status', json={"status": "processing"})
    assert fallback_response.status_code == 200
    assert fallback_response.json["status"] == "processing"

    precedence_response = client.put(
        '/api/orders/UPDATE003/status',
        json={"status": "delivered", "new_status": "shipped"}
    )
    assert precedence_response.status_code == 200
    assert precedence_response.json["status"] == "shipped"

def test_list_all_orders_api_with_data(client):
    client.post('/api/orders', json={"order_id": "LST001", "item_name": "Item A", "quantity": 1, "customer_id": "C1"})
    client.post('/api/orders', json={"order_id": "LST002", "item_name": "Item B", "quantity": 2, "customer_id": "C2"})
    response = client.get('/api/orders')
    assert response.status_code == 200
    assert len(response.json) == 2


def test_list_all_orders_api_returns_empty_array_when_no_orders_exist(client):
    response = client.get('/api/orders')

    assert response.status_code == 200
    assert response.json == []

def test_list_orders_by_status_api_matching(client):
    client.post('/api/orders', json={"order_id": "S001", "item_name": "A", "quantity": 1, "customer_id": "C1", "status": "pending"})
    client.post('/api/orders', json={"order_id": "S002", "item_name": "B", "quantity": 2, "customer_id": "C2", "status": "shipped"})
    response = client.get('/api/orders?status=pending')
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['order_id'] == "S001"


def test_list_orders_by_status_api_invalid_status_returns_400(client):
    response = client.get('/api/orders?status=bogus')

    assert response.status_code == 400
    assert response.json["error"].startswith("status must be one of:")


def test_list_orders_by_status_api_empty_status_returns_400(client):
    response = client.get('/api/orders?status=')

    assert response.status_code == 400
    assert response.json == {"error": "status must be a non-empty string"}


def test_list_all_orders_api_limit_bounds_response_size(client):
    client.post('/api/orders', json={"order_id": "LIM001", "item_name": "Item A", "quantity": 1, "customer_id": "C1"})
    client.post('/api/orders', json={"order_id": "LIM002", "item_name": "Item B", "quantity": 2, "customer_id": "C2"})
    client.post('/api/orders', json={"order_id": "LIM003", "item_name": "Item C", "quantity": 3, "customer_id": "C3"})

    response = client.get('/api/orders?limit=2')

    assert response.status_code == 200
    assert len(response.json) == 2
    assert [order["order_id"] for order in response.json] == ["LIM001", "LIM002"]
