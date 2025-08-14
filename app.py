import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Настройка логирования для отладки
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Создание экземпляра базы данных
db = SQLAlchemy(model_class=Base)

# Создание приложения Flask
app = Flask(__name__)

# Настройка секретного ключа для сессий
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Middleware для обработки прокси (нужно для правильной генерации URL)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Настройка базы данных SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///autobusiness.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Инициализация базы данных с приложением
db.init_app(app)

# Создание контекста приложения и таблиц
with app.app_context():
    # Импорт моделей для создания таблиц
    import models
    # Создание всех таблиц
    db.create_all()

# Импорт маршрутов
import routes
