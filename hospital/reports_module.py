import mysql.connector
from mysql.connector import Error
from hospital.config import get_connection
from hospital.exceptions import HospitalAppError


def get_dashboard_stats():
    """
    Fetches high-level key metrics for the Dashboard view.
    Returns a dictionary of counts and totals.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Total Active Patients
        cursor.execute("SELECT COUNT(*) FROM patients WHERE status = 'ACTIVE'")
        total_patients = cursor.fetchone()[0]
        
        # 2. Total Active Doctors
        cursor.execute("SELECT COUNT(*) FROM doctors WHERE status = 'ACTIVE'")
        active_doctors = cursor.fetchone()[0]
        
        # 3. Total Departments
        cursor.execute("SELECT COUNT(*) FROM departments")
        total_departments = cursor.fetchone()[0]
        
        # 4. Today's Appointments Count
        cursor.execute("SELECT COUNT(*) FROM appointments WHERE appointment_date = CURDATE()")
        todays_appointments = cursor.fetchone()[0]
        
        # 5. Pending Bills Count & Amount
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(amount), 0) 
            FROM bills WHERE payment_status = 'PENDING'
        """)
        pending_row = cursor.fetchone()
        pending_bills_count = pending_row[0]
        pending_bills_amount = float(pending_row[1])
        
        # 6. Total Collected Revenue
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) 
            FROM bills WHERE payment_status = 'PAID'
        """)
        total_revenue = float(cursor.fetchone()[0])
        
        return {
            "total_patients": total_patients,
            "active_doctors": active_doctors,
            "total_departments": total_departments,
            "todays_appointments": todays_appointments,
            "pending_bills_count": pending_bills_count,
            "pending_bills_amount": pending_bills_amount,
            "total_revenue": total_revenue
        }
    except Error as e:
        raise HospitalAppError(f"Database error fetching dashboard stats: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_today_appointments(doctor_id=None, dept_id=None):
    """
    Fetches today's appointments, with optional filtering by doctor or department.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                a.appointment_id, a.time_slot, a.status, a.notes,
                p.patient_name, p.phone AS patient_phone,
                d.doctor_name, dept.dept_name
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            JOIN departments dept ON d.dept_id = dept.dept_id
            WHERE a.appointment_date = CURDATE()
        """
        params = []
        if doctor_id:
            query += " AND a.doctor_id = %s"
            params.append(doctor_id)
        if dept_id:
            query += " AND d.dept_id = %s"
            params.append(dept_id)
            
        query += " ORDER BY a.time_slot ASC"
        
        cursor.execute(query, tuple(params))
        appointments = cursor.fetchall()
        return appointments
    except Error as e:
        raise HospitalAppError(f"Database error fetching today's appointments: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_appointments_by_date_range(start_date, end_date):
    """
    Fetches all appointments scheduled within a date range [start_date, end_date].
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                a.appointment_id, a.appointment_date, a.time_slot, a.status,
                p.patient_name, p.phone AS patient_phone,
                d.doctor_name, dept.dept_name
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            JOIN departments dept ON d.dept_id = dept.dept_id
            WHERE a.appointment_date BETWEEN %s AND %s
            ORDER BY a.appointment_date DESC, a.time_slot ASC
        """
        cursor.execute(query, (start_date, end_date))
        appointments = cursor.fetchall()
        return appointments
    except Error as e:
        raise HospitalAppError(f"Database error fetching appointments by date range: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_doctor_wise_appointment_counts():
    """
    Generates a report of total appointments booked per doctor.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                d.doctor_id, d.doctor_name, dept.dept_name,
                COUNT(a.appointment_id) AS total_appointments,
                SUM(CASE WHEN a.status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_count,
                SUM(CASE WHEN a.status = 'BOOKED' THEN 1 ELSE 0 END) AS booked_count,
                SUM(CASE WHEN a.status = 'CANCELLED' THEN 1 ELSE 0 END) AS cancelled_count,
                SUM(CASE WHEN a.status = 'NO_SHOW' THEN 1 ELSE 0 END) AS noshow_count
            FROM doctors d
            JOIN departments dept ON d.dept_id = dept.dept_id
            LEFT JOIN appointments a ON d.doctor_id = a.doctor_id
            GROUP BY d.doctor_id, d.doctor_name, dept.dept_name
            ORDER BY total_appointments DESC
        """
        cursor.execute(query)
        report = cursor.fetchall()
        return report
    except Error as e:
        raise HospitalAppError(f"Database error fetching doctor-wise counts: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_revenue_summary():
    """
    Generates revenue summary including total billed, total paid, and total pending amounts.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                payment_status,
                COUNT(*) AS bill_count,
                COALESCE(SUM(amount), 0) AS total_amount
            FROM bills
            GROUP BY payment_status
        """
        cursor.execute(query)
        summary = cursor.fetchall()
        return summary
    except Error as e:
        raise HospitalAppError(f"Database error fetching revenue summary: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_cancelled_noshow_stats():
    """
    Generates statistics on cancelled and no-show appointments.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                status,
                COUNT(*) AS count
            FROM appointments
            WHERE status IN ('CANCELLED', 'NO_SHOW')
            GROUP BY status
        """
        cursor.execute(query)
        stats = cursor.fetchall()
        return stats
    except Error as e:
        raise HospitalAppError(f"Database error fetching cancellation stats: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
