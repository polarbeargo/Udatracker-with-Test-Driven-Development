# This file provides a simple in-memory storage implementation for orders.
# Data stored here will be lost when the application restarts.

from collections import OrderedDict


class InMemoryStorage:
    """
    A simple in-memory implementation of the storage interface.
    Stores orders in an insertion-ordered dictionary and evicts the oldest
    record once the configured maximum number of orders is reached.
    """
    def __init__(self, max_orders: int = 1000):
        if not isinstance(max_orders, int) or isinstance(max_orders, bool) or max_orders <= 0:
            raise ValueError("max_orders must be a positive integer")
        self.max_orders = max_orders
        self._orders = OrderedDict()

    def save_order(self, order_id: str, order_data: dict):
        if order_id in self._orders:
            self._orders.pop(order_id)

        self._orders[order_id] = order_data.copy()

        while len(self._orders) > self.max_orders:
            self._orders.popitem(last=False)

    def get_order(self, order_id: str):
        return self._orders.get(order_id, {}).copy() if self._orders.get(order_id) else None

    def get_all_orders(self):
        return {k: v.copy() for k, v in self._orders.items()}

    def clear(self):
        self._orders = OrderedDict()
