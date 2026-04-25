import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Importing the logic functions from your stego_logic.py
from stego_logic import embed_message, extract_message

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/users.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    # Publicly accessible feed [cite: 9, 21]
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', files=files)

@app.route('/upload', methods=['GET', 'POST'])
@login_required # Only authenticated users may submit [cite: 9, 21]
def upload():
    if request.method == 'POST':
        p_file = request.files['carrier']
        m_file = request.files['message']
        s = int(request.form.get('S', 1024)) # Starting bit [cite: 11]
        l = int(request.form.get('L', 8))    # Periodicity [cite: 11]
        
        p_filename = secure_filename(p_file.filename)
        p_path = os.path.join(app.config['UPLOAD_FOLDER'], p_filename)
        
        # Save message to a temporary location to process it
        m_filename = secure_filename(m_file.filename)
        m_path = os.path.join('/tmp', m_filename) if os.name != 'nt' else os.path.join(os.getenv('TEMP'), m_filename)
        
        p_file.save(p_path)
        m_file.save(m_path)
        
        try:
            # Apply steganography logic [cite: 13, 15]
            result_bits = embed_message(p_path, m_path, s, l, "default")
            with open(p_path, 'wb') as f:
                result_bits.tofile(f)
            flash(f"Message hidden in {p_filename} successfully!")
        except Exception as e:
            flash(f"Error during embedding: {str(e)}")
            
        return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/extract', methods=['GET', 'POST'])
def extract():
    # Reversibility: retrieving the original message 
    if request.method == 'POST':
        p_file = request.files['carrier']
        s = int(request.form.get('S', 1024))
        l = int(request.form.get('L', 8))
        # You need the length of the original message in bits to extract it correctly
        length_bits = int(request.form.get('bits', 0)) 
        
        p_filename = secure_filename(p_file.filename)
        p_path = os.path.join('/tmp', p_filename) if os.name != 'nt' else os.path.join(os.getenv('TEMP'), p_filename)
        p_file.save(p_path)
        
        try:
            extracted_bits = extract_message(p_path, s, l, length_bits)
            output_path = os.path.join('/tmp', 'extracted_msg') if os.name != 'nt' else os.path.join(os.getenv('TEMP'), 'extracted_msg')
            with open(output_path, 'wb') as f:
                extracted_bits.tofile(f)
            return send_file(output_path, as_attachment=True, download_name="extracted_message")
        except Exception as e:
            flash(f"Extraction failed: {str(e)}")
            
    return render_template('extract.html') # Ensure you create this template

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        new_user = User(username=request.form['username'], password=hashed_pw)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please login.")
            return redirect(url_for('login'))
        except:
            flash("Username already exists.")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash("Invalid credentials.")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)