import mysql.connector
from mysql.connector import Error
from hospital.config import DB_CONFIG, get_server_connection, get_connection


def create_database():
    """Create hospital_db database if it does not exist."""
    conn = None
    cursor = None
    try:
        conn = get_server_connection()
        cursor = conn.cursor()
        db_name = DB_CONFIG["database"]
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        conn.commit()
        print(f"Database '{db_name}' checked/created successfully.")
    except Error as e:
        print(f"Error creating database: {e}")
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def create_tables():
    """Create all required tables for the Hospital Appointment System."""
    table_queries = [
        # 1. Departments table
        """
        CREATE TABLE IF NOT EXISTS departments (
            dept_id INT AUTO_INCREMENT PRIMARY KEY,
            dept_name VARCHAR(80) NOT NULL UNIQUE,
            description VARCHAR(255) DEFAULT NULL
        ) ENGINE=InnoDB;
        """,
        # 2. Doctors table
        """
        CREATE TABLE IF NOT EXISTS doctors (
            doctor_id INT AUTO_INCREMENT PRIMARY KEY,
            doctor_name VARCHAR(100) NOT NULL,
            dept_id INT NOT NULL,
            phone VARCHAR(15),
            consultation_fee DECIMAL(10,2) NOT NULL DEFAULT 500.00,
            available_slots VARCHAR(100) DEFAULT 'Morning,Evening',
            status ENUM('ACTIVE','INACTIVE') DEFAULT 'ACTIVE',
            FOREIGN KEY (dept_id) REFERENCES departments(dept_id) ON DELETE CASCADE
        ) ENGINE=InnoDB;
        """,
        # 3. Patients table
        """
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INT AUTO_INCREMENT PRIMARY KEY,
            patient_name VARCHAR(100) NOT NULL,
            gender ENUM('Male','Female','Other'),
            dob DATE,
            phone VARCHAR(15) NOT NULL,
            address VARCHAR(255),
            blood_group VARCHAR(5),
            status ENUM('ACTIVE','INACTIVE') DEFAULT 'ACTIVE',
            registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """,
        # 4. Appointments table (Includes UNIQUE constraint to prevent double booking)
        """
        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id INT NOT NULL,
            doctor_id INT NOT NULL,
            appointment_date DATE NOT NULL,
            time_slot VARCHAR(20) NOT NULL,
            status ENUM('BOOKED','COMPLETED','CANCELLED','NO_SHOW') DEFAULT 'BOOKED',
            notes VARCHAR(255),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
            FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE,
            UNIQUE KEY uq_doctor_slot (doctor_id, appointment_date, time_slot)
        ) ENGINE=InnoDB;
        """,
        # 5. Bills table
        """
        CREATE TABLE IF NOT EXISTS bills (
            bill_id INT AUTO_INCREMENT PRIMARY KEY,
            appointment_id INT NOT NULL UNIQUE,
            amount DECIMAL(10,2) NOT NULL,
            payment_status ENUM('PENDING','PAID') DEFAULT 'PENDING',
            billed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id) ON DELETE CASCADE
        ) ENGINE=InnoDB;
        """
    ]

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        for query in table_queries:
            cursor.execute(query)
        conn.commit()
        print("All tables created successfully.")
    except Error as e:
        if conn:
            conn.rollback()
        print(f"Error creating tables: {e}")
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def seed_sample_data():
    """Insert initial sample departments, doctors, and patients if empty."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check if departments exist
        cursor.execute("SELECT COUNT(*) FROM departments")
        dept_count = cursor.fetchone()[0]

        if dept_count == 0:
            sample_depts = [
                ("Cardiology", "Heart and cardiovascular system care"),
                ("Neurology", "Brain, spinal cord and nerve care"),
                ("Orthopedics", "Bone, joint, and muscular system care"),
                ("General Medicine", "Primary healthcare and general medical conditions"),
                ("Pediatrics", "Infant, child, and adolescent healthcare")
            ]
            cursor.executemany(
                "INSERT INTO departments (dept_name, description) VALUES (%s, %s)",
                sample_depts
            )
            conn.commit()
            print("Seeded sample departments.")

            # Seed Doctors
            sample_doctors = [
                ("Dr. Rajesh Sharma", 1, "9876543210", 800.00, "Morning,Evening", "ACTIVE"),
                ("Dr. Priya Nair", 2, "9876543211", 1000.00, "Morning", "ACTIVE"),
                ("Dr. Amit Verma", 3, "9876543212", 750.00, "Evening", "ACTIVE"),
                ("Dr. Sunita Rao", 4, "9876543213", 500.00, "Morning,Evening", "ACTIVE"),
                ("Dr. Vikram Patel", 5, "9876543214", 600.00, "Morning", "ACTIVE")
            ]
            cursor.executemany(
                """INSERT INTO doctors 
                   (doctor_name, dept_id, phone, consultation_fee, available_slots, status) 
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                sample_doctors
            )
            conn.commit()
            print("Seeded sample doctors.")

            # Seed Patients
            sample_patients = [
                ("Ramesh Kumar", "Male", "1985-05-15", "9123456789", "123 Main St, City", "O+", "ACTIVE"),
                ("Anita Singh", "Female", "1992-08-22", "9123456790", "456 Park Ave, City", "A+", "ACTIVE"),
                ("Suresh Reddy", "Male", "1978-11-03", "9123456791", "789 Lake Rd, City", "B+", "ACTIVE")
            ]
            cursor.executemany(
                """INSERT INTO patients 
                   (patient_name, gender, dob, phone, address, blood_group, status) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                sample_patients
            )
            conn.commit()
            print("Seeded sample patients.")

    except Error as e:
        if conn:
            conn.rollback()
        print(f"Error seeding sample data: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def init_db():
    """Initialize full database schema and seed sample data."""
    create_database()
    create_tables()
    seed_sample_data()


if __name__ == "__main__":
    init_db()
