from flask import Flask, render_template, redirect, url_for, request
import psycopg2

app = Flask(__name__)

# Функция для подключения к базе данных
def get_db_connection():
    conn = psycopg2.connect(
        dbname='cars',
        user='postgres',
        password='18032004',
        host='localhost',
        port='5432'
    )
    return conn

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
        cur.execute('SELECT * FROM public.dilers WHERE id = %s', (car[9],))  # car[9] - это diler_id
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
        cur.execute('DELETE FROM public.cars WHERE id = %s;', (car_id,))
        conn.commit()
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
                'INSERT INTO public.dilers ("Name", "City", "Address", "Area", "Rating") VALUES (%s, %s, %s, %s, %s);',
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

        cur.execute('UPDATE public.dilers SET "Name" = %s, "City" = %s, "Address" = %s, "Area" = %s, "Rating" = %s WHERE id = %s;',
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

    if request.method == 'POST':
        firm = request.form['firm']
        model = request.form['model']
        year = int(request.form['year'])
        power = int(request.form['power'])
        color = request.form['color']
        price = float(request.form['price'])
        diler_id = request.form['diler_id']

        cur.execute('UPDATE public.cars SET firm = %s, model = %s, year = %s, power = %s, color = %s, price = %s, diler_id = %s WHERE id = %s;',
                    (firm, model, year, power, color, price, diler_id, car_id))
        conn.commit()
        cur.close()
        conn.close()

        return redirect('/cars')

    cur.execute('SELECT * FROM public.cars WHERE id = %s;', (car_id,))
    car = cur.fetchone()

    cur.close()
    conn.close()

    if car is None:
        return "Автомобиль не найден", 404

    return render_template('edit_car.html', car=car)

@app.route('/add_options')
def add_options():
    return render_template('add_options.html')

@app.route('/edit_options')
def edit_options():
    return render_template('edit_options.html')

if __name__ == '__main__':
    app.run(debug=True)
