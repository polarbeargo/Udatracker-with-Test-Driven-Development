from ..in_memory_storage import InMemoryStorage


def test_in_memory_storage_evicts_oldest_orders_when_limit_is_reached():
    storage = InMemoryStorage(max_orders=2)
    storage.save_order("A", {"order_id": "A", "status": "pending"})
    storage.save_order("B", {"order_id": "B", "status": "pending"})
    storage.save_order("C", {"order_id": "C", "status": "pending"})

    assert storage.get_order("A") is None
    assert storage.get_order("B") is not None
    assert storage.get_order("C") is not None
    assert len(storage.get_all_orders()) == 2
