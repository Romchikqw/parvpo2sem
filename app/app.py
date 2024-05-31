from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import redis
import json
from flask_caching import Cache
import time
import logging

# Настройка логгера
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Логирование всех уровней
logFormatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

# Консольный обработчик
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

# Файловый обработчик
fileHandler = logging.FileHandler("logs.log")
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

# Инициализация Flask-приложения
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Настройка кэширования
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
cache = Cache(app)

# Клиент Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Определение модели данных
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    master_name = db.Column(db.String(50), nullable=False)
    master_phone = db.Column(db.String(11), nullable=False)
    time = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f'<Booking {self.id}>'

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "master_name": self.master_name,
            "master_phone": self.master_phone,
            "time": self.time
        }

# Функция отправки сообщений через Redis
def send_message(message):
    try:
        redis_client.publish('booking_channel', json.dumps(message))
        logger.info(f"Sent message: {message}")
    except redis.RedisError as e:
        logger.error("Failed to publish message to Redis", exc_info=True)

# Главная страница
@app.route('/')
@cache.cached()
def index():
    start_time = time.perf_counter()
    result = cache.get('index')
    logger.debug("Accessed the index route")
    if not result:
        result = render_template("index.html")
        cache.set('index', result, timeout=60)
        logger.info(f'Cache miss: {time.perf_counter() - start_time:.6f} seconds')
    else:
        logger.info(f'Cache hit: {time.perf_counter() - start_time:.6f} seconds')
    return result

# Отображение списка встреч
@app.route('/ready_meets')
@cache.cached()
def ready_meets():
    meets = Booking.query.order_by(Booking.time).all()
    return render_template("ready_meets.html", meets=meets)

# Удаление записи
@app.route('/ready_meets/<int:id>/delete', methods=['POST'])
@cache.cached()
def post_delete(id):
    meet = Booking.query.get_or_404(id)
    try:
        db.session.delete(meet)
        db.session.commit()
        logger.info(f"Deleted meeting with id {id}")
        return redirect("/ready_meets")
    except Exception as e:
        db.session.rollback()
        logger.error("Failed to delete the meeting", exc_info=True)
        return "Ошибка при удалении записи"

# Редактирование записи
@app.route('/ready_meets/<int:id>/edit', methods=['GET', 'POST'])
@cache.cached()
def edit_meet(id):
    meet = Booking.query.get_or_404(id)
    if request.method == 'POST':
        meet.first_name = request.form['first_name']
        meet.last_name = request.form['last_name']
        meet.master_name = request.form['master_name']
        meet.master_phone = request.form['master_phone']
        meet.time = request.form['time']
        try:
            db.session.commit()
            logger.info(f"Updated meeting with id {id}")
            return redirect('/ready_meets')
        except Exception as e:
            db.session.rollback()
            logger.error("Failed to update the meeting", exc_info=True)
            return "Ошибка при сохранении данных."
    return render_template('edit_meet.html', meet=meet)

# Создание новой записи
@app.route('/meet', methods=['POST', 'GET'])
@cache.cached()
def meet():
    if request.method == "POST":
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        master_name = request.form['master_name']
        master_phone = request.form['master_phone']
        time = request.form['time']

        time_exists = Booking.query.filter_by(time=time).first()
        if time_exists:
            logger.warning(f"Attempt to book an already booked time: {time}")
            return "Это время уже занято. Пожалуйста, выберите другое время."
        else:
            booking = Booking(first_name=first_name, last_name=last_name, master_name=master_name, master_phone=master_phone, time=time)
            try:
                db.session.add(booking)
                db.session.commit()
                send_message(booking.to_dict())
                logger.info(f"Created new booking with id {booking.id}")
                return redirect('/')
            except Exception as e:
                db.session.rollback()
                logger.error("Failed to create a new booking", exc_info=True)
                return "Пожалуйста, повторите попытку позже!"
    return render_template("meet.html")

# Страница "О нас"
@app.route('/about')
@cache.cached()
def about():
    return render_template("about.html")

@app.errorhandler(404)
def page_not_found(error):
    # Логирование события с указанием запрашиваемого URL
    logger.error(f"404 Not Found: Attempted to access {request.path} which does not exist.")
    # Возвращаем простой текстовый ответ
    return "Страница не найдена", 404


# Запуск приложения
if __name__ == "__main__":
    app.run(debug=True, port=5000)
