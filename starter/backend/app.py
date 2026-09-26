from flask import Flask, request, jsonify, send_from_directory
from backend.order_tracker import OrderTracker
from backend.in_memory_storage import InMemoryStorage

ORDER_NOT_FOUND_ERROR = "order not found"

app = Flask(__name__, static_folder='../frontend')
in_memory_storage = InMemoryStorage(max_orders=1000)
order_tracker = OrderTracker(in_memory_storage)

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
        return jsonify(order), 201
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

@app.route('/api/orders/<string:order_id>', methods=['GET'])
def get_order_api(order_id):
    """Return 200 with an order, 400 for invalid IDs, or 404 when absent."""
    try:
        order = order_tracker.get_order_by_id(order_id)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    if order is None:
        return jsonify({'error': ORDER_NOT_FOUND_ERROR}), 404
    return jsonify(order), 200

@app.route('/api/orders/<string:order_id>/status', methods=['PUT'])
def update_order_status_api(order_id):
    """Return 200 with the updated order, 400 for invalid input, or 404 when missing."""
    data = request.get_json(silent=True) or {}
    try:
        order = order_tracker.update_order_status(
            order_id=order_id,
            new_status=data.get('new_status')
        )
        return jsonify(order), 200
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except LookupError as exc:
        return jsonify({'error': str(exc)}), 404

@app.route('/api/orders', methods=['GET'])
def list_orders_api():
    """Return 200 with all orders or filtered orders, or 400 for invalid filters."""
    status = request.args.get('status')
    if status:
        try:
            orders = order_tracker.list_orders_by_status(status)
            return jsonify(orders), 200
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 400

    orders = order_tracker.list_all_orders()
    return jsonify(orders), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
