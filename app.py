from flask import Flask, render_template, request, redirect, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "careersync123"
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="30363",
    database="careersync"
)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cursor = db.cursor()

        # Admin login
        cursor.execute(
            "SELECT * FROM admins WHERE username=%s AND password=%s",
            (email, password)
        )
        admin = cursor.fetchone()

        if admin:
            return redirect('/admin')

                # Student login
        cursor.execute(
            "SELECT * FROM students WHERE email=%s AND password=%s",
            (email, password)
        )

        student = cursor.fetchone()

        if student:
            session['student_id'] = student[0]
            session['student_name'] = student[1]

            return redirect('/dashboard')

        return "Invalid Login Credentials"

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        cursor = db.cursor()

        if role == "student":

            cursor.execute(
                """
                INSERT INTO students(name,email,password)
                VALUES(%s,%s,%s)
                """,
                (name, email, password)
            )

        else:

            cursor.execute(
                """
                INSERT INTO admins(username,password)
                VALUES(%s,%s)
                """,
                (email, password)
            )

        db.commit()

        return redirect('/')

    return render_template('signup.html')


@app.route('/dashboard')
def dashboard():

    cursor = db.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM opportunities"
    )

    total = cursor.fetchone()[0]

    return render_template(
        'dashboard.html',
        total=total
    )


@app.route('/opportunities')
def opportunities():
    student_id = session['student_id']

    cursor = db.cursor()

    cursor.execute(
    """
    SELECT
        o.id,
        o.title,
        o.category,
        o.deadline,
        a.id
    FROM opportunities o
    LEFT JOIN applications a
        ON o.id = a.opportunity_id
        AND a.student_id = %s
    """,
    (student_id,)
)
    opportunities = cursor.fetchall()

    return render_template(
        'opportunities.html',
        opportunities=opportunities
    )


@app.route('/apply/<int:opp_id>', methods=['POST'])
def apply(opp_id):

    student_id = session['student_id']

    cursor = db.cursor()

    # Check if already applied
    cursor.execute(
        """
        SELECT *
        FROM applications
        WHERE student_id=%s
        AND opportunity_id=%s
        """,
        (student_id, opp_id)
    )

    existing = cursor.fetchone()

    if not existing:

        cursor.execute(
            """
            INSERT INTO applications
            (student_id, opportunity_id, status)
            VALUES (%s,%s,%s)
            """,
            (student_id, opp_id, "Applied")
        )

        db.commit()

    return redirect('/applications')


@app.route('/applications')
def applications():

    if 'student_id' not in session:
        return redirect('/')

    student_id = session['student_id']

    cursor = db.cursor()

    cursor.execute("""
        SELECT
            o.title,
            a.status
        FROM applications a
        JOIN opportunities o
            ON a.opportunity_id = o.id
        WHERE a.student_id = %s
    """, (student_id,))

    applications = cursor.fetchall()

    return render_template(
        'applications.html',
        applications=applications
    )


@app.route('/admin')
def admin():

    cursor = db.cursor()

    cursor.execute(
        "SELECT id, title, category, deadline FROM opportunities"
    )

    opportunities = cursor.fetchall()

    return render_template(
        "admin.html",
        opportunities=opportunities
    )


@app.route('/admin/students')
def students():

    cursor = db.cursor()

    cursor.execute("""
    SELECT
        s.name,
        s.email,
        o.title,
        a.status
    FROM applications a
    JOIN students s
        ON a.student_id = s.id
    JOIN opportunities o
        ON a.opportunity_id = o.id
    ORDER BY s.name
""")

    students = cursor.fetchall()

    return render_template(
        "students.html",
        students=students
    )


@app.route('/add', methods=['GET', 'POST'])
def add():

    if request.method == 'POST':

        title = request.form['title']
        category = request.form['category']
        deadline = request.form['deadline']

        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO opportunities
            (title, category, deadline)
            VALUES (%s,%s,%s)
            """,
            (title, category, deadline)
        )

        db.commit()

        return redirect('/admin')

    return render_template('add.html')


@app.route('/delete/<int:id>')
def delete(id):

    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM opportunities WHERE id=%s",
        (id,)
    )

    db.commit()

    return redirect('/admin')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):

    cursor = db.cursor()

    if request.method == 'POST':

        title = request.form['title']
        category = request.form['category']
        deadline = request.form['deadline']

        cursor.execute(
            """
            UPDATE opportunities
            SET title=%s,
                category=%s,
                deadline=%s
            WHERE id=%s
            """,
            (title, category, deadline, id)
        )

        db.commit()

        return redirect('/admin')

    cursor.execute(
        "SELECT * FROM opportunities WHERE id=%s",
        (id,)
    )

    opp = cursor.fetchone()

    return render_template(
        'edit.html',
        opp=opp
    )


if __name__ == "__main__":
    app.run(debug=True)