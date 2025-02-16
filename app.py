from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_mysqldb import MySQL
import MySQLdb.cursors
import io
import pandas as pd
from datetime import datetime

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

@app.route("/admin_register")
def admin_register():
    return render_template('admin_register.html')

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

# Add Event
@app.route('/add_event', methods=['POST'])
def add_event():
    if 'loggedin' in session and session['user_type'] == 'admin':
        event_name = request.form['event_name']
        event_date = request.form['event_date']
        event_time = request.form['event_time']
        event_location = request.form['event_location']
        event_purpose = request.form['event_purpose']
        event_audience = request.form['event_audience']
        event_activities = request.form['event_activities']
        event_usps = request.form['event_usps']
        
        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO events (name, date, time, location, purpose, target_audience, key_activities, usps) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (event_name, event_date, event_time, event_location, event_purpose, event_audience, event_activities, event_usps)
        )
        mysql.connection.commit()
        cursor.close()
        flash('Event added successfully!', 'success')
        return redirect(url_for('Admin_dashboard'))
    return redirect(url_for('login'))

# Delete Event
@app.route('/delete_event/<int:event_id>')
def delete_event(event_id):
    if 'loggedin' in session and session['user_type'] == 'admin':
        cursor = mysql.connection.cursor()
        # First delete related registrations
        cursor.execute("DELETE FROM event_registrations WHERE event_id=%s", (event_id,))
        # Then delete the event
        cursor.execute("DELETE FROM events WHERE id=%s", (event_id,))
        mysql.connection.commit()
        cursor.close()
        flash('Event deleted successfully!', 'success')
        return redirect(url_for('Admin_dashboard'))
    return redirect(url_for('login'))

# Download Events as Excel
@app.route('/download_events')
def download_events():
    if 'loggedin' in session and session['user_type'] == 'admin':
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM events")
        events = cursor.fetchall()
        cursor.close()
        
        # Create DataFrame
        df = pd.DataFrame(events, columns=['ID', 'Name', 'Date', 'Time', 'Location', 'Purpose', 'Target Audience', 'Key Activities', 'USPs'])
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Events')
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'events_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
    return redirect(url_for('login'))

# Download Registrations as Excel
@app.route('/download_registrations')
def download_registrations():
    if 'loggedin' in session and session['user_type'] == 'admin':
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT r.id, e.name as event_name, r.user_id, r.name, r.phone, r.email, r.class_section
            FROM event_registrations r
            JOIN events e ON r.event_id = e.id
        """)
        registrations = cursor.fetchall()
        cursor.close()
        
        # Create DataFrame
        df = pd.DataFrame(registrations, columns=['ID', 'Event Name', 'User ID', 'Name', 'Phone', 'Email', 'Class/Section'])
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Registrations')
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'registrations_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
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
