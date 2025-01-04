import json
import psycopg2

# Подключение к базе данных
def connect_db():
    try:
        conn = psycopg2.connect(
            dbname='cars',
            user='postgres',
            password='postgres',
            host='localhost',
            port='5432'
        )
        print("Подключение к базе данных успешно.")
        return conn
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        raise

# Функция для создания таблиц
def create_tables(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dilers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                city VARCHAR(100),
                address VARCHAR(255),
                area VARCHAR(100),
                rating FLOAT
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cars (
                id SERIAL PRIMARY KEY,
                firm VARCHAR(100),
                model VARCHAR(100),
                year INT,
                power INT,
                color VARCHAR(50),
                price DECIMAL
            );
        """)
        conn.commit()
        print("Таблицы созданы или уже существуют.")

# Функция для загрузки дилеров
def load_dilers(conn, dilers_data):
    with conn.cursor() as cursor:
        for diler in dilers_data['dilers']:
            try:
                cursor.execute("""
                    INSERT INTO dilers (name, city, address, area, rating) 
                    VALUES (%s, %s, %s, %s, %s) RETURNING id;
                """, (diler['Name'], diler['City'], diler['Address'], diler['Area'], diler['Rating']))
                diler_id = cursor.fetchone()[0]
                conn.commit()
                print(f"Дилер добавлен с ID: {diler_id}")
            except Exception as e:
                print(f"Ошибка при вставке дилера {diler['Name']}: {e}")

# Функция для загрузки машин
def load_cars(conn, cars_data):
    with conn.cursor() as cursor:
        for car in cars_data['cars']:
            try:
                cursor.execute("""
                    INSERT INTO cars (firm, model, year, power, color, price) 
                    VALUES (%s, %s, %s, %s, %s, %s);
                """, (car['firm'], car['model'], car['year'], car['power'], car['color'], car['price']))
                conn.commit()
                print(f"Автомобиль добавлен: {car['firm']} {car['model']}")
            except Exception as e:
                print(f"Ошибка при вставке автомобиля {car['firm']} {car['model']}: {e}")

def main():
    # Загружаем данные из JSON файлов
    try:
        with open(r'C:\Desktop\Dev\web\json\dilers.json', 'r', encoding='utf-8') as f:
            dilers_data = json.load(f)

        with open(r'C:\Desktop\Dev\web\json\cars.json', 'r', encoding='utf-8') as f:
            cars_data = json.load(f)
    except Exception as e:
        print(f"Ошибка при загрузке JSON файлов: {e}")
        return

    # Подключаемся к базе данных
    conn = connect_db()

    try:
        # Создаем таблицы
        create_tables(conn)

        # Загружаем дилеров
        load_dilers(conn, dilers_data)

        # Загружаем машины
        load_cars(conn, cars_data)

    finally:
        conn.close()
        print("Соединение с базой данных закрыто.")

if __name__ == "__main__":
    main()
