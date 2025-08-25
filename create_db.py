from app import app, db

with app.app_context():
    print("Створюємо таблиці...")
    db.create_all()
    print("Таблиці створені ✅")
