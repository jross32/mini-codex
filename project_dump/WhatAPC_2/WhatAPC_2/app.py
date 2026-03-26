from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import or_

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Users/dmjr2/WhatAPC_2/instance/yourdatabase.db'
CORS(app)
db = SQLAlchemy(app)

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.String(50), unique=True, nullable=False)
    item_type = db.Column(db.String(100))
    brand = db.Column(db.String(100))
    model = db.Column(db.String(100))
    component = db.Column(db.String(100))
    qty = db.Column(db.Integer, nullable=False)
    details = db.Column(db.Text)
    socket_or_interface = db.Column(db.String(100))
    status = db.Column(db.String(50))
    used_in = db.Column(db.String(100))
    ownership = db.Column(db.String(50))
    test_status = db.Column(db.String(50))
    cooler_required = db.Column(db.String(100))
    notes = db.Column(db.Text)
    photo_refs = db.Column(db.Text)
    price_paid = db.Column(db.Float)
    source = db.Column(db.String(100))
    seller = db.Column(db.String(100))
    location_bin = db.Column(db.String(50))
    location_shelf = db.Column(db.String(50))
    location_notes = db.Column(db.Text)

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    sort = request.args.get('sort', 'id')
    order = request.args.get('order', 'asc')

    query = Inventory.query

    if search:
        query = query.filter(
            or_(
                Inventory.brand.contains(search),
                Inventory.model.contains(search),
                Inventory.item_type.contains(search),
                Inventory.details.contains(search)
            )
        )
    if status_filter:
        query = query.filter(Inventory.status == status_filter)

    sort_attribute = getattr(Inventory, sort, Inventory.id)
    if order == 'desc':
        query = query.order_by(sort_attribute.desc())
    else:
        query = query.order_by(sort_attribute.asc())

    items = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'items': [{
            'id': item.id,
            'inventory_id': item.inventory_id,
            'item_type': item.item_type,
            'brand': item.brand,
            'model': item.model,
            'component': item.component,
            'qty': item.qty,
            'details': item.details,
            'socket_or_interface': item.socket_or_interface,
            'status': item.status,
            'used_in': item.used_in,
            'ownership': item.ownership,
            'test_status': item.test_status,
            'cooler_required': item.cooler_required,
            'notes': item.notes,
            'photo_refs': item.photo_refs,
            'price_paid': item.price_paid,
            'source': item.source,
            'seller': item.seller,
            'location_bin': item.location_bin,
            'location_shelf': item.location_shelf,
            'location_notes': item.location_notes
        } for item in items.items],
        'total': items.total,
        'pages': items.pages,
        'current_page': items.page
    })

@app.route('/api/inventory', methods=['POST'])
def add_inventory():
    data = request.get_json()
    new_item = Inventory(
        inventory_id=data['inventory_id'],
        item_type=data.get('item_type', ''),
        brand=data.get('brand', ''),
        model=data.get('model', ''),
        component=data.get('component', ''),
        qty=data.get('qty', 1),
        details=data.get('details', ''),
        socket_or_interface=data.get('socket_or_interface', ''),
        status=data.get('status', 'AVAILABLE'),
        used_in=data.get('used_in', ''),
        ownership=data.get('ownership', 'INVENTORY'),
        test_status=data.get('test_status', 'UNTESTED'),
        cooler_required=data.get('cooler_required', ''),
        notes=data.get('notes', ''),
        photo_refs=data.get('photo_refs', ''),
        price_paid=data.get('price_paid'),
        source=data.get('source', ''),
        seller=data.get('seller', ''),
        location_bin=data.get('location_bin', ''),
        location_shelf=data.get('location_shelf', ''),
        location_notes=data.get('location_notes', '')
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify({'message': 'Item added successfully', 'id': new_item.id}), 201

@app.route('/api/inventory/<int:id>', methods=['PUT'])
def update_inventory(id):
    item = Inventory.query.get_or_404(id)
    data = request.get_json()
    for key, value in data.items():
        if hasattr(item, key):
            setattr(item, key, value)
    db.session.commit()
    return jsonify({'message': 'Item updated successfully'})

@app.route('/api/inventory/<int:id>', methods=['DELETE'])
def delete_inventory(id):
    item = Inventory.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Item deleted successfully'})

@app.after_request
def apply_cors(response):
    response.headers.setdefault('Access-Control-Allow-Origin', '*')
    response.headers.setdefault('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.setdefault('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    # Bind to all interfaces so the API is reachable via LAN IP (not just localhost)
    app.run(host='0.0.0.0', port=5000, debug=True)
