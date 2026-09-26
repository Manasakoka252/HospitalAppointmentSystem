import mysql.connector
from mysql.connector import Error
from hospital.config import get_connection
from hospital.exceptions import BillingError, HospitalAppError
from hospital.appointment_module import get_appointment_by_id


def generate_bill(appointment_id, extra_charges=0.0):
    """
    Generates a consultation bill for an appointment.
    CRITICAL RULE: Only allow billing for appointments with status COMPLETED.
    Base amount = Doctor's consultation fee + optional extra_charges.
    Stores bill record in 'bills' table with payment_status = 'PENDING'.
    """
    try:
        extra_charges = float(extra_charges)
        if extra_charges < 0:
            raise BillingError("Extra charges cannot be negative.")
    except ValueError:
        raise BillingError("Extra charges must be a valid numeric amount.")
        
    # Get appointment details
    appt = get_appointment_by_id(appointment_id)
    
    # Check rule: Only COMPLETED appointments can be billed
    if appt['status'] != 'COMPLETED':
        raise BillingError(
            f"Cannot generate bill. Appointment status is '{appt['status']}'. "
            "Billing is ONLY allowed for COMPLETED appointments."
        )
        
    base_fee = float(appt['consultation_fee'])
    total_amount = base_fee + extra_charges
    
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if bill already exists
        cursor.execute("SELECT bill_id FROM bills WHERE appointment_id = %s", (appointment_id,))
        existing_bill = cursor.fetchone()
        
        if existing_bill:
            raise BillingError(f"Bill already generated for appointment ID {appointment_id}.")
            
        query = """
            INSERT INTO bills (appointment_id, amount, payment_status)
            VALUES (%s, %s, 'PENDING')
        """
        cursor.execute(query, (appointment_id, total_amount))
        conn.commit()
        bill_id = cursor.lastrowid
        return bill_id
    except mysql.connector.IntegrityError:
        if conn:
            conn.rollback()
        raise BillingError(f"Bill already exists for appointment ID {appointment_id}.")
    except Error as e:
        if conn:
            conn.rollback()
        raise HospitalAppError(f"Database error generating bill: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def mark_bill_paid(bill_id):
    """
    Updates bill payment status from 'PENDING' to 'PAID'.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if bill exists
        cursor.execute("SELECT bill_id, payment_status FROM bills WHERE bill_id = %s", (bill_id,))
        bill = cursor.fetchone()
        if not bill:
            raise BillingError(f"Bill ID {bill_id} not found.")
            
        query = "UPDATE bills SET payment_status = 'PAID' WHERE bill_id = %s"
        cursor.execute(query, (bill_id,))
        conn.commit()
        return True
    except Error as e:
        if conn:
            conn.rollback()
        raise HospitalAppError(f"Database error updating bill status: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_bill_by_appointment(appointment_id):
    """
    Retrieves bill information linked to a specific appointment ID.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                b.bill_id, b.appointment_id, b.amount, b.payment_status, b.billed_at,
                a.appointment_date, a.time_slot, a.status AS appointment_status,
                p.patient_name, p.phone AS patient_phone,
                d.doctor_name, d.consultation_fee, dept.dept_name
            FROM bills b
            JOIN appointments a ON b.appointment_id = a.appointment_id
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            JOIN departments dept ON d.dept_id = dept.dept_id
            WHERE b.appointment_id = %s
        """
        cursor.execute(query, (appointment_id,))
        bill = cursor.fetchone()
        return bill
    except Error as e:
        raise HospitalAppError(f"Database error fetching bill: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_all_bills(payment_status_filter=None):
    """
    Retrieves all bills with appointment, patient, and doctor details.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                b.bill_id, b.appointment_id, b.amount, b.payment_status, b.billed_at,
                a.appointment_date, a.time_slot,
                p.patient_id, p.patient_name, p.phone AS patient_phone,
                d.doctor_name, dept.dept_name
            FROM bills b
            JOIN appointments a ON b.appointment_id = a.appointment_id
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            JOIN departments dept ON d.dept_id = dept.dept_id
            WHERE 1=1
        """
        params = []
        if payment_status_filter:
            query += " AND b.payment_status = %s"
            params.append(payment_status_filter)
            
        query += " ORDER BY b.bill_id DESC"
        
        cursor.execute(query, tuple(params))
        bills = cursor.fetchall()
        return bills
    except Error as e:
        raise HospitalAppError(f"Database error fetching all bills: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_bills_by_patient(patient_id):
    """
    Retrieves all bills for a specific patient.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                b.bill_id, b.appointment_id, b.amount, b.payment_status, b.billed_at,
                a.appointment_date, a.time_slot,
                d.doctor_name, dept.dept_name
            FROM bills b
            JOIN appointments a ON b.appointment_id = a.appointment_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            JOIN departments dept ON d.dept_id = dept.dept_id
            WHERE a.patient_id = %s
            ORDER BY b.bill_id DESC
        """
        cursor.execute(query, (patient_id,))
        bills = cursor.fetchall()
        return bills
    except Error as e:
        raise HospitalAppError(f"Database error fetching patient bills: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
