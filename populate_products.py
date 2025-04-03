import csv
from app import create_app
from app.models import Product
from app.extensions import db

app = create_app()

with app.app_context():
    with open('products.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            product = Product(
                id=int(row['id']),
                name=row['name'],
                price=float(row['price']),
                image=row['image'],
                description=row['description']
            )
            db.session.add(product)
        db.session.commit()
        print("Products added successfully!")
