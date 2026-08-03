import base64
import numpy as np
from PIL import Image
from io import BytesIO
import os
import cv2
import sqlite3
import datetime
import csv
import shutil
from flask import send_file
from flask import Flask, render_template, request, redirect, url_for, session, flash
from trainer import train_model
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key=os.environ.get(
    "SECRET_KEY",
    "attendance123"
)

def create_database():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()


    cursor.execute("""
CREATE TABLE IF NOT EXISTS admin(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    email TEXT UNIQUE,
    password TEXT
)
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students(
        student_id TEXT PRIMARY KEY,
        name TEXT,
        roll TEXT,
        department TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT,
    name TEXT,
    date TEXT,
    time TEXT
    )
    """)

    cursor.execute("""
    DELETE FROM attendance
    WHERE id NOT IN (
        SELECT MIN(id)
        FROM attendance
        GROUP BY student_id, date
    )
    """)

    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_attendance_student_date
    ON attendance(student_id, date)
    """)

    conn.commit()
    conn.close()

create_database()


@app.route("/")
def home():

    if "admin" not in session:
        return redirect("/admin")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    today = datetime.date.today().strftime("%Y-%m-%d")

    cursor.execute(
        "SELECT COUNT(*) FROM attendance WHERE date=?",
        (today,)
    )

    today_attendance = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        total_students=total_students,
        today_attendance=today_attendance
    )


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/save_student", methods=["POST"])
def save_student():

    student_id = request.form["student_id"]
    name = request.form["name"]
    roll = request.form["roll"]
    department = request.form["department"]

    try:
        conn = sqlite3.connect("database.db", timeout=30)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO students VALUES (?,?,?,?)",
            (student_id, name, roll, department)
        )

        conn.commit()

    except sqlite3.Error as e:
        return f"Database Error: {e}"

    finally:
        conn.close()

    return redirect("/capture/" + student_id)
@app.route("/capture/<student_id>")
def capture(student_id):
    return render_template("capture.html", student_id=student_id)


@app.route("/records", methods=["GET", "POST"])
def records():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "POST":

        keyword = request.form["keyword"]

        cursor.execute("""
        SELECT * FROM attendance
        WHERE student_id LIKE ?
        OR name LIKE ?
        OR date LIKE ?
        """, ("%"+keyword+"%", "%"+keyword+"%", "%"+keyword+"%"))

    else:

        cursor.execute("SELECT * FROM attendance")

    records = cursor.fetchall()

    conn.close()

    return render_template("records.html", records=records)
@app.route("/export")
def export():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM attendance")
    rows = cursor.fetchall()

    conn.close()

    filename = "attendance.csv"

    with open(filename, "w", newline="") as file:

        writer = csv.writer(file)

        writer.writerow([
            "ID",
            "Student ID",
            "Name",
            "Date",
            "Time"
        ])

        writer.writerows(rows)

    return send_file(filename, as_attachment=True)

@app.route("/admin")
def admin():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT password FROM admin WHERE username=?",
        (username,)
    )

    admin = cursor.fetchone()

    conn.close()

    if admin and check_password_hash(admin[0], password):

        session["admin"] = username

        return redirect("/")

    flash("Invalid Username or Password", "danger")
    return redirect("/admin")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/admin")

@app.route("/delete/<student_id>")
def delete_student(student_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM students WHERE student_id=?",
        (student_id,)
    )

    conn.commit()
    conn.close()

    folder = os.path.join("dataset", student_id)

    if os.path.exists(folder):
        shutil.rmtree(folder)

    flash("Student deleted successfully.","success")

    return redirect("/students")

@app.route("/students")
def students():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students")
    data = cursor.fetchall()

    conn.close()

    return render_template("students.html", students=data)

@app.route("/edit/<student_id>")
def edit_student(student_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM students WHERE student_id=?",
        (student_id,)
    )

    student = cursor.fetchone()

    conn.close()

    return render_template("edit.html", student=student)

@app.route("/update_student", methods=["POST"])
def update_student():

    student_id = request.form["student_id"]
    name = request.form["name"]
    roll = request.form["roll"]
    department = request.form["department"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE students
        SET name=?, roll=?, department=?
        WHERE student_id=?
    """, (name, roll, department, student_id))

    conn.commit()
    conn.close()

    return redirect("/students")
@app.route("/retake/<student_id>")
def retake_face(student_id):

    session["student_id"]=student_id

    path=os.path.join("dataset",student_id)

    if os.path.exists(path):
        shutil.rmtree(path)

    os.makedirs(path)

    return redirect("/capture/"+student_id)


@app.route("/train")
def train():

    success = train_model()

    if success:
        flash("Model trained successfully.","success")

    return redirect("/")
            

    return """
    <h2>No face images found!</h2>
    <a href="/students">
        <button>Back</button>
    </a>
    """

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "GET":
        return render_template("signup.html")

    username = request.form["username"]
    email = request.form["email"]
    password = generate_password_hash(request.form["password"])

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO admin(username,email,password) VALUES(?,?,?)",
            (username,email,password)
        )

        conn.commit()
        conn.close()

        flash("Account created successfully. Please login.","success")
        return redirect("/admin")

    except sqlite3.IntegrityError:

        conn.close()

        flash("Username or Email already exists!","danger")

        return redirect("/signup")
@app.route("/recognize", methods=["POST"])
def recognize():

    data = request.json["image"]

    image_data = data.split(",")[1]

    image = Image.open(BytesIO(base64.b64decode(image_data)))

    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read("trainer.yml")

    detector = cv2.CascadeClassifier(
        "haarcascade_frontalface_default.xml"
    )

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    faces = detector.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:

        student_id, confidence = recognizer.predict(gray[y:y+h, x:x+w])

        if confidence < 70:

            cursor.execute(
                "SELECT name FROM students WHERE student_id=?",
                (str(student_id),)
            )

            student = cursor.fetchone()

            if student:

                name = student[0]

                today = datetime.date.today().strftime("%Y-%m-%d")
                now = datetime.datetime.now().strftime("%H:%M:%S")

                cursor.execute(
                    "SELECT * FROM attendance WHERE student_id=? AND date=?",
                    (str(student_id), today)
                )

                if cursor.fetchone() is None:

                    cursor.execute(
                        """
                        INSERT INTO attendance(student_id,name,date,time)
                        VALUES(?,?,?,?)
                        """,
                        (str(student_id), name, today, now)
                    )

                    conn.commit()

                conn.close()

                return {
                    "status": "success",
                    "name": name
                }

    conn.close()

    return {
        "status": "unknown"
    }
@app.route("/attendance")
def attendance():
    return render_template("attendance.html")

@app.route("/save_face", methods=["POST"])
def save_face():

    data = request.json

    student_id = data["student_id"]
    image = data["image"]

    image = image.split(",")[1]

    image = base64.b64decode(image)

    image = Image.open(BytesIO(image))

    frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    detector = cv2.CascadeClassifier(
        "haarcascade_frontalface_default.xml"
    )

    faces = detector.detectMultiScale(gray, 1.3, 5)

    folder = os.path.join("dataset", student_id)
    os.makedirs(folder, exist_ok=True)

    for (x, y, w, h) in faces:

        face = gray[y:y+h, x:x+w]

        count = len(os.listdir(folder)) + 1

        cv2.imwrite(
            os.path.join(folder, f"{count}.jpg"),
            face
        )

        return {
            "status": "saved",
            "count": count
        }

    return {
        "status": "no_face"
    }
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

