import mysql.connector
from mysql.connector import Error
from hospital.config import get_connection
from hospital.exceptions import DepartmentNotFoundError, HospitalAppError
from hospital.validators import validate_department_input


def add_department(dept_name, description=None):
    """
    Adds a new department.
    Returns the new dept_id.
    """
    validate_department_input(dept_name)
    
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "INSERT INTO departments (dept_name, description) VALUES (%s, %s)"
        cursor.execute(query, (dept_name, description))
        conn.commit()
        return cursor.lastrowid
    except mysql.connector.IntegrityError:
        if conn:
            conn.rollback()
        raise HospitalAppError(f"Department '{dept_name}' already exists.")
    except Error as e:
        if conn:
            conn.rollback()
        raise HospitalAppError(f"Database error adding department: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_all_departments():
    """
    Retrieves all departments along with the count of doctors in each department.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT d.*, COUNT(doc.doctor_id) AS doctor_count
            FROM departments d
            LEFT JOIN doctors doc ON d.dept_id = doc.dept_id
            GROUP BY d.dept_id, d.dept_name, d.description
            ORDER BY d.dept_id ASC
        """
        cursor.execute(query)
        departments = cursor.fetchall()
        return departments
    except Error as e:
        raise HospitalAppError(f"Database error fetching departments: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_department_by_id(dept_id):
    """
    Retrieves department by ID.
    Raises DepartmentNotFoundError if not found.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM departments WHERE dept_id = %s"
        cursor.execute(query, (dept_id,))
        dept = cursor.fetchone()
        
        if not dept:
            raise DepartmentNotFoundError(f"Department ID {dept_id} not found.")
            
        return dept
    except Error as e:
        if isinstance(e, DepartmentNotFoundError):
            raise e
        raise HospitalAppError(f"Database error fetching department ID {dept_id}: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def update_department(dept_id, dept_name, description=None):
    """
    Updates department name and description.
    """
    validate_department_input(dept_name)
    get_department_by_id(dept_id)
    
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "UPDATE departments SET dept_name = %s, description = %s WHERE dept_id = %s"
        cursor.execute(query, (dept_name, description, dept_id))
        conn.commit()
        return True
    except mysql.connector.IntegrityError:
        if conn:
            conn.rollback()
        raise HospitalAppError(f"Department name '{dept_name}' is already taken by another department.")
    except Error as e:
        if conn:
            conn.rollback()
        raise HospitalAppError(f"Database error updating department: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_doctors_by_department(dept_id):
    """
    Lists doctors belonging to a specific department.
    """
    get_department_by_id(dept_id)
    
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM doctors WHERE dept_id = %s ORDER BY doctor_name ASC"
        cursor.execute(query, (dept_id,))
        doctors = cursor.fetchall()
        return doctors
    except Error as e:
        raise HospitalAppError(f"Database error fetching doctors for department {dept_id}: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
