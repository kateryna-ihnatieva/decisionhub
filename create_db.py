from app import app, db

with app.app_context():
    print("Создаём таблицы...")
    db.create_all()
    print("Таблицы созданы ✅")
