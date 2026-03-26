import csv
from app import app, db, Inventory

def import_csv():
    with app.app_context():
        db.drop_all()
        db.create_all()
        with open('whatapc_inventory_2026.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                item = Inventory(
                    inventory_id=row['inventory_id'],
                    item_type=row['item_type'],
                    brand=row['brand'],
                    model=row['model'],
                    component=row['component'],
                    qty=int(row['qty']) if row['qty'] else 0,
                    details=row['details'],
                    socket_or_interface=row['socket_or_interface'],
                    status=row['status'],
                    used_in=row['used_in'],
                    ownership=row['ownership'],
                    test_status=row['test_status'],
                    cooler_required=row['cooler_required'],
                    notes=row['notes'],
                    photo_refs=row['photo_refs'],
                    price_paid=float(row['price_paid']) if row['price_paid'] else None,
                    source=row['source'],
                    seller=row['seller'],
                    location_bin=row['location_bin'],
                    location_shelf=row['location_shelf'],
                    location_notes=row['location_notes']
                )
                db.session.add(item)
            db.session.commit()
        print("Data imported successfully")

if __name__ == '__main__':
    import_csv()