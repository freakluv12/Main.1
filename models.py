from app import db
from datetime import datetime, date
from sqlalchemy import func

class Car(db.Model):
    """Модель для автомобилей в гараже"""
    __tablename__ = 'cars'
    
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(100), nullable=False)  # Марка
    model = db.Column(db.String(100), nullable=False)  # Модель
    year = db.Column(db.Integer, nullable=False)       # Год выпуска
    vin = db.Column(db.String(17), unique=True)        # VIN номер
    purchase_price = db.Column(db.Float, default=0)    # Стоимость покупки
    description = db.Column(db.Text)                   # Описание
    status = db.Column(db.String(20), default='active')  # Статус: active, rented, disassembled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    expenses = db.relationship('Expense', backref='car', lazy=True)
    rentals = db.relationship('Rental', backref='car', lazy=True)
    
    def __repr__(self):
        return f'<Car {self.brand} {self.model} ({self.year})>'

class Expense(db.Model):
    """Модель для расходов по автомобилям"""
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    amount = db.Column(db.Float, nullable=False)       # Сумма расхода
    category = db.Column(db.String(50), nullable=False)  # Категория: топливо, ремонт, запчасти, обслуживание
    description = db.Column(db.Text)                   # Описание расхода
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Expense {self.amount} ({self.category})>'

class Client(db.Model):
    """Модель для клиентов аренды"""
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)   # Имя клиента
    phone = db.Column(db.String(20))                   # Телефон
    email = db.Column(db.String(100))                  # Email
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    rentals = db.relationship('Rental', backref='client', lazy=True)
    
    def __repr__(self):
        return f'<Client {self.name}>'

class Rental(db.Model):
    """Модель для контрактов аренды"""
    __tablename__ = 'rentals'
    
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)    # Дата начала аренды
    end_date = db.Column(db.Date, nullable=False)      # Дата окончания аренды
    daily_rate = db.Column(db.Float, nullable=False)   # Стоимость за день
    total_amount = db.Column(db.Float, nullable=False) # Общая стоимость
    status = db.Column(db.String(20), default='active')  # Статус: active, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    payments = db.relationship('Payment', backref='rental', lazy=True)
    
    def __repr__(self):
        return f'<Rental Car:{self.car_id} Client:{self.client_id}>'

class Payment(db.Model):
    """Модель для платежей по аренде"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    rental_id = db.Column(db.Integer, db.ForeignKey('rentals.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)       # Сумма платежа
    payment_date = db.Column(db.Date, nullable=False, default=date.today)
    description = db.Column(db.Text)                   # Описание платежа
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Payment {self.amount} for Rental:{self.rental_id}>'

class DisassemblyRecord(db.Model):
    """Модель для записей разборки автомобилей"""
    __tablename__ = 'disassembly_records'
    
    id = db.Column(db.Integer, primary_key=True)
    car_brand = db.Column(db.String(100), nullable=False)  # Марка разбираемого авто
    car_model = db.Column(db.String(100), nullable=False)  # Модель разбираемого авто
    car_year = db.Column(db.Integer, nullable=False)       # Год выпуска
    vin = db.Column(db.String(17))                         # VIN номер
    description = db.Column(db.Text)                       # Описание состояния авто
    disassembly_date = db.Column(db.Date, nullable=False, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    extracted_parts = db.relationship('Part', backref='disassembly_record', lazy=True)
    
    def __repr__(self):
        return f'<DisassemblyRecord {self.car_brand} {self.car_model}>'

class Supplier(db.Model):
    """Модель для поставщиков запчастей"""
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)   # Название поставщика
    contact_person = db.Column(db.String(100))         # Контактное лицо
    phone = db.Column(db.String(20))                   # Телефон
    email = db.Column(db.String(100))                  # Email
    address = db.Column(db.Text)                       # Адрес
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    parts = db.relationship('Part', backref='supplier', lazy=True)
    
    def __repr__(self):
        return f'<Supplier {self.name}>'

class Part(db.Model):
    """Модель для запчастей на складе"""
    __tablename__ = 'parts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)   # Наименование запчасти
    code = db.Column(db.String(50), unique=True)       # Код запчасти
    quantity = db.Column(db.Integer, default=0)        # Количество на складе
    price = db.Column(db.Float, nullable=False)        # Цена за единицу
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    disassembly_record_id = db.Column(db.Integer, db.ForeignKey('disassembly_records.id'))
    description = db.Column(db.Text)                   # Описание запчасти
    location = db.Column(db.String(100))               # Местоположение на складе
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Part {self.name} ({self.code})>'

class Sale(db.Model):
    """Модель для продаж запчастей"""
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('parts.id'), nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False)  # Количество проданных запчастей
    sale_price = db.Column(db.Float, nullable=False)       # Цена продажи за единицу
    total_amount = db.Column(db.Float, nullable=False)     # Общая сумма продажи
    sale_date = db.Column(db.Date, nullable=False, default=date.today)
    customer_name = db.Column(db.String(100))              # Имя покупателя
    description = db.Column(db.Text)                       # Описание продажи
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    part = db.relationship('Part', backref='sales', lazy=True)
    
    def __repr__(self):
        return f'<Sale Part:{self.part_id} Qty:{self.quantity_sold}>'
