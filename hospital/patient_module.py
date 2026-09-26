import mysql.connector
from mysql.connector import Error
from hospital.config import get_connection
from hospital.exceptions import PatientNotFoundError, HospitalAppError
from hospital.validators import validate_patient_input


def add_patient(name, gender, dob, phone, address, blood_group):
    """
    Registers a new patient in the database.
    Returns the generated patient_id.
    """
    validate_patient_input(name, phone, dob, blood_group)
    
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO patients (patient_name, gender, dob, phone, address, blood_group, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'ACTIVE')
        """
        cursor.execute(query, (name, gender, dob, phone, address, blood_group))
        conn.commit()
        patient_id = cursor.lastrowid
        return patient_id
    except Error as e:
        if conn:
            conn.rollback()
        raise HospitalAppError(f"Database error while adding patient: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_all_patients(status_filter=None):
    """
    Retrieves all patients from the database.
    Optionally filter by status ('ACTIVE' or 'INACTIVE').
    Returns a list of dictionaries.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        if status_filter:
            query = "SELECT * FROM patients WHERE status = %s ORDER BY patient_id DESC"
            cursor.execute(query, (status_filter,))
        else:
            query = "SELECT * FROM patients ORDER BY patient_id DESC"
            cursor.execute(query)
            
        patients = cursor.fetchall()
        return patients
    except Error as e:
        raise HospitalAppError(f"Database error fetching patients: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_patient_by_id(patient_id):
    """
    Retrieves a single patient by ID.
    Raises PatientNotFoundError if patient does not exist.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM patients WHERE patient_id = %s"
        cursor.execute(query, (patient_id,))
        patient = cursor.fetchone()
        
        if not patient:
            raise PatientNotFoundError(f"Patient with ID {patient_id} not found.")
            
        return patient
    except Error as e:
        if isinstance(e, PatientNotFoundError):
            raise e
        raise HospitalAppError(f"Database error fetching patient ID {patient_id}: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def search_patients(search_term):
    """
    Searches patients by ID, name, or phone number.
    Returns a list of matching patient dictionaries.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        term = f"%{search_term.strip()}%"
        query = """
            SELECT * FROM patients 
            WHERE patient_id LIKE %s 
               OR patient_name LIKE %s 
               OR phone LIKE %s
            ORDER BY patient_id DESC
        """
        cursor.execute(query, (term, term, term))
        patients = cursor.fetchall()
        return patients
    except Error as e:
        raise HospitalAppError(f"Database error searching patients: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def update_patient(patient_id, name, gender, dob, phone, address, blood_group):
    """
    Updates details of an existing patient.
    """
    validate_patient_input(name, phone, dob, blood_group)
    
    # Check if patient exists
    get_patient_by_id(patient_id)
    
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            UPDATE patients 
            SET patient_name = %s, gender = %s, dob = %s, phone = %s, address = %s, blood_group = %s
            WHERE patient_id = %s
        """
        cursor.execute(query, (name, gender, dob, phone, address, blood_group, patient_id))
        conn.commit()
        return True
    except Error as e:
        if conn:
            conn.rollback()
        raise HospitalAppError(f"Database error updating patient: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def set_patient_status(patient_id, new_status):
    """
    Changes patient status to 'ACTIVE' or 'INACTIVE' (Soft delete).
    """
    if new_status not in ['ACTIVE', 'INACTIVE']:
        raise HospitalAppError("Status must be either 'ACTIVE' or 'INACTIVE'.")
        
    get_patient_by_id(patient_id)
    
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "UPDATE patients SET status = %s WHERE patient_id = %s"
        cursor.execute(query, (new_status, patient_id))
        conn.commit()
        return True
    except Error as e:
        if conn:
            conn.rollback()
        raise HospitalAppError(f"Database error updating patient status: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_patient_appointment_history(patient_id):
    """
    Retrieves appointment history for a given patient along with doctor & bill info.
    """
    get_patient_by_id(patient_id)
    
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
                a.status AS appointment_status,
                a.notes,
                d.doctor_name,
                dept.dept_name,
                b.amount AS bill_amount,
                b.payment_status
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.doctor_id
            JOIN departments dept ON d.dept_id = dept.dept_id
            LEFT JOIN bills b ON a.appointment_id = b.appointment_id
            WHERE a.patient_id = %s
            ORDER BY a.appointment_date DESC, a.time_slot DESC
        """
        cursor.execute(query, (patient_id,))
        history = cursor.fetchall()
        return history
    except Error as e:
        raise HospitalAppError(f"Database error fetching patient appointment history: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()