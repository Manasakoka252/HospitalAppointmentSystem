import re
from datetime import datetime, date
from hospital.exceptions import ValidationError


def validate_name(name, field_name="Name"):
    """Validates that a name string is non-empty and has a reasonable length."""
    if not name or not str(name).strip():
        raise ValidationError(f"{field_name} cannot be empty.")
    if len(str(name).strip()) < 2:
        raise ValidationError(f"{field_name} must be at least 2 characters long.")
    return str(name).strip()


def validate_phone(phone):
    """Validates phone number format (10-15 digits)."""
    if not phone or not str(phone).strip():
        raise ValidationError("Phone number cannot be empty.")
    
    clean_phone = re.sub(r'[\s\-\(\)\+]', '', str(phone).strip())
    if not clean_phone.isdigit() or len(clean_phone) < 10 or len(clean_phone) > 15:
        raise ValidationError("Phone number must contain between 10 and 15 digits.")
    
    return str(phone).strip()


def validate_fee(fee):
    """Validates that consultation fee is a positive number."""
    try:
        fee_val = float(fee)
        if fee_val < 0:
            raise ValidationError("Consultation fee cannot be negative.")
        return fee_val
    except (ValueError, TypeError):
        raise ValidationError("Consultation fee must be a valid number.")


def validate_date(date_val, field_name="Date"):
    """Validates that a date value is valid and not in the past if required."""
    if date_val is None:
        raise ValidationError(f"{field_name} cannot be empty.")
    
    if isinstance(date_val, str):
        try:
            date_val = datetime.strptime(date_val, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError(f"{field_name} must be in YYYY-MM-DD format.")
            
    return date_val


def validate_patient_input(name, phone, dob=None, blood_group=None):
    """Validates patient registration details."""
    valid_name = validate_name(name, "Patient Name")
    valid_phone = validate_phone(phone)
    
    if dob:
        validate_date(dob, "Date of Birth")
        
    return valid_name, valid_phone


def validate_doctor_input(name, dept_id, phone, fee):
    """Validates doctor details."""
    valid_name = validate_name(name, "Doctor Name")
    if not dept_id or int(dept_id) <= 0:
        raise ValidationError("Please select a valid department.")
    valid_phone = validate_phone(phone)
    valid_fee = validate_fee(fee)
    
    return valid_name, int(dept_id), valid_phone, valid_fee


def validate_department_input(name):
    """Validates department details."""
    return validate_name(name, "Department Name")


def validate_appointment_input(patient_id, doctor_id, appt_date, slot):
    """Validates appointment booking inputs."""
    if not patient_id or int(patient_id) <= 0:
        raise ValidationError("Please select a valid patient.")
    if not doctor_id or int(doctor_id) <= 0:
        raise ValidationError("Please select a valid doctor.")
    
    valid_date = validate_date(appt_date, "Appointment Date")
    
    if not slot or not str(slot).strip():
        raise ValidationError("Time slot cannot be empty.")
        
    return int(patient_id), int(doctor_id), valid_date, str(slot).strip()