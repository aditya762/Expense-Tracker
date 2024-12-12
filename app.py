from flask import Flask, render_template, request, redirect, session
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///transactions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(200), nullable=True)

# Routes
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    transactions = Transaction.query.filter_by(user_id=user_id).all()
    total_expenses = sum(trans.amount for trans in transactions)

    grouped_daily_expenses = {}
    for trans in transactions:
        if trans.date not in grouped_daily_expenses:
            grouped_daily_expenses[trans.date] = 0
        grouped_daily_expenses[trans.date] += trans.amount

    return render_template(
        'index.html',
        transactions=transactions,
        daily_expenses=grouped_daily_expenses.items(),
        total_expenses=total_expenses
    )

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        if User.query.filter_by(username=username).first():
            return "Username already exists!"

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect('/')

        return "Invalid credentials!"

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')

@app.route('/add', methods=['POST'])
def add_transaction():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    date = request.form['date']
    amount = float(request.form['amount'])
    reason = request.form['reason']

    new_transaction = Transaction(user_id=user_id, date=date, amount=amount, reason=reason)
    db.session.add(new_transaction)
    db.session.commit()

    return redirect('/')

@app.route('/split', methods=['GET', 'POST'])
def split_expenses():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        user_id = session['user_id']
        amount = float(request.form['amount'])
        involved_users = request.form.getlist('users')

        if not involved_users:
            return "No users selected for splitting."

        split_amount = amount / len(involved_users)

        for user in involved_users:
            user_obj = User.query.filter_by(username=user).first()
            if user_obj:
                new_transaction = Transaction(
                    user_id=user_obj.id,
                    date=request.form['date'],
                    amount=split_amount,
                    reason=request.form['reason']
                )
                db.session.add(new_transaction)

        db.session.commit()
        return redirect('/')

    all_users = User.query.all()
    return render_template('split.html', users=all_users)

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
