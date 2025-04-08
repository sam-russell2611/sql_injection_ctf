from flask import Flask, request, render_template, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

DB_PATH = "database.db"

def init_db():
    if os.path.exists(DB_PATH):
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            balance INTEGER DEFAULT 0,  -- Added balance column
            flag TEXT
        )
    ''')
    # Add users (passwords stored in plain text for demo purposes!)
    c.execute("INSERT INTO users (username, password, balance) VALUES ('james_alvarez33', 'youll_never_guess', 543)")
    c.execute("INSERT INTO users (username, password, balance) VALUES ('sam_russell77', 'hey_get_out_of_here', 42)")
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # 💥 Vulnerable to SQL Injection (classic login bypass)
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute(query)
            user = c.fetchone()
        except Exception as e:
            msg = f"SQL Error: {e}"
            return render_template("login.html", msg=msg)
        
        if user:
            return redirect(url_for('profile', username=username))
        else:
            msg = 'Login failed. Invalid credentials.'
    
    return render_template("login.html", msg=msg)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    username = request.args.get('username')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 💥 Vulnerable to SQL Injection via GET parameter
    query = f"SELECT * FROM users WHERE username = '{username}'"

    # 🕵️ Hint: Can you UNION SELECT other data from the table?
    c.execute(query)
    user = c.fetchone()

    if request.method == 'POST':
        recipient = request.form['recipient']
        amount = int(request.form['amount'])
        
        # 💥 Vulnerable to SQL Injection again (no parameterized query)
        c.execute(f"SELECT balance FROM users WHERE username = '{username}'")
        balance = c.fetchone()[0]

        if balance >= amount:
            # 💥 Vulnerable: Directly modifying the balance (can be manipulated via SQL Injection)
            c.execute(f"UPDATE users SET balance = balance - {amount} WHERE username = '{username}'")
            c.execute(f"UPDATE users SET balance = balance + {amount} WHERE username = '{recipient}'")
            conn.commit()

            # Check if the recipient is 'sam_russell77' and reveal the flag
            flag = ''
            if recipient == 'sam_russell77':
                flag = 'itc101{just1ce_f0r_s@m}'
            
            # 💥 Vulnerable: Fetching balance without parameterized query
            c.execute(f"SELECT balance FROM users WHERE username = '{username}'")
            updated_balance = c.fetchone()[0]

            return render_template("profile.html", user=user, user_balance=updated_balance, flag=flag)
        else:
            # Handle insufficient funds
            msg = "Insufficient balance!"
            return render_template("profile.html", user=user, user_balance=balance, msg=msg)

    # 💥 Vulnerable: Fetching balance without parameterized query
    c.execute(f"SELECT balance FROM users WHERE username = '{username}'")
    balance = c.fetchone()[0]
    
    return render_template("profile.html", user=user, user_balance=balance)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)