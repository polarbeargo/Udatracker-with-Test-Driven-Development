from flask import Flask, request, jsonify, send_from_directory, url_for
from backend.order_tracker import OrderTracker
from backend.in_memory_storage import InMemoryStorage

ORDER_NOT_FOUND_ERROR = "order not found"
INVALID_LIMIT_ERROR = "limit must be a positive integer"

app = Flask(__name__, static_folder='../frontend')
# Keep the demo process bounded even though persistence is intentionally in-memory.
in_memory_storage = InMemoryStorage(max_orders=1000)
order_tracker = OrderTracker(in_memory_storage)


def error_response(message: str, status_code: int):
    return jsonify({'error': message}), status_code


def parse_limit(limit_value: str | None):
    if limit_value is None:
        return None

    try:
        limit = int(limit_value)
    except (TypeError, ValueError):
        raise ValueError(INVALID_LIMIT_ERROR) from None

    if limit <= 0:
        raise ValueError(INVALID_LIMIT_ERROR)

    return limit


@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)


@app.route('/api/orders', methods=['POST'])
def add_order_api():
    """Create an order and return 201, or 400 for invalid input."""
    data = request.get_json(silent=True) or {}
    try:
        order = order_tracker.add_order(
            order_id=data.get('order_id'),
            item_name=data.get('item_name'),
            quantity=data.get('quantity'),
            customer_id=data.get('customer_id'),
            status=data.get('status', 'pending')
        )
        return jsonify(order), 201, {
            'Location': url_for('get_order_api', order_id=order['order_id'])
        }
    except ValueError as exc:
        return error_response(str(exc), 400)


@app.route('/api/orders/<string:order_id>', methods=['GET'])
def get_order_api(order_id):
    """Return 200 with an order, 400 for invalid IDs, or 404 when absent."""
    try:
        order = order_tracker.get_order_by_id(order_id)
    except ValueError as exc:
        return error_response(str(exc), 400)

    if order is None:
        return error_response(ORDER_NOT_FOUND_ERROR, 404)
    return jsonify(order), 200


@app.route('/api/orders/<string:order_id>/status', methods=['PUT'])
def update_order_status_api(order_id):
    """Return 200 with the updated order, 400 for invalid input, or 404 when missing."""
    data = request.get_json(silent=True) or {}
    new_status = data['new_status'] if 'new_status' in data else data.get('status')
    try:
        order = order_tracker.update_order_status(
            order_id=order_id,
            new_status=new_status
        )
        return jsonify(order), 200
    except ValueError as exc:
        return error_response(str(exc), 400)
    except LookupError as exc:
        return error_response(str(exc), 404)


@app.route('/api/orders', methods=['GET'])
def list_orders_api():
    """Return 200 with all orders or filtered orders, or 400 for invalid filters."""
    status = request.args.get('status')
    limit_value = request.args.get('limit')

    try:
        limit = parse_limit(limit_value)
    except ValueError as exc:
        return error_response(str(exc), 400)

    if status is not None:
        if not status.strip():
            return error_response('status must be a non-empty string', 400)
        try:
            orders = order_tracker.list_orders_by_status(status)
        except ValueError as exc:
            return error_response(str(exc), 400)
    else:
        orders = order_tracker.list_all_orders()

    if limit is not None:
        orders = orders[:limit]

    return jsonify(orders), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
