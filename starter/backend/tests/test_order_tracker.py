import pytest
from unittest.mock import Mock
from ..order_tracker import OrderTracker, VALID_ORDER_STATUSES
from ..in_memory_storage import InMemoryStorage

# --- Fixtures for Unit Tests ---

@pytest.fixture
def mock_storage():
    """
    Provides a mock storage object for tests.
    This mock will be configured to simulate various storage behaviors.
    """
    mock = Mock()
    # By default, mock get_order to return None (no order found)
    mock.get_order.return_value = None
    # By default, mock get_all_orders to return an empty dict
    mock.get_all_orders.return_value = {}
    return mock

@pytest.fixture
def order_tracker(mock_storage):
    """
    Provides an OrderTracker instance initialized with the mock_storage.
    """
    return OrderTracker(mock_storage)

def test_add_order_success(order_tracker, mock_storage):
    expected_order = {
        "order_id": "ORD001",
        "item_name": "Laptop",
        "quantity": 1,
        "customer_id": "CUST001",
        "status": "pending",
    }

    created = order_tracker.add_order(
        order_id="ORD001",
        item_name="Laptop",
        quantity=1,
        customer_id="CUST001"
    )

    assert created == expected_order

    mock_storage.save_order.assert_called_once()
    saved_order = mock_storage.save_order.call_args[0][1]
    assert saved_order == expected_order


@pytest.mark.parametrize(
    "existing_order, order_kwargs, expected_message",
    [
        (
            {
                "order_id": "ORD001",
                "item_name": "Mouse",
                "quantity": 1,
                "customer_id": "CUST001",
                "status": "pending",
            },
            {
                "order_id": "ORD001",
                "item_name": "Laptop",
                "quantity": 1,
                "customer_id": "CUST002",
            },
            "already exists",
        ),
        (
            None,
            {
                "order_id": "ORD002",
                "item_name": "Mouse",
                "quantity": 0,
                "customer_id": "CUST002",
            },
            "quantity must be a positive integer",
        ),
        (
            None,
            {
                "order_id": "ORD002B",
                "item_name": "Mouse",
                "quantity": "1",
                "customer_id": "CUST002",
            },
            "quantity must be a positive integer",
        ),
        (
            None,
            {
                "order_id": "ORD003",
                "item_name": "Desk",
                "quantity": 1,
                "customer_id": "",
            },
            "customer_id must be a non-empty string",
        ),
    ],
)
def test_add_order_invalid_inputs_raise(order_tracker, mock_storage, existing_order, order_kwargs, expected_message):
    mock_storage.get_order.return_value = existing_order

    with pytest.raises(ValueError, match=expected_message):
        order_tracker.add_order(**order_kwargs)


def test_add_order_returns_copy_and_does_not_expose_storage_state():
    storage = InMemoryStorage(max_orders=10)
    tracker = OrderTracker(storage)

    created = tracker.add_order("ORD010", "Laptop", 1, "CUST010")
    created["status"] = "shipped"
    created["customer_id"] = "MUTATED"

    stored_order = storage.get_order("ORD010")
    assert stored_order == {
        "order_id": "ORD010",
        "item_name": "Laptop",
        "quantity": 1,
        "customer_id": "CUST010",
        "status": "pending",
    }


def test_get_order_by_id_success(order_tracker, mock_storage):
    mock_storage.get_order.return_value = {
        "order_id": "ORD123",
        "item_name": "Keyboard",
        "quantity": 2,
        "customer_id": "C3",
        "status": "pending",
    }

    order = order_tracker.get_order_by_id("ORD123")
    assert order is not None
    assert order["order_id"] == "ORD123"
    assert order["item_name"] == "Keyboard"


def test_get_order_by_id_not_found_returns_none(order_tracker, mock_storage):
    mock_storage.get_order.return_value = None
    assert order_tracker.get_order_by_id("MISSING") is None


@pytest.mark.parametrize("invalid_order_id", ["", " ", None])
def test_get_order_by_id_empty_or_non_string_id_raises(order_tracker, invalid_order_id):
    with pytest.raises(ValueError, match="order_id"):
        order_tracker.get_order_by_id(invalid_order_id)


def test_update_order_status_success(order_tracker, mock_storage):
    original_order = {
        "order_id": "ORD200",
        "item_name": "Monitor",
        "quantity": 1,
        "customer_id": "C4",
        "status": "pending",
    }
    mock_storage.get_order.return_value = original_order

    updated = order_tracker.update_order_status("ORD200", "shipped")
    assert updated == {
        **original_order,
        "status": "shipped",
    }
    mock_storage.save_order.assert_called_once()
    saved_order = mock_storage.save_order.call_args[0][1]
    assert saved_order == {
        **original_order,
        "status": "shipped",
    }


def test_update_order_status_multiple_transitions_preserve_order_fields():
    storage = InMemoryStorage(max_orders=10)
    tracker = OrderTracker(storage)
    processing_status = VALID_ORDER_STATUSES[1]
    shipped_status = VALID_ORDER_STATUSES[2]

    tracker.add_order("ORD201", "Monitor", 1, "C5")

    processing_order = tracker.update_order_status("ORD201", processing_status)
    shipped_order = tracker.update_order_status("ORD201", shipped_status)

    assert processing_order == {
        "order_id": "ORD201",
        "item_name": "Monitor",
        "quantity": 1,
        "customer_id": "C5",
        "status": processing_status,
    }
    assert shipped_order == {
        "order_id": "ORD201",
        "item_name": "Monitor",
        "quantity": 1,
        "customer_id": "C5",
        "status": shipped_status,
    }
    assert storage.get_order("ORD201") == shipped_order


def test_update_order_status_nonexistent_order_raises(order_tracker, mock_storage):
    mock_storage.get_order.return_value = None

    with pytest.raises(LookupError, match="not found"):
        order_tracker.update_order_status("ORD404", "shipped")


def test_update_order_status_invalid_status_raises(order_tracker, mock_storage):
    mock_storage.get_order.return_value = {
        "order_id": "ORD300",
        "item_name": "Desk",
        "quantity": 1,
        "customer_id": "C9",
        "status": "pending",
    }

    with pytest.raises(ValueError, match="status"):
        order_tracker.update_order_status("ORD300", "unknown")


def test_update_order_status_empty_order_id_raises(order_tracker):
    with pytest.raises(ValueError, match="order_id"):
        order_tracker.update_order_status("", "shipped")


def test_list_all_orders(order_tracker, mock_storage):
    mock_storage.get_all_orders.return_value = {
        "A": {
            "order_id": "A",
            "item_name": "Item A",
            "quantity": 1,
            "customer_id": "C1",
            "status": "pending",
        },
        "B": {
            "order_id": "B",
            "item_name": "Item B",
            "quantity": 2,
            "customer_id": "C2",
            "status": "shipped",
        },
    }

    orders = order_tracker.list_all_orders()
    assert len(orders) == 2
    ids = {o["order_id"] for o in orders}
    assert ids == {"A", "B"}


def test_list_all_orders_returns_empty_list_when_storage_is_empty(order_tracker, mock_storage):
    mock_storage.get_all_orders.return_value = {}

    assert order_tracker.list_all_orders() == []


def test_list_all_orders_returns_copies_of_orders():
    storage = InMemoryStorage(max_orders=10)
    tracker = OrderTracker(storage)
    tracker.add_order("ORD400", "Phone", 2, "C400")

    orders = tracker.list_all_orders()
    orders[0]["status"] = "shipped"
    orders[0]["customer_id"] = "MUTATED"

    assert storage.get_order("ORD400") == {
        "order_id": "ORD400",
        "item_name": "Phone",
        "quantity": 2,
        "customer_id": "C400",
        "status": "pending",
    }


def test_list_orders_by_status(order_tracker, mock_storage):
    mock_storage.get_all_orders.return_value = {
        "A": {
            "order_id": "A",
            "item_name": "Item A",
            "quantity": 1,
            "customer_id": "C1",
            "status": "pending",
        },
        "B": {
            "order_id": "B",
            "item_name": "Item B",
            "quantity": 2,
            "customer_id": "C2",
            "status": "shipped",
        },
        "C": {
            "order_id": "C",
            "item_name": "Item C",
            "quantity": 3,
            "customer_id": "C3",
            "status": "shipped",
        },
    }

    shipped_orders = order_tracker.list_orders_by_status("shipped")
    assert len(shipped_orders) == 2
    assert all(order["status"] == "shipped" for order in shipped_orders)


def test_list_orders_by_status_returns_empty_list_when_no_orders_match(order_tracker, mock_storage):
    mock_storage.get_all_orders.return_value = {
        "A": {
            "order_id": "A",
            "item_name": "Item A",
            "quantity": 1,
            "customer_id": "C1",
            "status": "pending",
        },
        "B": {
            "order_id": "B",
            "item_name": "Item B",
            "quantity": 2,
            "customer_id": "C2",
            "status": "shipped",
        },
    }

    assert order_tracker.list_orders_by_status("delivered") == []


def test_list_orders_by_status_invalid_status_raises(order_tracker):
    with pytest.raises(ValueError, match="status"):
        order_tracker.list_orders_by_status("invalid")
