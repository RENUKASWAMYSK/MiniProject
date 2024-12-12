from flask import Flask, render_template, redirect, request, url_for, flash
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import UserMixin
from bson.objectid import ObjectId

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config["MONGO_URI"] = "mongodb://localhost:27017/salon_db"
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Google OAuth setup
google_bp = make_google_blueprint(client_id='YOUR_GOOGLE_CLIENT_ID', client_secret='YOUR_GOOGLE_CLIENT_SECRET', redirect_to='google_login')
app.register_blueprint(google_bp, url_prefix='/google_login')

# User class
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.email = user_data['email']
        self.password = user_data['password']

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

# Home route
@app.route('/')
@login_required
def home():
    return render_template('homepage.html')

# Service pages
@app.route('/index2')
def haircut():
    return render_template('haircut.html')

@app.route('/index3')
def haircolor():
    return render_template('haircolor.html')

@app.route('/index4')
def beard_lineup():
    return render_template('beard_Lineup.html')
@app.route('/short')
def short_haircut():
    return render_template('short_haircut.html')
# Default costs for services
service_costs = {
    "long_haircut": 150,
    "short_haircut": 150,
    "beard_trim": 100,
    "hair_color": 140
}

# Book appointment
@app.route('/book_appointment', methods=['GET', 'POST'])
def book_appointment():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        barber = request.form['barber']
        service = request.form['service']
        date = request.form['date']
        time = request.form['time']

        existing_appointment = mongo.db.appointments.find_one({"barber":barber,"date":date,"time":time})
        if existing_appointment:
            flash(f"Slot already taken for {barber} at {time} on {date}.Please choose another slot","error")
            return render_template('book_appointment.html')
        cost = service_costs.get(service, 0)

        appointment = {
            'name': name,
            'email': email,
            'phone': phone,
            'service': service,
            'barber':barber,
            'date': date,
            'time': time,
            'cost': cost
        }
        mongo.db.appointments.insert_one(appointment)

        flash(f'Appointment booked successfully! Cost: ₹{cost}', 'success')
        return redirect(url_for('list_appointments'))
    
    barbers = ["Barber A","Barber B","Barber C"]
    return render_template('book_appointment.html',barbers=barbers)

# Read: List All Appointments
@app.route('/appointments')
def list_appointments():
    appointments = mongo.db.appointments.find()
    return render_template('list_appointment.html', appointments=appointments)

# Update: Edit Appointment
@app.route('/edit_appointment/<appointment_id>', methods=['GET', 'POST'])
def edit_appointment(appointment_id):
    appointment = mongo.db.appointments.find_one({'_id': ObjectId(appointment_id)})

    if request.method == 'POST':
        updated_data = {
            'name': request.form['name'],
            'email': request.form['email'],
            'phone': request.form['phone'],
            'service': request.form['service'],
            'date': request.form['date'],
            'time': request.form['time']
        }
        mongo.db.appointments.update_one({'_id': ObjectId(appointment_id)}, {'$set': updated_data})

        flash('Appointment updated successfully!', 'success')
        return redirect(url_for('list_appointments'))

    return render_template('edit_appointment.html', appointment=appointment)

# Delete: Remove Appointment
@app.route('/delete_appointment/<appointment_id>', methods=['POST'])
def delete_appointment(appointment_id):
    mongo.db.appointments.delete_one({'_id': ObjectId(appointment_id)})
    flash('Appointment deleted successfully!', 'success')
    return redirect(url_for('list_appointments'))

# User Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        hashpwd = bcrypt.generate_password_hash(password).decode("utf-8")
        user = mongo.db.users.find_one({"email": email})
        if user:
            return "User already exists!"
        mongo.db.users.insert_one({"email": email, "password": hashpwd})
        return redirect(url_for('login'))
    return render_template('signup.html')

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_data = mongo.db.users.find_one({"email": email})
        if user_data:
            if bcrypt.check_password_hash(user_data['password'], password):
                user = User(user_data)
                login_user(user)
                return redirect(url_for('home'))
            else:
                return "Invalid password!"
        else:
            return "Invalid username!"
    return render_template('login.html')

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)