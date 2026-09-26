import mysql.connector
from mysql.connector import Error
from hospital.config import get_connection
from hospital.exceptions import DoctorNotFoundError, HospitalAppError
from hospital.validators import validate_doctor_input


def add_doctor(name, dept_id, phone, consultation_fee, available_slots="Morning,Evening"):
    """
    Adds a new doctor linked to a department.
    Returns the new doctor_id.
    """
    validate_doctor_input(name, dept_id, phone, consultation_fee)
    
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO doctors (doctor_name, dept_id, phone, consultation_fee, available_slots, status)
            VALUES (%s, %s, %s, %s, %s, 'ACTIVE')
        """
        cursor.execute(query, (name, dept_id, phone, consultation_fee, available_slots))
        conn.commit()
        doctor_id = cursor.lastrowid
        return doctor_id
    except Error as e:
        if conn:
            conn.rollback()
        raise HospitalAppError(f"Database error while adding doctor: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_all_doctors(dept_id=None, status_filter=None):
    """
    Retrieves doctors with department details.
    Optionally filter by department ID or status.
    Returns a list of dictionaries.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT d.*, dept.dept_name 
            FROM doctors d
            JOIN departments dept ON d.dept_id = dept.dept_id
            WHERE 1=1
        """
        params = []
        
        if dept_id:
            query += " AND d.dept_id = %s"
            params.append(dept_id)
            
        if status_filter:
            query += " AND d.status = %s"
            params.append(status_filter)
            
        query += " ORDER BY d.doctor_id DESC"
        
        cursor.execute(query, tuple(params))
        doctors = cursor.fetchall()
        return doctors
    except Error as e:
        raise HospitalAppError(f"Database error fetching doctors: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_doctor_by_id(doctor_id):
    """
    Retrieves a single doctor by ID.
    Raises DoctorNotFoundError if not found.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT d.*, dept.dept_name 
            FROM doctors d
            JOIN departments dept ON d.dept_id = dept.dept_id
            WHERE d.doctor_id = %s
        """
        cursor.execute(query, (doctor_id,))
        doctor = cursor.fetchone()
        
        if not doctor:
            raise DoctorNotFoundError(f"Doctor with ID {doctor_id} not found.")
            
        return doctor
    except Error as e:
        if isinstance(e, DoctorNotFoundError):
            raise e
        raise HospitalAppError(f"Database error fetching doctor ID {doctor_id}: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def update_doctor(doctor_id, name, dept_id, phone, consultation_fee, available_slots):
    """
    Updates doctor profile, consultation fee, phone, timings, or department.
    """
    validate_doctor_input(name, dept_id, phone, consultation_fee)
    get_doctor_by_id(doctor_id)
    
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            UPDATE doctors 
            SET doctor_name = %s, dept_id = %s, phone = %s, consultation_fee = %s, available_slots = %s
            WHERE doctor_id = %s
        """
        cursor.execute(query, (name, dept_id, phone, consultation_fee, available_slots, doctor_id))
        conn.commit()
        return True
    except Error as e:
        if conn:
            conn.rollback()
        raise HospitalAppError(f"Database error updating doctor: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def set_doctor_status(doctor_id, new_status):
    """
    Changes doctor status to 'ACTIVE' or 'INACTIVE'.
    """
    if new_status not in ['ACTIVE', 'INACTIVE']:
        raise HospitalAppError("Status must be either 'ACTIVE' or 'INACTIVE'.")
        
    get_doctor_by_id(doctor_id)
    
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "UPDATE doctors SET status = %s WHERE doctor_id = %s"
        cursor.execute(query, (new_status, doctor_id))
        conn.commit()
        return True
    except Error as e:
        if conn:
            conn.rollback()
        raise HospitalAppError(f"Database error updating doctor status: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_doctor_schedule(doctor_id, schedule_date):
    """
    Fetches doctor's appointment schedule for a specific date.
    """
    get_doctor_by_id(doctor_id)
    
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                a.appointment_id,
                a.appointment_date,
                a.time_slot,
                a.status,
                a.notes,
                p.patient_name,
                p.phone AS patient_phone
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            WHERE a.doctor_id = %s AND a.appointment_date = %s
            ORDER BY a.time_slot ASC
        """
        cursor.execute(query, (doctor_id, schedule_date))
        schedule = cursor.fetchall()
        return schedule
    except Error as e:
        raise HospitalAppError(f"Database error fetching doctor schedule: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
