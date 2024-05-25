from flask import Flask, render_template, request , redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
app.config['SQLALCHEMY_DATABASE_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    master_name = db.Column(db.String(50), nullable=False)
    master_phone = db.Column(db.String(11), nullable=False)
    time = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return '<Booking %r>' % self.id


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/ready_meets')
def ready_meets():
    meets = Booking.query.order_by(Booking.time).all()
    return render_template("ready_meets.html",meets=meets)


@app.route('/ready_meets/<int:id>/delete', methods=['POST'])
def post_delete(id):
    meet = Booking.query.get_or_404(id)
    try:
        db.session.delete(meet)
        db.session.commit()
        return redirect("/ready_meets")
    except:
        db.session.rollback()
        return "При удалении записи произошла ошибка"


@app.route('/ready_meets/<int:id>/edit', methods=['GET', 'POST'])
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
            return redirect('/ready_meets')
        except:
            db.session.rollback()
            return "Произошла ошибка при сохранении данных."
    return render_template('edit_meet.html', meet=meet)


@app.route('/meet', methods=['POST', 'GET'])
def meet():
    error_message = None
    if request.method == "POST":
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        master_name = request.form['master_name']
        master_phone = request.form['master_phone']
        time = request.form['time']

        time_exists = Booking.query.filter_by(time=time).first()
        if time_exists:
            error_message = "Это время уже занято. Пожалуйста, выберите другое время."
        else:
            booking = Booking(first_name=first_name, last_name=last_name, master_name=master_name, master_phone=master_phone, time=time)
            try:
                db.session.add(booking)
                db.session.commit()
                return redirect('/')
            except:
                db.session.rollback()
                error_message = "Пожалуйста повторите попозже!"

    return render_template("meet.html", error=error_message)


@app.route('/about')
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)
