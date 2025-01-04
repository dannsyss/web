from flask import Flask, render_template, redirect, url_for, request
import psycopg2
import pika
import json
from decimal import Decimal

app = Flask(__name__)

# Функция для подключения к базе данных
def get_db_connection():
    conn = psycopg2.connect(
        dbname='cars',
        user='postgres',
        password='postgres',
        host='localhost',
        port='5432'
    )
    return conn

# Функция для отправки события в RabbitMQ
def send_event(event_type, car_data):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.exchange_declare(exchange='cars_events_exchange', exchange_type='fanout')
    channel.queue_declare(queue='cars_events_queue', durable=True)
    channel.queue_bind(exchange='cars_events_exchange', queue='cars_events_queue')

    event = {
        "eventType": event_type,
        "car": car_data
    }

    channel.basic_publish(
        exchange='cars_events_exchange',
        routing_key='',
        body=json.dumps(event),
        properties=pika.BasicProperties(
            delivery_mode=2,  # Сделать сообщение устойчивым
        )
    )
    connection.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dilers')
def dilers():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT * FROM public.dilers;')
    dilers_data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('dilers.html', dilers=dilers_data)

@app.route('/cars')
def cars():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT * FROM public.cars;')
    cars_data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('cars.html', cars=cars_data)

@app.route('/dilers/<int:diler_id>/cars')
def dilers_cars(diler_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT * FROM public.cars WHERE diler_id = %s', (diler_id,))
    cars = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('dilers_cars.html', cars=cars, diler_id=diler_id)

@app.route('/cars/<int:car_id>/diler')
def car_diler(car_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT * FROM public.cars WHERE id = %s', (car_id,))
    car = cur.fetchone()

    diler = None
    if car:
        cur.execute('SELECT * FROM public.dilers WHERE id = %s', (car[7],))  # car[7] - это diler_id
        diler = cur.fetchone()

    cur.close()
    conn.close()

    return render_template('car_diler.html', car=car, diler=diler)

@app.route('/cars/remove/<int:car_id>/diler/<int:diler_id>', methods=['POST'])
def remove_car_from_diler(car_id, diler_id):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('UPDATE public.cars SET diler_id = NULL WHERE id = %s;', (car_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return f"Ошибка при удалении автомобиля у дилера: {str(e)}", 500
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('dilers_cars', diler_id=diler_id))

@app.route('/cars/delete/<int:car_id>', methods=['POST'])
def delete_car(car_id):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Получаем данные автомобиля перед удалением
        cur.execute('SELECT * FROM public.cars WHERE id = %s;', (car_id,))
        car = cur.fetchone()
        if car:
            print(car)
            car_data = {
                "firm": car[1],
                "model": car[2],
                "year": car[3],
                "power": car[4],
                "color": car[5],
                "price": str(car[6]),
            }
        cur.execute('DELETE FROM public.cars WHERE id = %s;', (car_id,))
        conn.commit()

        # Отправка события о удалении автомобиля
        send_event("DELETE", car_data)

    except Exception as e:
        conn.rollback()
        return f"Ошибка при удалении автомобиля: {str(e)}", 500
    finally:
        cur.close()
        conn.close()

    return redirect('/cars')

@app.route('/dilers/delete/<int:diler_id>', methods=['POST'])
def delete_diler(diler_id):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('DELETE FROM public.dilers WHERE id = %s;', (diler_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return f"Ошибка при удалении дилера: {str(e)}", 500
    finally:
        cur.close()
        conn.close()

    return redirect('/dilers')

@app.route('/dilers/<int:diler_id>/add_car', methods=['GET', 'POST'])
def add_car_to_diler(diler_id):
    if request.method == 'POST':
        car_id = request.form['car_id']
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('UPDATE public.cars SET diler_id = %s WHERE id = %s;', (diler_id, car_id))
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('dilers_cars', diler_id=diler_id))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM public.cars WHERE diler_id IS NULL;')
    available_cars = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('add_car.html', available_cars=available_cars, diler_id=diler_id)

@app.route('/dilers/add', methods=['GET', 'POST'])
def add_diler():
    if request.method == 'POST':
        try:
            name = request.form['name']
            city = request.form['city']
            address = request.form['address']
            area = request.form['area']
            rating = float(request.form['rating'])

            if not name or not city or not address or not area:
                return "Форма заполнена некорректно, все поля должны быть заполнены.", 400

            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute(
                'INSERT INTO public.dilers ("name", "city", "address", "area", "rating") VALUES (%s, %s, %s, %s, %s);',
                (name, city, address, area, rating))

            conn.commit()
            cur.close()
            conn.close()

            return redirect('/dilers')

        except Exception as e:
            return f"Произошла ошибка: {str(e)}", 500

    return render_template('new_diler.html')

@app.route('/dilers/<int:diler_id>/edit', methods=['GET', 'POST'])
def edit_diler(diler_id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        city = request.form['city']
        address = request.form['address']
        area = request.form['area']
        rating = float(request.form['rating'])

        cur.execute('UPDATE public.dilers SET "name" = %s, "city" = %s, "address" = %s, "area" = %s, "rating" = %s WHERE id = %s;',
                    (name, city, address, area, rating, diler_id))
        conn.commit()
        cur.close()
        conn.close()

        return redirect('/dilers')

    cur.execute('SELECT * FROM public.dilers WHERE id = %s;', (diler_id,))
    diler = cur.fetchone()

    cur.close()
    conn.close()

    if diler is None:
        return "Дилер не найден", 404

    return render_template('edit_diler.html', diler=diler)

@app.route('/cars/add', methods=['GET', 'POST'])
def add_car():
    if request.method == 'POST':
        try:
            firm = request.form['firm']
            model = request.form['model']
            year = int(request.form['year'])
            power = int(request.form['power'])
            color = request.form['color']
            price = float(request.form['price'])

            if not firm or not model or not color:
                return "Форма заполнена некорректно, все поля должны быть заполнены.", 400

            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute(
                'INSERT INTO public.cars (firm, model, year, power, color, price) VALUES (%s, %s, %s, %s, %s, %s);',
                (firm, model, year, power, color, price))

            conn.commit()

            # Отправка события о создании автомобиля
            car_data = {
                "firm": firm,
                "model": model,
                "year": year,
                "power": power,
                "color": color,
                "price": price
            }
            send_event("CREATE", car_data)

            cur.close()
            conn.close()

            return redirect('/cars')

        except Exception as e:
            return f"Произошла ошибка: {str(e)}", 500

    return render_template('new_car.html')

@app.route('/cars/<int:car_id>/edit', methods=['GET', 'POST'])
def edit_car(car_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Получаем данные автомобиля перед обработкой POST-запроса
    cur.execute('SELECT * FROM public.cars WHERE id = %s;', (car_id,))
    car = cur.fetchone()

    if car is None:
        return "Автомобиль не найден", 404  # Обработка случая, когда автомобиль не найден

    if request.method == 'POST':
        firm = request.form['firm']
        model = request.form['model']
        year = int(request.form['year'])
        power = int(request.form['power'])
        color = request.form['color']
        price = float(request.form['price'])
        diler_id = request.form['diler_id']

        # Получаем старые данные автомобиля для отправки в событии
        old_car = car  # Используем ранее полученные данные

        if old_car:
            old_car_data = {
                "firm": old_car[1],
                "model": old_car[2],
                "year": str(old_car[3]),
                "power": str(old_car[4]),
                "color": old_car[5],
                "price": str(old_car[6]),
                "new_firm": firm,
                "new_model": model,
                "new_year": year,
                "new_power": power,
                "new_color": color,
                "new_price": price
            }

        cur.execute('UPDATE public.cars SET firm = %s, model = %s, year = %s, power = %s, color = %s, price = %s, diler_id = %s WHERE id = %s;',
                    (firm, model, year, power, color, price, diler_id, car_id))
        conn.commit()

        # Отправка события о изменении автомобиля
        send_event("UPDATE", old_car_data)

        cur.close()
        conn.close()

        return redirect('/cars')

    cur.close()
    conn.close()

    return render_template('edit_car.html', car=car)


@app.route('/add_options')
def add_options():
    return render_template('add_options.html')

@app.route('/edit_options')
def edit_options():
    return render_template('edit_options.html')

if __name__ == '__main__':
    app.run(debug=True)
