# 🏥 Hospital Appointment System (Python + MySQL + Streamlit)

A complete, beginner-friendly **Hospital Appointment Management System** built with Python, MySQL, `mysql-connector-python`, and Streamlit. This application allows multi-specialty hospitals to manage patient profiles, doctor records, department specialties, appointment scheduling with double-booking prevention, consultation billing, and management reports.

---

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Objective](#objective)
3. [Technologies Used](#technologies-used)
4. [Project Folder Structure](#project-folder-structure)
5. [Database Architecture & Design](#database-architecture--design)
6. [Key Features & Modules](#key-features--modules)
7. [Installation & Setup Guide](#installation--setup-guide)
8. [Database Configuration](#database-configuration)
9. [How to Run the Application](#how-to-run-the-application)
10. [Application Workflow](#application-workflow)
11. [Final Explanation & Viva / Interview Guide](#final-explanation--viva--interview-guide)

---

## 🌟 Project Overview
The **Hospital Appointment System** simplifies hospital workflows by digitizing patient registrations, doctor allocations, slot scheduling, billing, and reports generation. Built with a modular Python backend and an intuitive Streamlit GUI, it replaces complex terminal interfaces with a clean interactive web dashboard.

---

## 🎯 Objective
- Understand modular Python project design and package structuring.
- Perform relational database CRUD operations using MySQL and standard SQL queries.
- Prevent slot conflicts (double-booking) through database integrity constraints and application-level checks.
- Enforce business logic rules (e.g., billing allowed only for completed consultations).
- Build a web GUI using Streamlit.

---

## 🛠️ Technologies Used
- **Language**: Python 3.8+
- **Database**: MySQL 5.7+ / MySQL 8.x
- **Database Driver**: `mysql-connector-python`
- **Frontend GUI**: Streamlit (`streamlit`)
- **Data Handling**: Pandas (`pandas`)

---

## 📁 Project Folder Structure
```
HospitalAppointmentSystem/
│
├── main.py                    # Streamlit entry point application
├── requirements.txt           # Python dependencies
├── README.md                  # Complete documentation & interview guide
│
└── hospital/                  # Main Python package
    ├── __init__.py            # Package initialization marker
    ├── config.py              # MySQL database connection settings & helper functions
    ├── db_setup.py            # Automated database & tables creation script
    ├── exceptions.py          # Custom exception classes
    ├── validators.py          # Input validation functions
    ├── patient_module.py      # Patient CRUD operations & history
    ├── doctor_module.py       # Doctor CRUD operations & schedule tracking
    ├── department_module.py   # Department CRUD operations & doctor lookup
    ├── appointment_module.py  # Core scheduling logic & double-booking prevention
    ├── billing_module.py      # Consultation bill generation & payment tracking
    └── reports_module.py      # Data analytics & management summary reports
```

---

## 🗄️ Database Architecture & Design

Database Name: `hospital_db`

### Tables & Relationships
1. **`departments`**: Stores hospital specialties (e.g., Cardiology, Neurology, Orthopedics).
   - `dept_id` (INT, Primary Key, Auto Increment)
   - `dept_name` (VARCHAR(80), Unique, Not Null)
   - `description` (VARCHAR(255))

2. **`doctors`**: Stores doctor profiles linked to a department.
   - `doctor_id` (INT, Primary Key, Auto Increment)
   - `doctor_name` (VARCHAR(100), Not Null)
   - `dept_id` (INT, Foreign Key -> `departments.dept_id`)
   - `phone` (VARCHAR(15))
   - `consultation_fee` (DECIMAL(10,2), Default 500.00)
   - `available_slots` (VARCHAR(100), Default 'Morning,Evening')
   - `status` (ENUM('ACTIVE', 'INACTIVE'))

3. **`patients`**: Stores patient registration data with soft delete support.
   - `patient_id` (INT, Primary Key, Auto Increment)
   - `patient_name` (VARCHAR(100), Not Null)
   - `gender` (ENUM('Male', 'Female', 'Other'))
   - `dob` (DATE)
   - `phone` (VARCHAR(15), Not Null)
   - `address` (VARCHAR(255))
   - `blood_group` (VARCHAR(5))
   - `status` (ENUM('ACTIVE', 'INACTIVE'))
   - `registered_at` (DATETIME)

4. **`appointments`**: Stores scheduled appointments with status lifecycle.
   - `appointment_id` (INT, Primary Key, Auto Increment)
   - `patient_id` (INT, Foreign Key -> `patients.patient_id`)
   - `doctor_id` (INT, Foreign Key -> `doctors.doctor_id`)
   - `appointment_date` (DATE, Not Null)
   - `time_slot` (VARCHAR(20), Not Null)
   - `status` (ENUM('BOOKED', 'COMPLETED', 'CANCELLED', 'NO_SHOW'))
   - `notes` (VARCHAR(255))
   - `created_at` (DATETIME)
   - **`UNIQUE KEY uq_doctor_slot (doctor_id, appointment_date, time_slot)`** -> *Prevents double booking at DB level*.

5. **`bills`**: Stores billing records linked to completed consultations.
   - `bill_id` (INT, Primary Key, Auto Increment)
   - `appointment_id` (INT, Foreign Key -> `appointments.appointment_id`, Unique)
   - `amount` (DECIMAL(10,2), Not Null)
   - `payment_status` (ENUM('PENDING', 'PAID'))
   - `billed_at` (DATETIME)

---

## ⚡ Key Features & Modules

### 1. Dashboard
- Displays real-time metrics: Total Active Patients, Active Doctors, Total Departments, Today's Appointments, Pending Bills, Total Revenue.
- Table of today's scheduled consultations.

### 2. Patient Module
- Register new patients with full profile details.
- View and search directory by Patient ID, Name, or Phone.
- Update profile details.
- Soft-delete (Deactivate/Activate) patients to maintain historical integrity.
- View detailed appointment history for any patient.

### 3. Doctor Module
- Add doctors and assign to departments.
- View doctor list with department filtering.
- Update consultation fee, contact details, and shift timings.
- View doctor appointment schedule for any chosen date.

### 4. Department Module
- Create and update hospital departments/specialties dynamically.
- View list of doctors under each department.

### 5. Appointment Module (Core)
- **Booking Flow**: Patient Selection -> Department Selection -> Doctor Selection -> Date -> Time Slot.
- **Double Booking Prevention**: Checked via both application logic and database `UNIQUE KEY (doctor_id, appointment_date, time_slot)`.
- Reschedule or cancel existing bookings.
- Mark consultation status as `COMPLETED` or `NO_SHOW`.

### 6. Billing Module
- Generate consultation bill using the doctor's fee as base amount + optional extra charges (lab/medicines).
- **Enforced Business Rule**: Billing is allowed ONLY for appointments marked as `COMPLETED`.
- Track payment status (`PENDING` / `PAID`) and process payments.

### 7. Reports Module
- Today's Appointments report.
- Appointments within a custom date range.
- Doctor-wise booking summary.
- Financial revenue summary (Paid vs Pending).
- Cancelled & No-Show statistics.

---

## 🚀 Installation & Setup Guide

### Prerequisites
- Python 3.8 or higher installed.
- MySQL Server installed and running.

### 1. Clone / Navigate to Project Directory
```bash
cd HospitalAppointmentSystem
```

### 2. Install Required Packages
```bash
pip install -r requirements.txt
```

---

## ⚙️ Database Configuration

Open `hospital/config.py` and update your MySQL connection details:

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",
    "database": "hospital_db",
    "port": 3306
}
```
*Note: The application automatically creates `hospital_db`, sets up all required tables, and seeds sample data on first launch!*

---

## ▶️ How to Run the Application

Run the application using Streamlit:

```bash
streamlit run main.py
```

The Streamlit GUI will open automatically in your web browser at `http://localhost:8501`.

---

## 🎓 Final Explanation & Viva / Interview Guide

### 1. Purpose of Every File in the Project
- `main.py`: Streamlit entry point. Handles GUI layout, sidebar menu navigation, input forms, and calls module functions.
- `hospital/config.py`: Centralized database configuration dictionary (`DB_CONFIG`) and `get_connection()` function.
- `hospital/db_setup.py`: Automates `CREATE DATABASE` and `CREATE TABLE` queries, adding foreign keys and unique constraints. Seeds sample data.
- `hospital/exceptions.py`: Custom Python exception classes for readable error management.
- `hospital/validators.py`: Input validation functions (e.g. phone digit count, non-negative fees, required text).
- `hospital/patient_module.py`: Database helper functions for patient CRUD operations, soft delete, and patient history.
- `hospital/doctor_module.py`: Database helper functions for doctor records and schedule views.
- `hospital/department_module.py`: Database helper functions for managing departments.
- `hospital/appointment_module.py`: Core logic for booking, rescheduling, cancelling, slot availability checks, and status updates.
- `hospital/billing_module.py`: Logic for generating bills for completed consultations and tracking payment status.
- `hospital/reports_module.py`: SQL aggregation queries for dashboard metrics and reporting.

### 2. How Streamlit Connects to Python & MySQL
1. The user interacts with Streamlit UI components (e.g., forms, buttons, inputs) in `main.py`.
2. When a button is clicked, `main.py` calls backend functions in the `hospital/` package modules.
3. Backend functions invoke `get_connection()` from `hospital/config.py` to create a `mysql.connector` connection.
4. SQL queries execute, transactions are committed (`conn.commit()`), cursors & connections are closed safely in `finally` blocks, and data is returned to Streamlit to display.

### 3. How Double Booking is Prevented
Double booking is prevented at two independent layers:
1. **Application Layer**: Before running `INSERT`, `check_slot_availability()` executes a `SELECT COUNT(*)` query to check if the doctor already has a booking for that date and time slot.
2. **Database Layer**: The `appointments` table includes a `UNIQUE KEY uq_doctor_slot (doctor_id, appointment_date, time_slot)`. If a duplicate insert occurs, MySQL rejects the transaction and raises a `mysql.connector.IntegrityError`, which Python catches to display a user-friendly error message.

### 4. Hard Delete vs Soft Delete
- **Hard Delete**: `DELETE FROM patients WHERE patient_id = 1` permanently removes the record from the database. This breaks historical foreign key records in appointments and bills.
- **Soft Delete**: `UPDATE patients SET status = 'INACTIVE' WHERE patient_id = 1` flags the patient as inactive while preserving medical and billing history.

### 5. Why `commit()` and `rollback()` are Used
- `commit()`: Saves database changes permanently after successful operations.
- `rollback()`: Undoes all changes in the current transaction if an error or exception occurs mid-operation, ensuring database consistency.

### 6. Frequently Asked Viva / Interview Q&A

**Q1: What is a Foreign Key and why is it used here?**  
*A: A Foreign Key is a field in one table (e.g. `doctor_id` in `appointments`) that links to the Primary Key of another table (`doctors`). It enforces referential integrity so appointments cannot reference non-existent doctors or patients.*

**Q2: What is an ENUM column?**  
*A: ENUM is a string object with a value chosen from a permitted list of values specified at table creation (e.g., status in appointments: `'BOOKED'`, `'COMPLETED'`, `'CANCELLED'`, `'NO_SHOW'`).*

**Q3: Why is billing restricted to COMPLETED appointments?**  
*A: In real-world hospital workflows, a patient cannot be charged for a doctor consultation that hasn't taken place yet or was cancelled/no-show.*

**Q4: Where are `try...except...finally` blocks used and why?**  
*A: They are used around database queries. `try` executes SQL, `except` catches errors and triggers `rollback()`, and `finally` ensures cursors and connections are closed to prevent connection leaks.*
