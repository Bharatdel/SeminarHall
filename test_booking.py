import unittest
import os
import db

class TestBookingSystem(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Override the database file for testing
        db.DB_FILE = 'test_bookings.db'
        
    def setUp(self):
        # Clear database before each test
        if os.path.exists(db.DB_FILE):
            os.remove(db.DB_FILE)
        db.init_db()

    def tearDown(self):
        # Clean up database after each test
        if os.path.exists(db.DB_FILE):
            os.remove(db.DB_FILE)

    def test_single_hour_booking(self):
        # Book 9 to 10
        success, msg = db.add_booking(
            faculty_name="Dr. Smith",
            department="Computer Science",
            phone="1234567890",
            purpose="Lecture",
            booking_date="2026-08-21",
            start_hour=9,
            end_hour=10
        )
        self.assertTrue(success)
        self.assertEqual(msg, "Booking successful!")
        
        # Verify it exists in range
        bookings = db.get_bookings_in_range("2026-08-21", "2026-08-21")
        self.assertEqual(len(bookings), 1)
        self.assertEqual(bookings[0]['faculty_name'], "Dr. Smith")
        self.assertEqual(bookings[0]['start_hour'], 9)
        self.assertEqual(bookings[0]['end_hour'], 10)

    def test_multi_hour_booking(self):
        # Book 10 to 13 (3 hours)
        success, msg = db.add_booking(
            faculty_name="Dr. Jones",
            department="Electrical Engineering",
            phone="9876543210",
            purpose="Lab exam",
            booking_date="2026-08-21",
            start_hour=10,
            end_hour=13
        )
        self.assertTrue(success)
        
        # Verify overlap checks block a new booking at 11 to 12
        success2, msg2 = db.add_booking(
            faculty_name="Dr. Brown",
            department="Mechanical Engineering",
            phone="1112223333",
            purpose="Seminar",
            booking_date="2026-08-21",
            start_hour=11,
            end_hour=12
        )
        self.assertFalse(success2)
        self.assertIn("already booked", msg2)

    def test_non_overlapping_bookings(self):
        # Book 10 to 12
        success, _ = db.add_booking(
            faculty_name="Dr. Jones",
            department="EE",
            phone="9876543210",
            purpose="A",
            booking_date="2026-08-21",
            start_hour=10,
            end_hour=12
        )
        self.assertTrue(success)
        
        # Book 9 to 10 (consecutive, non-overlapping)
        success2, _ = db.add_booking(
            faculty_name="Dr. Brown",
            department="ME",
            phone="1112223333",
            purpose="B",
            booking_date="2026-08-21",
            start_hour=9,
            end_hour=10
        )
        self.assertTrue(success2)

        # Book 12 to 14 (consecutive, non-overlapping)
        success3, _ = db.add_booking(
            faculty_name="Dr. White",
            department="CS",
            phone="4445556666",
            purpose="C",
            booking_date="2026-08-21",
            start_hour=12,
            end_hour=14
        )
        self.assertTrue(success3)

    def test_overlapping_cases(self):
        # Setup: Book 10 to 12
        db.add_booking("Prof A", "Dept", "123", "P", "2026-08-21", 10, 12)
        
        # Case 1: Exact Overlap (10-12)
        success, _ = db.add_booking("Prof B", "Dept", "123", "P", "2026-08-21", 10, 12)
        self.assertFalse(success)
        
        # Case 2: Partial Overlap Left (9-11)
        success, _ = db.add_booking("Prof B", "Dept", "123", "P", "2026-08-21", 9, 11)
        self.assertFalse(success)
        
        # Case 3: Partial Overlap Right (11-13)
        success, _ = db.add_booking("Prof B", "Dept", "123", "P", "2026-08-21", 11, 13)
        self.assertFalse(success)
        
        # Case 4: Contained Overlap (11-12)
        success, _ = db.add_booking("Prof B", "Dept", "123", "P", "2026-08-21", 11, 12)
        self.assertFalse(success)
        
        # Case 5: Containing Overlap (9-13)
        success, _ = db.add_booking("Prof B", "Dept", "123", "P", "2026-08-21", 9, 13)
        self.assertFalse(success)

    def test_invalid_ranges(self):
        # Start hour greater than end hour
        success, msg = db.add_booking("Prof A", "Dept", "123", "P", "2026-08-21", 12, 10)
        self.assertFalse(success)
        self.assertIn("before end time", msg)
        
        # Out of bounds (starts before 9 AM)
        success, msg = db.add_booking("Prof A", "Dept", "123", "P", "2026-08-21", 8, 10)
        self.assertFalse(success)
        self.assertIn("between 9:00 AM and 4:00 PM", msg)

        # Out of bounds (ends after 4 PM)
        success, msg = db.add_booking("Prof A", "Dept", "123", "P", "2026-08-21", 15, 17)
        self.assertFalse(success)
        self.assertIn("between 9:00 AM and 4:00 PM", msg)

    def test_multi_range_booking(self):
        # Book non-consecutive: 9-10 and 12-14
        ranges = [
            {'start_hour': 9, 'end_hour': 10},
            {'start_hour': 12, 'end_hour': 14}
        ]
        success, msg = db.add_booking(
            faculty_name="Dr. Multi",
            department="CS",
            phone="9990008888",
            purpose="Multiple Seminars",
            booking_date="2026-08-22",
            ranges=ranges
        )
        self.assertTrue(success)
        
        # Verify both are booked in range
        bookings = db.get_bookings_in_range("2026-08-22", "2026-08-22")
        self.assertEqual(len(bookings), 2)
        self.assertEqual(bookings[0]['start_hour'], 9)
        self.assertEqual(bookings[0]['end_hour'], 10)
        self.assertEqual(bookings[1]['start_hour'], 12)
        self.assertEqual(bookings[1]['end_hour'], 14)

        # Verify overlapping any of these ranges fails
        success2, msg2 = db.add_booking(
            faculty_name="Dr. Conflict",
            department="EE",
            phone="123",
            purpose="Lecture",
            booking_date="2026-08-22",
            start_hour=13,
            end_hour=15
        )
        self.assertFalse(success2)
        self.assertIn("already booked", msg2)

if __name__ == '__main__':
    unittest.main()
