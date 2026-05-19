import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "gym_saas_key"


def init_db():
    conn = sqlite3.connect("gym.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        is_admin INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        training_type TEXT,
        gym_zone TEXT,
        gym_address TEXT,
        booking_date TEXT,
        booking_time TEXT,
        trainer_type TEXT,
        price INTEGER
    )
    """)

    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect("gym.db")
    conn.row_factory = sqlite3.Row
    return conn


def login_required():
    return "user_id" in session


@app.route("/")
def home():
    if login_required():
        return redirect(url_for("dashboard"))
    return render_template("index.html")



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        hashed_pw = generate_password_hash(password)
        
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            conn.commit()
            return redirect(url_for('home')) 
        except sqlite3.IntegrityError:
            return "Этот логин уже занят!"
        finally:
            conn.close()
            
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session["user_id"] = user['id']
            session["username"] = user['username']
            return redirect(url_for('dashboard'))
        else:
            return "Неверный логин или пароль!"
            
    return render_template('index.html')




@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("home"))

    return render_template("dashboard.html", username=session["username"])


@app.route("/book", methods=["POST"])
def book():
    if not login_required():
        return redirect(url_for("home"))

    training = request.form.get("training", "")
    zone = request.form.get("gym_zone", "")
    address = request.form.get("gym_address", "")
    date = request.form.get("date", "")
    time = request.form.get("time", "")
    trainer = request.form.get("trainer_type", "without")

    price = 10000 if trainer == "with" else 5000

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO bookings (
            user_id,
            training_type,
            gym_zone,
            gym_address,
            booking_date,
            booking_time,
            trainer_type,
            price
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        training,
        zone,
        address,
        date,
        time,
        trainer,
        price
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("profile"))


@app.route("/profile")
def profile():
    if not login_required():
        return redirect(url_for("home"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id,
               training_type,
               gym_zone,
               gym_address,
               booking_date,
               booking_time,
               trainer_type,
               price
        FROM bookings
        WHERE user_id=?
        ORDER BY id DESC
    """, (session["user_id"],))

    bookings = cur.fetchall()
    conn.close()

    return render_template("profile.html", bookings=bookings)

@app.route("/update/<int:bid>", methods=["POST"])
def update_booking(bid):
    if not login_required():
        return redirect(url_for("home"))

    training = request.form.get("training", "")
    zone = request.form.get("gym_zone", "")
    address = request.form.get("gym_address", "")
    date = request.form.get("date", "")
    time = request.form.get("time", "")
    trainer = request.form.get("trainer_type", "without")

    price = 10000 if trainer == "with" else 5000

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE bookings
        SET training_type = ?,
            gym_zone = ?,
            gym_address = ?,
            booking_date = ?,
            booking_time = ?,
            trainer_type = ?,
            price = ?
        WHERE id = ? AND user_id = ?
    """, (
        training,
        zone,
        address,
        date,
        time,
        trainer,
        price,
        bid,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("profile"))


@app.route("/delete/<int:bid>", methods=["POST"])
def delete(bid):
    if not login_required():
        return redirect(url_for("home"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM bookings WHERE id=? AND user_id=?",
        (bid, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect(url_for("profile"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)