from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'college_events'

mysql = MySQL(app)

# Login Page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['userid']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        cursor.execute("SELECT * FROM admins WHERE username=%s AND password=%s", (username, password))
        admin = cursor.fetchone()
        cursor.close()
        
        if admin:
            session['loggedin'] = True
            session['username'] = username
            session['user_type'] = 'admin'
            return redirect(url_for('Admin_dashboard'))
        elif user:
            session['loggedin'] = True
            session['username'] = username
            session['user_type'] = 'user'
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

# User Dashboard
@app.route('/user_dashboard')
def user_dashboard():
    if 'loggedin' in session and session['user_type'] == 'user':
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM events")
        events = cursor.fetchall()
        cursor.execute("SELECT * FROM event_registrations WHERE user_id=%s", (session['username'],))
        my_events = cursor.fetchall()
        cursor.close()
        return render_template('user_dashboard.html', events=events, my_events=my_events)
    return redirect(url_for('login'))

# Admin Dashboard
@app.route('/admin_dashboard')
def Admin_dashboard():
    if 'loggedin' in session and session['user_type'] == 'admin':
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM events")
        events = cursor.fetchall()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        cursor.close()
        return render_template('admin_dashboard.html', events=events, users=users)
    return redirect(url_for('login'))

# Register Event
@app.route('/register_event', methods=['POST'])
def register_event():
    if 'loggedin' in session and session['user_type'] == 'user':
        event_id = request.form['event_id']
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        class_section = request.form['class_section_branch']
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO event_registrations (user_id, event_id, name, phone, email, class_section) VALUES (%s, %s, %s, %s, %s, %s)", (session['username'], event_id, name, phone, email, class_section))
        mysql.connection.commit()
        cursor.close()
        flash('Registered successfully!', 'success')
        return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
