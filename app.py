from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

TOTAL_SLOTS = 10

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ----------------------------
# DATABASE MODELS
# ----------------------------

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), unique=True, nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)

class EntryLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), nullable=False)
    entry_time = db.Column(db.DateTime, nullable=False)
    exit_time = db.Column(db.DateTime, nullable=True)

# ----------------------------
# ROUTES
# ----------------------------

@app.route('/')
def home():
    return render_template("index.html")

# ----------------------------
# REGISTER VEHICLE
# ----------------------------

@app.route('/register', methods=['POST'])
def register_vehicle():
    data = request.get_json()

    vehicle_number = data.get('vehicle_number')
    owner_name = data.get('owner_name')

    if not vehicle_number or not owner_name:
        return jsonify({"error": "Missing data"}), 400

    existing_vehicle = Vehicle.query.filter_by(vehicle_number=vehicle_number).first()
    if existing_vehicle:
        return jsonify({"error": "Vehicle already registered"}), 400

    new_vehicle = Vehicle(
        vehicle_number=vehicle_number,
        owner_name=owner_name
    )

    db.session.add(new_vehicle)
    db.session.commit()

    return jsonify({"message": "Vehicle registered successfully"})

# ----------------------------
# VEHICLE ENTRY
# ----------------------------

@app.route('/entry', methods=['POST'])
def vehicle_entry():
    data = request.get_json()
    vehicle_number = data.get('vehicle_number')

    if not vehicle_number:
        return jsonify({"error": "Vehicle number required"}), 400

    vehicle = Vehicle.query.filter_by(vehicle_number=vehicle_number).first()

    if not vehicle:
        return jsonify({"status": "DENIED", "message": "Vehicle not registered"}), 403

    # Check if vehicle already inside
    active_entry = EntryLog.query.filter(
        EntryLog.vehicle_number == vehicle_number,
        EntryLog.exit_time.is_(None)
    ).first()

    if active_entry:
        return jsonify({"status": "DENIED", "message": "Vehicle already inside"}), 403

    new_entry = EntryLog(
        vehicle_number=vehicle_number,
        entry_time=datetime.now(),
        exit_time=None
    )

    db.session.add(new_entry)
    db.session.commit()

    return jsonify({"status": "ALLOWED", "message": "Entry logged successfully"})

# ----------------------------
# VEHICLE EXIT
# ----------------------------

@app.route('/exit', methods=['POST'])
def vehicle_exit():
    data = request.get_json()
    vehicle_number = data.get('vehicle_number')

    if not vehicle_number:
        return jsonify({"error": "Vehicle number required"}), 400

    active_entry = EntryLog.query.filter(
        EntryLog.vehicle_number == vehicle_number,
        EntryLog.exit_time.is_(None)
    ).first()

    if not active_entry:
        return jsonify({"status": "DENIED", "message": "Vehicle not inside"}), 403

    active_entry.exit_time = datetime.now()
    db.session.commit()

    return jsonify({"status": "ALLOWED", "message": "Exit logged successfully"})

# ----------------------------
# VIEW ALL LOGS
# ----------------------------

@app.route('/logs', methods=['GET'])
def view_logs():
    logs = EntryLog.query.all()

    result = []

    for log in logs:
        result.append({
            "vehicle_number": log.vehicle_number,
            "entry_time": log.entry_time.strftime("%Y-%m-%d %H:%M:%S"),
            "exit_time": log.exit_time.strftime("%Y-%m-%d %H:%M:%S") if log.exit_time else None
        })

    return jsonify(result)

# ----------------------------
# VIEW ACTIVE VEHICLES
# ----------------------------

@app.route('/active', methods=['GET'])
def view_active():
    active_logs = EntryLog.query.filter(
        EntryLog.exit_time.is_(None)
    ).all()

    result = []

    for log in active_logs:
        result.append({
            "vehicle_number": log.vehicle_number,
            "entry_time": log.entry_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    return jsonify(result)

# ----------------------------
# START SERVER
# ----------------------------

@app.route('/active_vehicles')
def active_vehicles():

    vehicles = EntryLog.query.filter(
        EntryLog.exit_time.is_(None)
    ).all()

    result = []

    for v in vehicles:
        result.append({
            "vehicle_number": v.vehicle_number,
            "entry_time": v.entry_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    return jsonify(result)

@app.route('/parking_status')
def parking_status():

    active_count = EntryLog.query.filter(
        EntryLog.exit_time.is_(None)
    ).count()

    available = TOTAL_SLOTS - active_count

    return jsonify({
        "total_slots": TOTAL_SLOTS,
        "occupied": active_count,
        "available": available
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)