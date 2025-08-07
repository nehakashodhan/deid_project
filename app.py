from flask import Flask, request, render_template, send_file
import qrcode
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/medical_reports'
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = sqlite3.connect('deid.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT, dob TEXT, allergies TEXT, emergency_contact TEXT,
                 blood_group TEXT, medical_report_path TEXT)''')
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        allergies = request.form['allergies']
        emergency_contact = request.form['emergency_contact']
        blood_group = request.form['blood_group']
        
        # Handle PDF upload
        if 'medical_report' not in request.files:
            medical_report_path = None
        else:
            file = request.files['medical_report']
            if file.filename == '':
                medical_report_path = None
            elif file and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                medical_report_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(medical_report_path)
            else:
                medical_report_path = None
        
        conn = sqlite3.connect('deid.db')
        c = conn.cursor()
        c.execute('''INSERT INTO users (name, dob, allergies, emergency_contact, blood_group, medical_report_path)
                     VALUES (?, ?, ?, ?, ?, ?)''', (name, dob, allergies, emergency_contact, blood_group, medical_report_path))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        
        qr_data = f"Name: {name}\nDOB: {dob}\nAllergies: {allergies}\nEmergency Contact: {emergency_contact}\nBlood Group: {blood_group}\nMedical Report: {medical_report_path if medical_report_path else 'Not uploaded'}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill='black', back_color='white')
        qr_path = f"static/qr_codes/{user_id}.png"
        os.makedirs('static/qr_codes', exist_ok=True)
        qr_img.save(qr_path)
        
        with open('static/qr_codes/qr_codes.txt', 'a') as f:
            f.write(f"User ID: {user_id}, QR Path: {qr_path}, Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        
        return render_template('success.html', user_id=user_id, qr_path=qr_path, medical_report_path=medical_report_path)
    
    return render_template('index.html')

@app.route('/profile/<int:user_id>')
def profile(user_id):
    conn = sqlite3.connect('deid.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    
    if user:
        return render_template('view.html', user=user)
    return "User not found", 404

@app.route('/qr/<int:user_id>')
def download_qr(user_id):
    qr_path = f"static/qr_codes/{user_id}.png"
    if os.path.exists(qr_path):
        return send_file(qr_path, as_attachment=True)
    return "QR code not found", 404

@app.route('/medical_report/<int:user_id>')
def download_medical_report(user_id):
    conn = sqlite3.connect('deid.db')
    c = conn.cursor()
    c.execute('SELECT medical_report_path FROM users WHERE id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    
    if result and result[0] and os.path.exists(result[0]):
        return send_file(result[0], as_attachment=True)
    return "Medical report not found", 404

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('static/qr_codes', exist_ok=True)
    init_db()
    app.run(debug=True)