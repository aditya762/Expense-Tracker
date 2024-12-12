from flask import Flask, render_template, request, redirect
from collections import defaultdict

app = Flask(__name__)

# Data storage
transactions = []  # List of transactions
users = set()  # Dynamic set of users
users.add("User1")  # Example initial user
daily_expenses = defaultdict(lambda: defaultdict(float))  # Nested dict: {user: {date: total_expense}}

@app.route('/')
def home():
    total_expenses = sum(trans['amount'] for trans in transactions)
    grouped_daily_expenses = {
        date: sum(daily_expenses[user][date] for user in users)
        for date in {date for user_expenses in daily_expenses.values() for date in user_expenses}
    }
    user_expenses = {
        user: sum(daily_expenses[user][date] for date in daily_expenses[user])
        for user in users
    }
    return render_template(
        'index.html',
        transactions=transactions,
        daily_expenses=grouped_daily_expenses.items(),
        total_expenses=total_expenses,
        user_expenses=user_expenses,
        users=users
    )

@app.route('/user/<username>')
def user_transactions(username):
    user_transactions = [trans for trans in transactions if trans['user'] == username]
    user_daily_expenses = {
        date: daily_expenses[username][date] for date in daily_expenses[username]
    }
    total_user_expenses = sum(user_daily_expenses.values())
    return render_template(
        'user.html',
        username=username,
        transactions=user_transactions,
        daily_expenses=user_daily_expenses.items(),
        total_expenses=total_user_expenses,
    )

@app.route('/add', methods=['POST'])
def add_transaction():
    user = request.form['user']
    if user not in users:
        users.add(user)

    date = request.form['date']
    amount = float(request.form['amount'])
    reason = request.form['reason']

    # Append to transactions list
    transactions.append({
        'user': user,
        'date': date,
        'amount': amount,
        'reason': reason,
    })

    # Update daily expenses
    daily_expenses[user][date] += amount

    return redirect('/')

@app.route('/split', methods=['GET', 'POST'])
def split_expenses():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        involved_users = request.form.getlist('users')

        if not involved_users:
            return render_template('split.html', message="No users selected for splitting.", users=users)

        split_amount = amount / len(involved_users)

        for user in involved_users:
            date = request.form['date']  # Assuming the date is entered in the form
            reason = request.form['reason']  # Reason for splitting
            transactions.append({
                'user': user,
                'date': date,
                'amount': split_amount,
                'reason': reason,
            })
            daily_expenses[user][date] += split_amount

        return redirect('/')

    return render_template('split.html', users=users)

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
