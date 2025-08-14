from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from app import app, db
from models import Car, Expense, Client, Rental, Payment, DisassemblyRecord, Supplier, Part, Sale
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
import json
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

@app.route('/')
def index():
    """Главная страница с общей статистикой"""
    # Получаем основную статистику для дашборда
    total_cars = Car.query.filter_by(status='active').count()
    active_rentals = Rental.query.filter_by(status='active').count()
    total_parts = db.session.query(func.sum(Part.quantity)).scalar() or 0
    
    # Доходы и расходы за текущий месяц
    current_month = date.today().replace(day=1)
    monthly_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.date >= current_month
    ).scalar() or 0
    
    monthly_rental_income = db.session.query(func.sum(Payment.amount)).filter(
        Payment.payment_date >= current_month
    ).scalar() or 0
    
    monthly_parts_income = db.session.query(func.sum(Sale.total_amount)).filter(
        Sale.sale_date >= current_month
    ).scalar() or 0
    
    monthly_income = monthly_rental_income + monthly_parts_income
    monthly_profit = monthly_income - monthly_expenses
    
    return render_template('index.html',
                         total_cars=total_cars,
                         active_rentals=active_rentals,
                         total_parts=total_parts,
                         monthly_income=monthly_income,
                         monthly_expenses=monthly_expenses,
                         monthly_profit=monthly_profit)

@app.route('/garage')
def garage():
    """Страница модуля Гараж - показывает только список автомобилей"""
    # Получаем все автомобили с их связями для вычисления финансов
    cars = Car.query.all()
    
    return render_template('garage.html', cars=cars)

@app.route('/garage/add_car', methods=['POST'])
def add_car():
    """Добавление нового автомобиля"""
    try:
        car = Car(
            brand=request.form['brand'],
            model=request.form['model'],
            year=int(request.form['year']),
            purchase_price=float(request.form.get('purchase_price', 0)),
            vin=request.form.get('vin') or None,
            description=request.form.get('description', '')
        )
        db.session.add(car)
        db.session.commit()
        flash('Автомобиль успешно добавлен!', 'success')
    except Exception as e:
        flash(f'Ошибка при добавлении автомобиля: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('garage'))

@app.route('/garage/car/<int:car_id>')
def car_detail(car_id):
    """Детальная информация об автомобиле"""
    car = Car.query.get_or_404(car_id)
    
    # Получение всех расходов для данного автомобиля
    expenses = Expense.query.filter_by(car_id=car_id).order_by(Expense.date.desc()).all()
    
    # Получение всех аренд для данного автомобиля
    rentals = Rental.query.filter_by(car_id=car_id).order_by(Rental.created_at.desc()).all()
    
    # Расчет финансовых показателей
    total_expenses = sum(expense.amount for expense in expenses)
    total_income = 0
    
    for rental in rentals:
        rental_income = sum(payment.amount for payment in rental.payments)
        total_income += rental_income
    
    return render_template('car_detail.html', 
                         car=car, 
                         expenses=expenses,
                         rentals=rentals,
                         total_expenses=total_expenses,
                         total_income=total_income)

@app.route('/garage/add_expense', methods=['POST'])
def add_expense():
    """Добавление расхода"""
    try:
        car_id = int(request.form['car_id'])
        expense = Expense(
            car_id=car_id,
            date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
            amount=float(request.form['amount']),
            category=request.form['category'],
            description=request.form.get('description', '')
        )
        db.session.add(expense)
        db.session.commit()
        flash('Расход успешно добавлен!', 'success')
        
        # Проверяем, откуда был сделан запрос - из детальной страницы или из гаража
        referer = request.headers.get('Referer', '')
        if f'/garage/car/{car_id}' in referer:
            return redirect(url_for('car_detail', car_id=car_id))
        else:
            return redirect(url_for('garage'))
            
    except Exception as e:
        flash(f'Ошибка при добавлении расхода: {str(e)}', 'error')
        db.session.rollback()
        return redirect(url_for('garage'))

@app.route('/rent')
def rent():
    """Страница модуля Аренда"""
    clients = Client.query.all()
    cars = Car.query.filter_by(status='active').all()
    rentals = Rental.query.order_by(Rental.created_at.desc()).all()
    
    return render_template('rent.html', clients=clients, cars=cars, rentals=rentals)

@app.route('/rent/add_client', methods=['POST'])
def add_client():
    """Добавление нового клиента"""
    try:
        client = Client(
            name=request.form['name'],
            phone=request.form.get('phone', ''),
            email=request.form.get('email', '')
        )
        db.session.add(client)
        db.session.commit()
        flash('Клиент успешно добавлен!', 'success')
    except Exception as e:
        flash(f'Ошибка при добавлении клиента: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('rent'))

@app.route('/rent/add_rental', methods=['POST'])
def add_rental():
    """Создание нового контракта аренды"""
    try:
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        daily_rate = float(request.form['daily_rate'])
        days = (end_date - start_date).days + 1
        total_amount = daily_rate * days
        
        rental = Rental(
            car_id=int(request.form['car_id']),
            client_id=int(request.form['client_id']),
            start_date=start_date,
            end_date=end_date,
            daily_rate=daily_rate,
            total_amount=total_amount
        )
        
        # Обновляем статус автомобиля
        car = Car.query.get(rental.car_id)
        car.status = 'rented'
        
        db.session.add(rental)
        db.session.commit()
        flash('Контракт аренды успешно создан!', 'success')
    except Exception as e:
        flash(f'Ошибка при создании контракта: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('rent'))

@app.route('/rent/add_payment', methods=['POST'])
def add_payment():
    """Добавление платежа по аренде"""
    try:
        payment = Payment(
            rental_id=int(request.form['rental_id']),
            amount=float(request.form['amount']),
            payment_date=datetime.strptime(request.form['payment_date'], '%Y-%m-%d').date(),
            description=request.form.get('description', '')
        )
        db.session.add(payment)
        db.session.commit()
        flash('Платеж успешно добавлен!', 'success')
    except Exception as e:
        flash(f'Ошибка при добавлении платежа: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('rent'))

@app.route('/rent/complete/<int:rental_id>')
def complete_rental(rental_id):
    """Завершение аренды"""
    try:
        rental = Rental.query.get_or_404(rental_id)
        rental.status = 'completed'
        
        # Возвращаем статус автомобиля
        car = Car.query.get(rental.car_id)
        car.status = 'active'
        
        db.session.commit()
        flash('Аренда успешно завершена!', 'success')
    except Exception as e:
        flash(f'Ошибка при завершении аренды: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('rent'))

@app.route('/disassembly')
def disassembly():
    """Страница модуля Разборка"""
    records = DisassemblyRecord.query.order_by(DisassemblyRecord.created_at.desc()).all()
    suppliers = Supplier.query.all()
    
    return render_template('disassembly.html', records=records, suppliers=suppliers)

@app.route('/disassembly/add_record', methods=['POST'])
def add_disassembly_record():
    """Добавление записи о разборке"""
    try:
        record = DisassemblyRecord(
            car_brand=request.form['car_brand'],
            car_model=request.form['car_model'],
            car_year=int(request.form['car_year']),
            vin=request.form.get('vin') or None,
            description=request.form.get('description', ''),
            disassembly_date=datetime.strptime(request.form['disassembly_date'], '%Y-%m-%d').date()
        )
        db.session.add(record)
        db.session.commit()
        flash('Запись о разборке успешно добавлена!', 'success')
    except Exception as e:
        flash(f'Ошибка при добавлении записи: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('disassembly'))

@app.route('/disassembly/add_part', methods=['POST'])
def add_part_from_disassembly():
    """Добавление запчасти с разборки"""
    try:
        part = Part(
            name=request.form['name'],
            code=request.form.get('code'),
            quantity=int(request.form['quantity']),
            price=float(request.form['price']),
            disassembly_record_id=int(request.form['disassembly_record_id']),
            description=request.form.get('description', ''),
            location=request.form.get('location', '')
        )
        db.session.add(part)
        db.session.commit()
        flash('Запчасть успешно добавлена в склад!', 'success')
    except Exception as e:
        flash(f'Ошибка при добавлении запчасти: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('disassembly'))

@app.route('/parts')
def parts():
    """Страница модуля Учет запчастей"""
    # Фильтры поиска
    search = request.args.get('search', '')
    supplier_id = request.args.get('supplier_id')
    
    # Базовый запрос
    parts_query = Part.query
    
    # Применяем фильтры
    if search:
        parts_query = parts_query.filter(
            or_(
                Part.name.ilike(f'%{search}%'),
                Part.code.ilike(f'%{search}%'),
                Part.description.ilike(f'%{search}%')
            )
        )
    
    if supplier_id:
        parts_query = parts_query.filter(Part.supplier_id == supplier_id)
    
    parts = parts_query.order_by(Part.created_at.desc()).all()
    suppliers = Supplier.query.all()
    
    return render_template('parts.html', parts=parts, suppliers=suppliers)

@app.route('/parts/add_supplier', methods=['POST'])
def add_supplier():
    """Добавление нового поставщика"""
    try:
        supplier = Supplier(
            name=request.form['name'],
            contact_person=request.form.get('contact_person', ''),
            phone=request.form.get('phone', ''),
            email=request.form.get('email', ''),
            address=request.form.get('address', '')
        )
        db.session.add(supplier)
        db.session.commit()
        flash('Поставщик успешно добавлен!', 'success')
    except Exception as e:
        flash(f'Ошибка при добавлении поставщика: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('parts'))

@app.route('/parts/add_part', methods=['POST'])
def add_part():
    """Добавление новой запчасти"""
    try:
        part = Part(
            name=request.form['name'],
            code=request.form.get('code'),
            quantity=int(request.form['quantity']),
            price=float(request.form['price']),
            supplier_id=int(request.form['supplier_id']) if request.form.get('supplier_id') else None,
            description=request.form.get('description', ''),
            location=request.form.get('location', '')
        )
        db.session.add(part)
        db.session.commit()
        flash('Запчасть успешно добавлена!', 'success')
    except Exception as e:
        flash(f'Ошибка при добавлении запчасти: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('parts'))

@app.route('/parts/sale', methods=['POST'])
def sell_part():
    """Продажа запчасти"""
    try:
        part_id = int(request.form['part_id'])
        quantity_sold = int(request.form['quantity_sold'])
        sale_price = float(request.form['sale_price'])
        
        part = Part.query.get_or_404(part_id)
        
        # Проверяем наличие на складе
        if part.quantity < quantity_sold:
            flash('Недостаточно товара на складе!', 'error')
            return redirect(url_for('parts'))
        
        # Создаем запись о продаже
        sale = Sale(
            part_id=part_id,
            quantity_sold=quantity_sold,
            sale_price=sale_price,
            total_amount=quantity_sold * sale_price,
            sale_date=datetime.strptime(request.form['sale_date'], '%Y-%m-%d').date(),
            customer_name=request.form.get('customer_name', ''),
            description=request.form.get('description', '')
        )
        
        # Уменьшаем количество на складе
        part.quantity -= quantity_sold
        
        db.session.add(sale)
        db.session.commit()
        flash('Продажа успешно оформлена!', 'success')
    except Exception as e:
        flash(f'Ошибка при оформлении продажи: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('parts'))

@app.route('/analytics')
def analytics():
    """Страница модуля Аналитика"""
    # Получаем данные для графиков за последние 12 месяцев
    months = []
    income_data = []
    expense_data = []
    profit_data = []
    
    for i in range(11, -1, -1):
        month_start = (date.today().replace(day=1) - timedelta(days=32*i)).replace(day=1)
        if i > 0:
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        else:
            month_end = date.today()
        
        months.append(month_start.strftime('%Y-%m'))
        
        # Доходы
        rental_income = db.session.query(func.sum(Payment.amount)).filter(
            and_(Payment.payment_date >= month_start, Payment.payment_date <= month_end)
        ).scalar() or 0
        
        parts_income = db.session.query(func.sum(Sale.total_amount)).filter(
            and_(Sale.sale_date >= month_start, Sale.sale_date <= month_end)
        ).scalar() or 0
        
        total_income = rental_income + parts_income
        income_data.append(float(total_income))
        
        # Расходы
        expenses = db.session.query(func.sum(Expense.amount)).filter(
            and_(Expense.date >= month_start, Expense.date <= month_end)
        ).scalar() or 0
        
        expense_data.append(float(expenses))
        profit_data.append(float(total_income - expenses))
    
    # Статистика по категориям расходов
    expense_categories = db.session.query(
        Expense.category,
        func.sum(Expense.amount)
    ).group_by(Expense.category).all()
    
    return render_template('analytics.html',
                         months=json.dumps(months),
                         income_data=json.dumps(income_data),
                         expense_data=json.dumps(expense_data),
                         profit_data=json.dumps(profit_data),
                         expense_categories=expense_categories)

@app.route('/analytics/export_pdf')
def export_pdf():
    """Экспорт отчета в PDF"""
    try:
        # Создаем PDF в памяти
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Стили
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Центрирование
        )
        
        # Заголовок
        story.append(Paragraph("Отчет по прибыльности автобизнеса", title_style))
        story.append(Spacer(1, 20))
        
        # Период отчета
        story.append(Paragraph(f"Период: {date.today().strftime('%d.%m.%Y')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Общая статистика
        total_cars = Car.query.filter_by(status='active').count()
        active_rentals = Rental.query.filter_by(status='active').count()
        total_parts = db.session.query(func.sum(Part.quantity)).scalar() or 0
        
        # Доходы и расходы за текущий месяц
        current_month = date.today().replace(day=1)
        monthly_expenses = db.session.query(func.sum(Expense.amount)).filter(
            Expense.date >= current_month
        ).scalar() or 0
        
        monthly_rental_income = db.session.query(func.sum(Payment.amount)).filter(
            Payment.payment_date >= current_month
        ).scalar() or 0
        
        monthly_parts_income = db.session.query(func.sum(Sale.total_amount)).filter(
            Sale.sale_date >= current_month
        ).scalar() or 0
        
        monthly_income = monthly_rental_income + monthly_parts_income
        monthly_profit = monthly_income - monthly_expenses
        
        # Таблица с основными показателями
        data = [
            ['Показатель', 'Значение'],
            ['Активных автомобилей', str(total_cars)],
            ['Активных аренд', str(active_rentals)],
            ['Запчастей на складе', str(total_parts)],
            ['Доходы за месяц, руб.', f"{monthly_income:.2f}"],
            ['Расходы за месяц, руб.', f"{monthly_expenses:.2f}"],
            ['Прибыль за месяц, руб.', f"{monthly_profit:.2f}"]
        ]
        
        table = Table(data, colWidths=[4*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        # Создаем PDF
        doc.build(story)
        buffer.seek(0)
        
        # Возвращаем PDF файл
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=report_{date.today().strftime("%Y%m%d")}.pdf'
        
        return response
        
    except Exception as e:
        flash(f'Ошибка при создании PDF: {str(e)}', 'error')
        return redirect(url_for('analytics'))

@app.route('/api/car_availability/<int:car_id>')
def car_availability(car_id):
    """API для проверки доступности автомобиля"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'available': False, 'message': 'Не указаны даты'})
    
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Проверяем пересечения с существующими арендами
        conflicts = Rental.query.filter(
            and_(
                Rental.car_id == car_id,
                Rental.status == 'active',
                or_(
                    and_(Rental.start_date <= start, Rental.end_date >= start),
                    and_(Rental.start_date <= end, Rental.end_date >= end),
                    and_(Rental.start_date >= start, Rental.end_date <= end)
                )
            )
        ).count()
        
        available = conflicts == 0
        message = 'Автомобиль доступен' if available else 'Автомобиль занят в указанные даты'
        
        return jsonify({'available': available, 'message': message})
        
    except Exception as e:
        return jsonify({'available': False, 'message': f'Ошибка: {str(e)}'})
