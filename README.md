# 🏥 Hospital Appointment System (Python + MySQL + Streamlit)

A complete, beginner-friendly **Hospital Appointment Management System** built with Python, MySQL, `mysql-connector-python`, and Streamlit. This application allows multi-specialty hospitals to manage patient profiles, doctor records, department specialties, appointment scheduling with double-booking prevention, consultation billing, and management reports.

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


