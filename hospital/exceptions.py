"""
Custom Exception Classes for Hospital Appointment System.
Provides readable and specific exceptions for error handling.
"""


class HospitalAppError(Exception):
    """Base exception for all hospital application errors."""
    pass


class PatientNotFoundError(HospitalAppError):
    """Raised when a patient record is not found."""
    pass


class DoctorNotFoundError(HospitalAppError):
    """Raised when a doctor record is not found."""
    pass


class DepartmentNotFoundError(HospitalAppError):
    """Raised when a department record is not found."""
    pass


class AppointmentNotFoundError(HospitalAppError):
    """Raised when an appointment record is not found."""
    pass


class AppointmentSlotUnavailableError(HospitalAppError):
    """Raised when an appointment slot is already booked or unavailable."""
    pass


class BillingError(HospitalAppError):
    """Raised when a billing rule is violated (e.g., billing a non-completed appointment)."""
    pass


class ValidationError(HospitalAppError):
    """Raised when input validation fails."""
    pass