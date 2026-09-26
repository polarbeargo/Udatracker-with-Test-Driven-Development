# This module contains the OrderTracker class, which encapsulates the core
# business logic for managing orders.

from threading import RLock

# Shared status values keep the tracker and tests aligned on one source of truth.
VALID_ORDER_STATUSES = (
    "pending",
    "processing",
    "shipped",
    "delivered",
    "cancelled",
)


class OrderTracker:
    """
    Manages customer orders, providing functionalities to add, update,
    and retrieve order information.
    """
    def __init__(self, storage):
        required_methods = ['save_order', 'get_order', 'get_all_orders']
        for method in required_methods:
            if not hasattr(storage, method) or not callable(getattr(storage, method)):
                raise TypeError(f"Storage object must implement a callable '{method}' method.")
        self.storage = storage
        # Serialize storage access so create/update/list operations stay consistent.
        self._lock = RLock()
        self._valid_statuses = set(VALID_ORDER_STATUSES)

    @staticmethod
    def _validate_non_empty_str(value, field_name: str):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")

    @staticmethod
    def _validate_quantity(quantity):
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
            raise ValueError("quantity must be a positive integer")

    def _validate_status(self, status: str):
        if not isinstance(status, str) or status not in self._valid_statuses:
            raise ValueError(f"status must be one of: {sorted(self._valid_statuses)}")

    def add_order(self, order_id: str, item_name: str, quantity: int, customer_id: str, status: str = "pending"):
        """Return a new order dict, or raise ValueError for invalid or duplicate input."""
        self._validate_non_empty_str(order_id, "order_id")
        self._validate_non_empty_str(item_name, "item_name")
        self._validate_non_empty_str(customer_id, "customer_id")
        self._validate_quantity(quantity)
        self._validate_status(status)

        with self._lock:
            if self.storage.get_order(order_id) is not None:
                raise ValueError("order_id already exists")

            order = {
                "order_id": order_id,
                "item_name": item_name,
                "quantity": quantity,
                "customer_id": customer_id,
                "status": status,
            }
            self.storage.save_order(order_id, order)
            return order.copy()

    def get_order_by_id(self, order_id: str):
        """Return a copied order dict or None, or raise ValueError for an invalid ID."""
        self._validate_non_empty_str(order_id, "order_id")
        with self._lock:
            return self.storage.get_order(order_id)

    def update_order_status(self, order_id: str, new_status: str):
        """Return the updated order dict, or raise ValueError/LookupError on invalid updates."""
        self._validate_non_empty_str(order_id, "order_id")
        self._validate_status(new_status)

        with self._lock:
            order = self.storage.get_order(order_id)
            if order is None:
                raise LookupError("order not found")

            order["status"] = new_status
            self.storage.save_order(order_id, order)
            return order.copy()

    def list_all_orders(self):
        """Return copied order dicts for all stored orders."""
        with self._lock:
            orders = self.storage.get_all_orders().values()
            return [order.copy() for order in orders]

    def list_orders_by_status(self, status: str):
        """Return copied order dicts for a valid status, or raise ValueError otherwise."""
        self._validate_status(status)
        return [order for order in self.list_all_orders() if order.get("status") == status]
