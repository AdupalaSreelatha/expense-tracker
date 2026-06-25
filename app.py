from flask import Flask, render_template, request, redirect, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "expensetracker"

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="2004",
    database="expense_tracker"
)

cursor = db.cursor()

@app.route('/')
def home():
    return redirect('/login')


# ---------------- REGISTER ROUTE ----------------

@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        sql = """
        INSERT INTO users(username,email,password)
        VALUES(%s,%s,%s)
        """

        cursor.execute(sql,(username,email,password))
        db.commit()

        return redirect('/login')

    return render_template('register.html')


# ---------------- LOGIN ROUTE ----------------

@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        sql = """
        SELECT * FROM users
        WHERE email=%s AND password=%s
        """

        cursor.execute(sql, (email, password))

        user = cursor.fetchone()

        if user:
            session['user_id'] = user[0]
            return redirect('/dashboard')

        else:
            return render_template(
                'login.html',
                error="Invalid Email or Password. Please register first."
            )

    return render_template('login.html')


# ---------------- DASHBOARD ROUTE ----------------
@app.route('/dashboard')
def dashboard():

    user_id = session.get('user_id')

    if not user_id:
        return redirect('/login')

    # Total Expenses
    cursor.execute(
        "SELECT SUM(amount) FROM expenses WHERE user_id=%s",
        (user_id,)
    )

    total_expenses = cursor.fetchone()[0]

    if total_expenses is None:
        total_expenses = 0

    # Latest Budget
    cursor.execute(
        """
        SELECT monthly_budget
        FROM budget
        WHERE user_id=%s
        ORDER BY budget_id DESC
        LIMIT 1
        """,
        (user_id,)
    )

    budget = cursor.fetchone()

    monthly_budget = budget[0] if budget else 0

    # Remaining Budget
    budget_remaining = monthly_budget - total_expenses

    # Savings
    savings = max(0, budget_remaining)

    return render_template(
        'dashboard.html',
        monthly_budget=monthly_budget,
        total_expenses=total_expenses,
        budget_remaining=budget_remaining,
        savings=savings
    )

# ----------------- ADD EXPENSES ROUTE ----------------

@app.route('/add_expense', methods=['GET','POST'])
def add_expense():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    if request.method == 'POST':

        category = request.form['category']
        amount = request.form['amount']
        description = request.form['description']
        date = request.form['date']
        sql = """
INSERT INTO expenses
(user_id,category,amount,description,expense_date)
VALUES(%s,%s,%s,%s,%s)
"""
        cursor.execute(
            sql,
            (
                session['user_id'],
                category,
                amount,
                description,
                date
            )
        )

        db.commit()

        return redirect('/expenses')

    return render_template('add_expense.html')


#-------------------- EXPENSES ROUTE ----------------

@app.route('/expenses')
def expenses():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    sql = """
    SELECT *
    FROM expenses
    WHERE user_id=%s
    """

    cursor.execute(
        sql,
        (session['user_id'],)
    )

    data = cursor.fetchall()

    return render_template(
        'expenses.html',
        expenses=data
    )

#----------------- DELETE EXPENSE ROUTE ----------------


@app.route('/delete_expense/<int:id>')
def delete_expense(id):

    user_id = session.get('user_id')

    cursor.execute(
        "DELETE FROM expenses WHERE expense_id=%s",
        (id,)
    )

    db.commit()

    # Check remaining expenses
    cursor.execute(
        "SELECT COUNT(*) FROM expenses WHERE user_id=%s",
        (user_id,)
    )

    count = cursor.fetchone()[0]

    # If no expenses remain, clear budget too
    if count == 0:

        cursor.execute(
            "DELETE FROM budget WHERE user_id=%s",
            (user_id,)
        )

        db.commit()

    return redirect('/expenses')

#----------------- EDIT EXPENSE ROUTE ----------------

@app.route('/edit_expense/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):

    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    if request.method == 'POST':

        category = request.form['category']
        amount = request.form['amount']
        description = request.form['description']
        date = request.form['date']

        sql = """
        UPDATE expenses
        SET category=%s,
            amount=%s,
            description=%s,
            expense_date=%s
        WHERE expense_id=%s
        """

        cursor.execute(
            sql,
            (
                category,
                amount,
                description,
                date,
                id
            )
        )

        db.commit()

        return redirect('/expenses')

    sql = """
    SELECT *
    FROM expenses
    WHERE expense_id=%s
    """

    cursor.execute(sql, (id,))
    expense = cursor.fetchone()

    return render_template(
        'edit_expense.html',
        expense=expense
    )

#----------------- SET BUDGET ROUTE ----------------
@app.route('/set_budget', methods=['GET', 'POST'])
def set_budget():

    user_id = session.get('user_id')

    if not user_id:
        return redirect('/login')

    if request.method == 'POST':

        amount = request.form['amount']

        sql = """
INSERT INTO budget(user_id, monthly_budget)
VALUES(%s,%s)
"""

        cursor.execute(sql, (user_id, amount))
        db.commit()

        return redirect('/dashboard')

    return render_template('set_budget.html')
@app.route('/clear_budget')
def clear_budget():

    user_id = session.get('user_id')

    if not user_id:
        return redirect('/login')

    cursor.execute(
        "DELETE FROM budget WHERE user_id=%s",
        (user_id,)
    )

    db.commit()

    return redirect('/dashboard')


#----------------- BUDGET REMAINING ROUTE ----------------
@app.route('/budget_remaining')
def budget_remaining():

    user_id = session.get('user_id')

    if not user_id:
        return redirect('/login')

    cursor.execute("""
        SELECT monthly_budget
        FROM budget
        WHERE user_id=%s
        ORDER BY budget_id DESC
        LIMIT 1
    """, (user_id,))

    budget = cursor.fetchone()

    monthly_budget = budget[0] if budget else 0

    cursor.execute("""
        SELECT SUM(amount)
        FROM expenses
        WHERE user_id=%s
    """, (user_id,))

    total = cursor.fetchone()[0]

    if total is None:
        total = 0

    remaining = monthly_budget - total

    return render_template(
        'budget_remaining.html',
        monthly_budget=monthly_budget,
        total=total,
        remaining=remaining
    )

#----------------- BUDGET ALERT ROUTE ----------------
@app.route('/budget_alert')
def budget_alert():

    user_id = session.get('user_id')

    if not user_id:
        return redirect('/login')

    cursor.execute("""
        SELECT monthly_budget
        FROM budget
        WHERE user_id=%s
        ORDER BY budget_id DESC
        LIMIT 1
    """, (user_id,))

    budget = cursor.fetchone()

    monthly_budget = budget[0] if budget else 0

    cursor.execute("""
        SELECT SUM(amount)
        FROM expenses
        WHERE user_id=%s
    """, (user_id,))

    total = cursor.fetchone()[0]

    if total is None:
        total = 0

    alert = total > monthly_budget

    return render_template(
        'budget_alert.html',
        alert=alert,
        monthly_budget=monthly_budget,
        total=total
    )

#----------------- SAVINGS ROUTE ----------------
@app.route('/savings')
def savings():

    user_id = session.get('user_id')

    if not user_id:
        return redirect('/login')

    cursor.execute("""
        SELECT monthly_budget
        FROM budget
        WHERE user_id=%s
        ORDER BY budget_id DESC
        LIMIT 1
    """, (user_id,))

    budget = cursor.fetchone()

    monthly_budget = budget[0] if budget else 0

    cursor.execute("""
        SELECT SUM(amount)
        FROM expenses
        WHERE user_id=%s
    """, (user_id,))

    total = cursor.fetchone()[0]

    if total is None:
        total = 0

    savings = max(0, monthly_budget - total)

    return render_template(
        'savings.html',
        savings=savings
    )

#----------------- DAILY REPORT ROUTE ----------------
@app.route('/daily_report')
def daily_report():

    user_id = session.get('user_id')

    if not user_id:
        return redirect('/login')

    cursor.execute("""
        SELECT expense_date,
               SUM(amount)
        FROM expenses
        WHERE user_id=%s
        GROUP BY expense_date
        ORDER BY expense_date DESC
    """,(user_id,))

    data = cursor.fetchall()

    return render_template(
        'daily_report.html',
        data=data
    )

#----------------- MONTHLY REPORT ROUTE ----------------
@app.route('/monthly_report')
def monthly_report():

    user_id = session.get('user_id')

    if not user_id:
        return redirect('/login')

    cursor.execute("""
        SELECT DATE_FORMAT(expense_date,'%Y-%m') AS month,
               SUM(amount)
        FROM expenses
        WHERE user_id=%s
        GROUP BY month
        ORDER BY month DESC
    """,(user_id,))

    data = cursor.fetchall()

    return render_template(
        'monthly_report.html',
        data=data
    )

#----------------- YEARLY REPORT ROUTE ----------------
@app.route('/yearly_report')
def yearly_report():

    user_id = session.get('user_id')

    if not user_id:
        return redirect('/login')

    cursor.execute("""
        SELECT YEAR(expense_date),
               SUM(amount)
        FROM expenses
        WHERE user_id=%s
        GROUP BY YEAR(expense_date)
        ORDER BY YEAR(expense_date) DESC
    """,(user_id,))

    data = cursor.fetchall()

    return render_template(
        'yearly_report.html',
        data=data
    )
# ----------------- LOGOUT ROUTE ----------------
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')

# ---------------- RUN APP ----------------

if __name__ == "__main__":
    app.run(debug=True)