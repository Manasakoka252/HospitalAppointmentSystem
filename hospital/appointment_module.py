import mysql.connector
from mysql.connector import Error
from hospital.config import get_connection
from hospital.exceptions import (
    AppointmentNotFoundError, 
    AppointmentSlotUnavailableError, 
    HospitalAppError
)
from hospital.validators import validate_appointment_input


def check_slot_availability(doctor_id, appointment_date, time_slot, exclude_appointment_id=None):
    """
    Checks if a doctor is available at the given date and time slot.
    Returns True if available, False otherwise.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT COUNT(*) FROM appointments
            WHERE doctor_id = %s 
              AND appointment_date = %s 
              AND time_slot = %s 
              AND status IN ('BOOKED', 'COMPLETED')
        """
        params = [doctor_id, appointment_date, time_slot]
        
        if exclude_appointment_id:
            query += " AND appointment_id != %s"
            params.append(exclude_appointment_id)
            
        cursor.execute(query, tuple(params))
        count = cursor.fetchone()[0]
        return count == 0
    except Error as e:
        raise HospitalAppError(f"Database error checking availability: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def book_appointment(patient_id, doctor_id, appointment_date, time_slot, notes=""):
    """
    Books a new appointment.
    Prevents double booking using:
      1. Application level availability check
      2. Database UNIQUE constraint (uq_doctor_slot)
    Uses SQL transaction (commit / rollback).
    Returns generated appointment_id.
    """
    validate_appointment_input(patient_id, doctor_id, appointment_date, time_slot)
    
    # 1. Application-level check
    if not check_slot_availability(doctor_id, appointment_date, time_slot):
        raise AppointmentSlotUnavailableError(
            f"Doctor is already booked for slot '{time_slot}' on {appointment_date}."
        )
        
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            INSERT INTO appointments (patient_id, doctor_id, appointment_date, time_slot, status, notes)
            VALUES (%s, %s, %s, %s, 'BOOKED', %s)
        """
        cursor.execute(query, (patient_id, doctor_id, appointment_date, time_slot, notes))
        
        # Explicit commit for transaction
        conn.commit()
        appointment_id = cursor.lastrowid
        return appointment_id
    except mysql.connector.IntegrityError as ie:
        # Handles 2. Database-level UNIQUE constraint violation
        if conn:
            conn.rollback()
        raise AppointmentSlotUnavailableError(
            f"Double Booking Error: The doctor is already booked for date {appointment_date} at {time_slot}."
        )
    except Error as e:
        if conn:
            conn.rollback()
        raise HospitalAppError(f"Database error booking appointment: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_all_appointments(date_filter=None, doctor_id=None, patient_id=None, status_filter=None):
    """
    Retrieves appointments with detailed patient and doctor information.
    Supports filtering by date, doctor, patient, or status.
    """
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
                a.created_at,
                p.patient_id,
                p.patient_name,
                p.phone AS patient_phone,
                d.doctor_id,
                d.doctor_name,
                d.consultation_fee,
                dept.dept_name,
                b.bill_id,
                b.payment_status,
                b.amount AS bill_amount
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            JOIN departments dept ON d.dept_id = dept.dept_id
            LEFT JOIN bills b ON a.appointment_id = b.appointment_id
            WHERE 1=1
        """
        params = []
        
        if date_filter:
            query += " AND a.appointment_date = %s"
            params.append(date_filter)
            
        if doctor_id:
            query += " AND a.doctor_id = %s"
            params.append(doctor_id)
            
        if patient_id:
            query += " AND a.patient_id = %s"
            params.append(patient_id)
            
        if status_filter:
            query += " AND a.status = %s"
            params.append(status_filter)
            
        query += " ORDER BY a.appointment_date DESC, a.time_slot ASC"
        
        cursor.execute(query, tuple(params))
        appointments = cursor.fetchall()
        return appointments
    except Error as e:
        raise HospitalAppError(f"Database error fetching appointments: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_appointment_by_id(appointment_id):
    """
    Retrieves a single appointment by ID.
    Raises AppointmentNotFoundError if not found.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                a.*,
                p.patient_name, p.phone AS patient_phone,
                d.doctor_name, d.consultation_fee, dept.dept_name
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            JOIN departments dept ON d.dept_id = dept.dept_id
            WHERE a.appointment_id = %s
        """
        cursor.execute(query, (appointment_id,))
        appt = cursor.fetchone()
        
        if not appt:
            raise AppointmentNotFoundError(f"Appointment ID {appointment_id} not found.")
            
        return appt
    except Error as e:
        if isinstance(e, AppointmentNotFoundError):
            raise e
        raise HospitalAppError(f"Database error fetching appointment ID {appointment_id}: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def cancel_appointment(appointment_id):
    """
    Cancels an appointment by changing status to 'CANCELLED'.
    """
    appt = get_appointment_by_id(appointment_id)
    if appt['status'] == 'COMPLETED':
        raise HospitalAppError("Cannot cancel an appointment that is already COMPLETED.")
        
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "UPDATE appointments SET status = 'CANCELLED' WHERE appointment_id = %s"
        cursor.execute(query, (appointment_id,))
        conn.commit()
        return True
    except Error as e:
        if conn:
            conn.rollback()
        raise HospitalAppError(f"Database error cancelling appointment: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def reschedule_appointment(appointment_id, new_date, new_slot):
    """
    Reschedules an existing appointment to a new date and slot.
    Checks availability first to prevent double booking.
    """
    appt = get_appointment_by_id(appointment_id)
    if appt['status'] in ['COMPLETED', 'CANCELLED']:
        raise HospitalAppError(f"Cannot reschedule an appointment with status '{appt['status']}'.")
        
    doctor_id = appt['doctor_id']
    
    # Check availability excluding current appointment
    if not check_slot_availability(doctor_id, new_date, new_slot, exclude_appointment_id=appointment_id):
        raise AppointmentSlotUnavailableError(
            f"Slot '{new_slot}' on {new_date} is already booked for this doctor."
        )
        
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            UPDATE appointments 
            SET appointment_date = %s, time_slot = %s, status = 'BOOKED' 
            WHERE appointment_id = %s
        """
        cursor.execute(query, (new_date, new_slot, appointment_id))
        conn.commit()
        return True
    except mysql.connector.IntegrityError:
        if conn:
            conn.rollback()
        raise AppointmentSlotUnavailableError("Double booking detected. The selected slot is unavailable.")
    except Error as e:
        if conn:
            conn.rollback()
        raise HospitalAppError(f"Database error rescheduling appointment: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def update_appointment_status(appointment_id, new_status):
    """
    Updates appointment status to 'COMPLETED', 'NO_SHOW', 'BOOKED', or 'CANCELLED'.
    """
    valid_statuses = ['BOOKED', 'COMPLETED', 'CANCELLED', 'NO_SHOW']
    if new_status not in valid_statuses:
        raise HospitalAppError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
    get_appointment_by_id(appointment_id)
    
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "UPDATE appointments SET status = %s WHERE appointment_id = %s"
        cursor.execute(query, (new_status, appointment_id))
        conn.commit()
        return True
    except Error as e:
        if conn:
            conn.rollback()
        raise HospitalAppError(f"Database error updating appointment status: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
