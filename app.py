from flask import Flask, render_template, request, jsonify
import db
from datetime import datetime

app = Flask(__name__)

# Initialize Database on startup
db.init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({"status": "error", "message": "Missing start_date or end_date parameters."}), 400
        
    try:
        # Simple date validation
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({"status": "error", "message": "Dates must be in YYYY-MM-DD format."}), 400

    bookings = db.get_bookings_in_range(start_date, end_date)
    return jsonify({"status": "success", "bookings": bookings})

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Invalid request payload."}), 400
        
    required_base_fields = ['faculty_name', 'department', 'phone', 'purpose', 'booking_date']
    for field in required_base_fields:
        if field not in data or not str(data[field]).strip():
            return jsonify({"status": "error", "message": f"Field '{field}' is required and cannot be empty."}), 400
            
    faculty_name = str(data['faculty_name']).strip()
    department = str(data['department']).strip()
    phone = str(data['phone']).strip()
    purpose = str(data['purpose']).strip()
    booking_date = str(data['booking_date']).strip()
    
    try:
        datetime.strptime(booking_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({"status": "error", "message": "booking_date must be in YYYY-MM-DD format."}), 400

    ranges = []
    if 'ranges' in data:
        if not isinstance(data['ranges'], list) or len(data['ranges']) == 0:
            return jsonify({"status": "error", "message": "ranges must be a non-empty list."}), 400
        for item in data['ranges']:
            if 'start_hour' not in item or 'end_hour' not in item:
                return jsonify({"status": "error", "message": "Each range item must contain start_hour and end_hour."}), 400
            try:
                ranges.append({
                    'start_hour': int(item['start_hour']),
                    'end_hour': int(item['end_hour'])
                })
            except ValueError:
                return jsonify({"status": "error", "message": "start_hour and end_hour within ranges must be integers."}), 400
    else:
        if 'start_hour' not in data or 'end_hour' not in data:
            return jsonify({"status": "error", "message": "Missing start_hour and end_hour, or ranges list."}), 400
        try:
            sh = int(data['start_hour'])
            eh = int(data['end_hour'])
            ranges.append({'start_hour': sh, 'end_hour': eh})
        except ValueError:
            return jsonify({"status": "error", "message": "start_hour and end_hour must be integers."}), 400

    # Call db to attempt booking
    success, message = db.add_booking(
        faculty_name=faculty_name,
        department=department,
        phone=phone,
        purpose=purpose,
        booking_date=booking_date,
        ranges=ranges
    )
    
    if success:
        return jsonify({"status": "success", "message": message}), 201
    else:
        return jsonify({"status": "error", "message": message}), 409

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
