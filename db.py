import sqlite3
import os
from datetime import datetime

DB_FILE = 'bookings.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faculty_name TEXT NOT NULL,
            department TEXT NOT NULL,
            phone TEXT NOT NULL,
            purpose TEXT NOT NULL,
            booking_date TEXT NOT NULL, -- Format: YYYY-MM-DD
            start_hour INTEGER NOT NULL, -- 24h format: 9, 10, 11, etc.
            end_hour INTEGER NOT NULL,   -- 24h format: 10, 11, 12, etc.
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_bookings_in_range(start_date, end_date):
    """
    Fetches all bookings between start_date and end_date (inclusive).
    Dates should be in 'YYYY-MM-DD' format.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, faculty_name, department, phone, purpose, booking_date, start_hour, end_hour, created_at
        FROM bookings
        WHERE booking_date >= ? AND booking_date <= ?
        ORDER BY booking_date ASC, start_hour ASC
    ''', (start_date, end_date))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def check_overlap(cursor, booking_date, start_hour, end_hour):
    """
    Checks if there are any bookings on the specified date that overlap with start_hour to end_hour.
    Must be run inside an open transaction.
    """
    cursor.execute('''
        SELECT COUNT(*) as count
        FROM bookings
        WHERE booking_date = ? AND start_hour < ? AND end_hour > ?
    ''', (booking_date, end_hour, start_hour))
    row = cursor.fetchone()
    return row['count'] > 0

def add_booking(faculty_name, department, phone, purpose, booking_date, start_hour=None, end_hour=None, ranges=None):
    """
    Attempts to add booking ranges. Checks for overlaps in a transaction-safe manner.
    Can accept a single range via start_hour and end_hour, or a list of ranges via ranges.
    """
    # ----- New validation: disallow past dates/times -----
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    current_hour = now.hour
    if booking_date < today_str:
        return False, "Cannot book a date in the past."
    if booking_date == today_str:
        # If any requested start hour is <= current hour, reject (slot already started or passed)
        if ranges:
            for r in ranges:
                if r['start_hour'] <= current_hour:
                    return False, "Cannot book slots that have already started or passed for today."
        else:
            if start_hour is not None and start_hour <= current_hour:
                return False, "Cannot book a slot that has already started or passed for today."
    
    if ranges is None:
        if start_hour is None or end_hour is None:
            return False, "Either a start/end hour or a list of ranges must be provided."
        ranges = [{'start_hour': start_hour, 'end_hour': end_hour}]

    if not ranges:
        return False, "No slots selected for booking."

    for r in ranges:
        sh = r['start_hour']
        eh = r['end_hour']
        if sh >= eh:
            return False, f"Start time ({sh}) must be before end time ({eh})."
        if sh < 9 or eh > 16:
            return False, "Booking time must be between 9:00 AM and 4:00 PM."
        
    conn = get_db_connection()
    try:
        # Acquire an immediate write lock to prevent race conditions
        conn.execute('BEGIN IMMEDIATE TRANSACTION')
        cursor = conn.cursor()
        
        # Check overlaps for all ranges
        for r in ranges:
            sh = r['start_hour']
            eh = r['end_hour']
            if check_overlap(cursor, booking_date, sh, eh):
                conn.rollback()
                return False, "One or more of the selected slots are already booked."
            
        # Perform insert for all ranges
        for r in ranges:
            sh = r['start_hour']
            eh = r['end_hour']
            cursor.execute('''
                INSERT INTO bookings (faculty_name, department, phone, purpose, booking_date, start_hour, end_hour)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (faculty_name, department, phone, purpose, booking_date, sh, eh))
        
        conn.commit()
        return True, "Booking successful!"
    except sqlite3.Error as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()
