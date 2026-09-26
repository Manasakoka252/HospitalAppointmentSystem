import datetime
import pandas as pd
import streamlit as st

from hospital.db_setup import init_db
from hospital import (
    patient_module,
    doctor_module,
    department_module,
    appointment_module,
    billing_module,
    reports_module
)
from hospital.exceptions import (
    HospitalAppError,
    PatientNotFoundError,
    DoctorNotFoundError,
    DepartmentNotFoundError,
    AppointmentNotFoundError,
    AppointmentSlotUnavailableError,
    BillingError,
    ValidationError
)

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="Hospital Appointment System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database Schema on Application Startup
@st.cache_resource
def setup_database():
    try:
        init_db()
        return True
    except Exception as e:
        st.error(f"Failed to initialize database: {e}")
        return False

db_ready = setup_database()


# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
st.sidebar.image("https://img.icons8.com/color/96/hospital-2.png", width=70)
st.sidebar.title("Hospital System")
st.sidebar.markdown("---")

# Main Navigation (Must use st.sidebar.radio as per requirements)
menu_choice = st.sidebar.radio(
    "Navigation Menu",
    [
        "Dashboard",
        "Patients",
        "Doctors",
        "Departments",
        "Appointments",
        "Billing",
        "Reports"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("🏥 Multi-Specialty Hospital Management System")


# ==========================================
# 1. DASHBOARD MODULE
# ==========================================
if menu_choice == "Dashboard":
    st.title("🏥 Hospital Overview Dashboard")
    st.markdown("Welcome to the Hospital Appointment Management System.")
    
    if not db_ready:
        st.error("Database connection issue. Please check your MySQL server configuration in `hospital/config.py`.")
        st.stop()
        
    try:
        stats = reports_module.get_dashboard_stats()
        
        # Top Metric Cards
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Active Patients", stats["total_patients"], delta=None)
        with col2:
            st.metric("Active Doctors", stats["active_doctors"])
        with col3:
            st.metric("Departments", stats["total_departments"])
        with col4:
            st.metric("Today's Appointments", stats["todays_appointments"])
        with col5:
            st.metric("Pending Bills", f"{stats['pending_bills_count']} (₹{stats['pending_bills_amount']:.2f})")
            
        st.markdown("---")
        
        # Today's Appointments Summary Table
        st.subheader("📅 Today's Scheduled Appointments")
        todays_appts = reports_module.get_today_appointments()
        if todays_appts:
            df_today = pd.DataFrame(todays_appts)
            df_today.columns = [
                "Appt ID", "Time Slot", "Status", "Notes", 
                "Patient Name", "Patient Phone", "Doctor Name", "Department"
            ]
            st.dataframe(df_today, use_container_width=True)
        else:
            st.info("No appointments scheduled for today.")
            
    except HospitalAppError as e:
        st.error(f"Error loading dashboard stats: {e}")


# ==========================================
# 2. PATIENTS MODULE
# ==========================================
elif menu_choice == "Patients":
    st.title("👤 Patient Management")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "View & Search Patients", 
        "Register New Patient", 
        "Update Patient Details", 
        "Deactivate / Activate", 
        "Patient History"
    ])
    
    # --- Tab 1: View & Search Patients ---
    with tab1:
        st.subheader("Patient Directory")
        search_query = st.text_input("🔍 Search by Patient ID, Name, or Phone", placeholder="Type patient name, phone, or ID...")
        status_filter = st.radio("Filter Status", ["ALL", "ACTIVE", "INACTIVE"], horizontal=True)
        
        try:
            if search_query.strip():
                patients = patient_module.search_patients(search_query)
            else:
                filter_val = None if status_filter == "ALL" else status_filter
                patients = patient_module.get_all_patients(status_filter=filter_val)
                
            if patients:
                df_p = pd.DataFrame(patients)
                df_p.rename(columns={
                    "patient_id": "ID",
                    "patient_name": "Name",
                    "gender": "Gender",
                    "dob": "DOB",
                    "phone": "Phone",
                    "address": "Address",
                    "blood_group": "Blood Group",
                    "status": "Status",
                    "registered_at": "Registration Date"
                }, inplace=True)
                st.dataframe(df_p, use_container_width=True)
            else:
                st.warning("No patient records found.")
        except HospitalAppError as e:
            st.error(f"Error fetching patients: {e}")

    # --- Tab 2: Register New Patient ---
    with tab2:
        st.subheader("➕ Register New Patient")
        with st.form("register_patient_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                name = st.text_input("Full Name *", placeholder="e.g. John Doe")
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                dob = st.date_input("Date of Birth", min_value=datetime.date(1920, 1, 1), max_value=datetime.date.today())
            with col_b:
                phone = st.text_input("Phone Number *", placeholder="10-digit phone number")
                blood_group = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
                address = st.text_area("Residential Address", placeholder="Street, City, Pin Code")
                
            submit_btn = st.form_submit_button("Register Patient")
            
            if submit_btn:
                try:
                    p_id = patient_module.add_patient(name, gender, dob, phone, address, blood_group)
                    st.success(f"✅ Patient registered successfully! Assigned Patient ID: **{p_id}**")
                except ValidationError as ve:
                    st.warning(f"⚠️ Validation Error: {ve}")
                except HospitalAppError as he:
                    st.error(f"❌ Error: {he}")

    # --- Tab 3: Update Patient Details ---
    with tab3:
        st.subheader("✏️ Update Patient Information")
        patients_list = patient_module.get_all_patients()
        if patients_list:
            patient_map = {f"ID {p['patient_id']} - {p['patient_name']} ({p['phone']})": p['patient_id'] for p in patients_list}
            selected_patient_str = st.selectbox("Select Patient to Update", list(patient_map.keys()))
            selected_pid = patient_map[selected_patient_str]
            
            p_data = patient_module.get_patient_by_id(selected_pid)
            
            with st.form("update_patient_form"):
                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    u_name = st.text_input("Full Name", value=p_data['patient_name'])
                    u_gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(p_data['gender'] or "Male"))
                    u_dob = st.date_input("Date of Birth", value=p_data['dob'] if p_data['dob'] else datetime.date(1990, 1, 1))
                with col_u2:
                    u_phone = st.text_input("Phone Number", value=p_data['phone'])
                    bg_options = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
                    u_bg = st.selectbox("Blood Group", bg_options, index=bg_options.index(p_data['blood_group']) if p_data['blood_group'] in bg_options else 0)
                    u_address = st.text_area("Address", value=p_data['address'] or "")
                    
                update_btn = st.form_submit_button("Update Details")
                if update_btn:
                    try:
                        patient_module.update_patient(selected_pid, u_name, u_gender, u_dob, u_phone, u_address, u_bg)
                        st.success("✅ Patient details updated successfully!")
                    except (ValidationError, HospitalAppError) as e:
                        st.error(f"Error: {e}")
        else:
            st.info("No patients available to update.")

    # --- Tab 4: Deactivate / Activate Patient ---
    with tab4:
        st.subheader("🚫 Deactivate / Activate Patient")
        st.info("Soft delete requirement: Deactivating a patient preserves historical medical data while marking them INACTIVE.")
        all_pts = patient_module.get_all_patients()
        if all_pts:
            pt_options = {f"ID {p['patient_id']} - {p['patient_name']} (Status: {p['status']})": p for p in all_pts}
            sel_pt_str = st.selectbox("Select Patient", list(pt_options.keys()), key="deact_pt_select")
            target_pt = pt_options[sel_pt_str]
            
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if target_pt['status'] == 'ACTIVE':
                    if st.button("🔴 Deactivate Patient", type="secondary"):
                        patient_module.set_patient_status(target_pt['patient_id'], 'INACTIVE')
                        st.success(f"Patient {target_pt['patient_name']} has been set to INACTIVE.")
                        st.rerun()
            with col_act2:
                if target_pt['status'] == 'INACTIVE':
                    if st.button("🟢 Activate Patient", type="primary"):
                        patient_module.set_patient_status(target_pt['patient_id'], 'ACTIVE')
                        st.success(f"Patient {target_pt['patient_name']} has been set to ACTIVE.")
                        st.rerun()

    # --- Tab 5: Patient Appointment History ---
    with tab5:
        st.subheader("📜 Patient Appointment History")
        pts = patient_module.get_all_patients()
        if pts:
            pt_dict = {f"ID {p['patient_id']} - {p['patient_name']}": p['patient_id'] for p in pts}
            selected_h_pid = st.selectbox("Select Patient to View History", list(pt_dict.keys()), key="history_pt_select")
            pid = pt_dict[selected_h_pid]
            
            history = patient_module.get_patient_appointment_history(pid)
            if history:
                df_h = pd.DataFrame(history)
                df_h.columns = [
                    "Appt ID", "Date", "Slot", "Status", "Notes", 
                    "Doctor Name", "Department", "Bill Amount", "Payment Status"
                ]
                st.dataframe(df_h, use_container_width=True)
            else:
                st.info("No appointment history found for this patient.")


# ==========================================
# 3. DOCTORS MODULE
# ==========================================
elif menu_choice == "Doctors":
    st.title("👨‍⚕️ Doctor Management")
    
    doc_tab1, doc_tab2, doc_tab3, doc_tab4, doc_tab5 = st.tabs([
        "View Doctors", 
        "Add Doctor", 
        "Update Doctor Details", 
        "Deactivate / Activate", 
        "Doctor Schedule"
    ])
    
    # --- Tab 1: View Doctors ---
    with doc_tab1:
        st.subheader("Doctor Directory")
        depts = department_module.get_all_departments()
        dept_filter_options = {"All Departments": None}
        for d in depts:
            dept_filter_options[d['dept_name']] = d['dept_id']
            
        selected_dept_label = st.selectbox("Filter by Department", list(dept_filter_options.keys()))
        selected_dept_id = dept_filter_options[selected_dept_label]
        
        doctors = doctor_module.get_all_doctors(dept_id=selected_dept_id)
        if doctors:
            df_doc = pd.DataFrame(doctors)
            df_doc.rename(columns={
                "doctor_id": "Doctor ID",
                "doctor_name": "Doctor Name",
                "dept_name": "Department",
                "phone": "Phone",
                "consultation_fee": "Fee (₹)",
                "available_slots": "Available Timings",
                "status": "Status"
            }, inplace=True)
            columns_to_show = ["Doctor ID", "Doctor Name", "Department", "Phone", "Fee (₹)", "Available Timings", "Status"]
            st.dataframe(df_doc[columns_to_show], use_container_width=True)
        else:
            st.warning("No doctor records found.")

    # --- Tab 2: Add Doctor ---
    with doc_tab2:
        st.subheader("➕ Add New Doctor")
        depts = department_module.get_all_departments()
        if not depts:
            st.warning("Please add at least one department first before registering doctors.")
        else:
            dept_map = {d['dept_name']: d['dept_id'] for d in depts}
            with st.form("add_doctor_form", clear_on_submit=True):
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    doc_name = st.text_input("Doctor Name *", placeholder="Dr. Jane Smith")
                    dept_name_sel = st.selectbox("Department / Specialty *", list(dept_map.keys()))
                    phone = st.text_input("Phone Number *", placeholder="10-digit phone")
                with col_d2:
                    fee = st.number_input("Consultation Fee (₹) *", min_value=0.0, value=500.0, step=50.0)
                    available_slots = st.multiselect(
                        "Available Shift Timings",
                        ["Morning", "Afternoon", "Evening"],
                        default=["Morning", "Evening"]
                    )
                    
                doc_submit = st.form_submit_button("Add Doctor")
                if doc_submit:
                    try:
                        slots_str = ",".join(available_slots) if available_slots else "Morning,Evening"
                        dept_id = dept_map[dept_name_sel]
                        new_doc_id = doctor_module.add_doctor(doc_name, dept_id, phone, fee, slots_str)
                        st.success(f"✅ Doctor registered successfully! Assigned Doctor ID: **{new_doc_id}**")
                    except (ValidationError, HospitalAppError) as e:
                        st.error(f"Error: {e}")

    # --- Tab 3: Update Doctor ---
    with doc_tab3:
        st.subheader("✏️ Update Doctor Profile")
        docs = doctor_module.get_all_doctors()
        depts = department_module.get_all_departments()
        if docs and depts:
            doc_map = {f"ID {d['doctor_id']} - {d['doctor_name']} ({d['dept_name']})": d['doctor_id'] for d in docs}
            dept_id_map = {d['dept_name']: d['dept_id'] for d in depts}
            dept_id_to_name = {d['dept_id']: d['dept_name'] for d in depts}
            
            sel_doc_str = st.selectbox("Select Doctor", list(doc_map.keys()), key="update_doc_select")
            doc_id = doc_map[sel_doc_str]
            curr_doc = doctor_module.get_doctor_by_id(doc_id)
            
            with st.form("update_doc_form"):
                col_u_d1, col_u_d2 = st.columns(2)
                with col_u_d1:
                    u_doc_name = st.text_input("Doctor Name", value=curr_doc['doctor_name'])
                    curr_dept = dept_id_to_name.get(curr_doc['dept_id'], list(dept_id_map.keys())[0])
                    u_dept_name = st.selectbox("Department", list(dept_id_map.keys()), index=list(dept_id_map.keys()).index(curr_dept))
                    u_phone = st.text_input("Phone", value=curr_doc['phone'])
                with col_u_d2:
                    u_fee = st.number_input("Consultation Fee (₹)", min_value=0.0, value=float(curr_doc['consultation_fee']))
                    existing_slots = curr_doc['available_slots'].split(',') if curr_doc['available_slots'] else []
                    u_slots = st.multiselect("Available Timings", ["Morning", "Afternoon", "Evening"], default=[s for s in existing_slots if s in ["Morning", "Afternoon", "Evening"]])
                    
                u_doc_btn = st.form_submit_button("Update Doctor")
                if u_doc_btn:
                    try:
                        slots_str = ",".join(u_slots) if u_slots else "Morning,Evening"
                        doctor_module.update_doctor(doc_id, u_doc_name, dept_id_map[u_dept_name], u_phone, u_fee, slots_str)
                        st.success("✅ Doctor details updated successfully!")
                    except (ValidationError, HospitalAppError) as e:
                        st.error(f"Error: {e}")

    # --- Tab 4: Deactivate / Activate Doctor ---
    with doc_tab4:
        st.subheader("🚫 Deactivate / Activate Doctor")
        all_docs = doctor_module.get_all_doctors()
        if all_docs:
            d_options = {f"ID {d['doctor_id']} - {d['doctor_name']} ({d['status']})": d for d in all_docs}
            sel_d_str = st.selectbox("Select Doctor", list(d_options.keys()), key="deact_doc_select")
            target_d = d_options[sel_d_str]
            
            col_d_act1, col_d_act2 = st.columns(2)
            with col_d_act1:
                if target_d['status'] == 'ACTIVE':
                    if st.button("🔴 Deactivate Doctor", type="secondary", key="deact_doc_btn"):
                        doctor_module.set_doctor_status(target_d['doctor_id'], 'INACTIVE')
                        st.success(f"Doctor {target_d['doctor_name']} set to INACTIVE.")
                        st.rerun()
            with col_d_act2:
                if target_d['status'] == 'INACTIVE':
                    if st.button("🟢 Activate Doctor", type="primary", key="act_doc_btn"):
                        doctor_module.set_doctor_status(target_d['doctor_id'], 'ACTIVE')
                        st.success(f"Doctor {target_d['doctor_name']} set to ACTIVE.")
                        st.rerun()

    # --- Tab 5: Doctor Schedule ---
    with doc_tab5:
        st.subheader("📅 View Doctor's Schedule")
        docs = doctor_module.get_all_doctors(status_filter='ACTIVE')
        if docs:
            doc_select_map = {f"{d['doctor_name']} ({d['dept_name']})": d['doctor_id'] for d in docs}
            sel_doc_sched = st.selectbox("Select Doctor", list(doc_select_map.keys()), key="sched_doc_select")
            sched_date = st.date_input("Select Date", datetime.date.today(), key="sched_date_input")
            
            doc_id = doc_select_map[sel_doc_sched]
            schedule = doctor_module.get_doctor_schedule(doc_id, sched_date)
            
            if schedule:
                df_sch = pd.DataFrame(schedule)
                df_sch.columns = ["Appt ID", "Date", "Slot", "Status", "Notes", "Patient Name", "Patient Phone"]
                st.dataframe(df_sch, use_container_width=True)
            else:
                st.info(f"No appointments scheduled for this doctor on {sched_date}.")


# ==========================================
# 4. DEPARTMENTS MODULE
# ==========================================
elif menu_choice == "Departments":
    st.title("🏢 Department Management")
    
    dept_tab1, dept_tab2, dept_tab3, dept_tab4 = st.tabs([
        "View Departments", 
        "Add Department", 
        "Update Department", 
        "Department Doctors"
    ])
    
    # --- Tab 1: View Departments ---
    with dept_tab1:
        st.subheader("Hospital Departments")
        depts = department_module.get_all_departments()
        if depts:
            df_dept = pd.DataFrame(depts)
            df_dept.rename(columns={
                "dept_id": "ID",
                "dept_name": "Department Name",
                "description": "Description",
                "doctor_count": "Total Doctors"
            }, inplace=True)
            st.dataframe(df_dept, use_container_width=True)
        else:
            st.warning("No departments found.")

    # --- Tab 2: Add Department ---
    with dept_tab2:
        st.subheader("➕ Add New Department")
        with st.form("add_dept_form", clear_on_submit=True):
            dept_name = st.text_input("Department Name *", placeholder="e.g. Oncology, Dermatology")
            description = st.text_area("Description", placeholder="Short overview of the department specialty...")
            dept_submit = st.form_submit_button("Add Department")
            
            if dept_submit:
                try:
                    new_dept_id = department_module.add_department(dept_name, description)
                    st.success(f"✅ Department '{dept_name}' added successfully! ID: **{new_dept_id}**")
                except (ValidationError, HospitalAppError) as e:
                    st.error(f"Error: {e}")

    # --- Tab 3: Update Department ---
    with dept_tab3:
        st.subheader("✏️ Update Department")
        depts = department_module.get_all_departments()
        if depts:
            dept_map = {f"ID {d['dept_id']} - {d['dept_name']}": d['dept_id'] for d in depts}
            sel_dept_str = st.selectbox("Select Department to Edit", list(dept_map.keys()))
            d_id = dept_map[sel_dept_str]
            curr_dept = department_module.get_department_by_id(d_id)
            
            with st.form("update_dept_form"):
                u_dept_name = st.text_input("Department Name", value=curr_dept['dept_name'])
                u_description = st.text_area("Description", value=curr_dept['description'] or "")
                u_dept_btn = st.form_submit_button("Update Department")
                
                if u_dept_btn:
                    try:
                        department_module.update_department(d_id, u_dept_name, u_description)
                        st.success("✅ Department details updated successfully!")
                    except (ValidationError, HospitalAppError) as e:
                        st.error(f"Error: {e}")

    # --- Tab 4: Department Doctors ---
    with dept_tab4:
        st.subheader("🩺 Doctors in Department")
        depts = department_module.get_all_departments()
        if depts:
            dept_map = {d['dept_name']: d['dept_id'] for d in depts}
            selected_dname = st.selectbox("Select Department", list(dept_map.keys()), key="dept_docs_select")
            d_id = dept_map[selected_dname]
            
            dept_doctors = department_module.get_doctors_by_department(d_id)
            if dept_doctors:
                df_dd = pd.DataFrame(dept_doctors)
                df_dd.rename(columns={
                    "doctor_id": "Doctor ID",
                    "doctor_name": "Doctor Name",
                    "phone": "Phone",
                    "consultation_fee": "Fee (₹)",
                    "available_slots": "Slots",
                    "status": "Status"
                }, inplace=True)
                st.dataframe(df_dd[["Doctor ID", "Doctor Name", "Phone", "Fee (₹)", "Slots", "Status"]], use_container_width=True)
            else:
                st.info("No doctors assigned to this department yet.")


# ==========================================
# 5. APPOINTMENTS MODULE (CORE)
# ==========================================
elif menu_choice == "Appointments":
    st.title("📌 Appointment Scheduling & Management")
    
    appt_tab1, appt_tab2, appt_tab3, appt_tab4 = st.tabs([
        "Book Appointment", 
        "View Appointments", 
        "Reschedule / Cancel", 
        "Mark Status (Complete / No-Show)"
    ])
    
    # Standard Time Slots
    TIME_SLOTS = [
        "09:00 - 09:30 AM",
        "09:30 - 10:00 AM",
        "10:00 - 10:30 AM",
        "10:30 - 11:00 AM",
        "11:00 - 11:30 AM",
        "11:30 - 12:00 PM",
        "04:00 - 04:30 PM",
        "04:30 - 05:00 PM",
        "05:00 - 05:30 PM",
        "05:30 - 06:00 PM"
    ]
    
    # --- Tab 1: Book Appointment ---
    with appt_tab1:
        st.subheader("🗓️ Book New Appointment")
        
        patients = patient_module.get_all_patients(status_filter='ACTIVE')
        departments = department_module.get_all_departments()
        
        if not patients:
            st.warning("⚠️ No active patients found. Please register a patient first.")
        elif not departments:
            st.warning("⚠️ No departments found. Please add a department and doctor first.")
        else:
            pt_map = {f"ID {p['patient_id']} - {p['patient_name']} ({p['phone']})": p['patient_id'] for p in patients}
            dept_map = {d['dept_name']: d['dept_id'] for d in departments}
            
            st.markdown("#### Booking Workflow Steps:")
            col_b1, col_b2 = st.columns(2)
            
            with col_b1:
                sel_pt_label = st.selectbox("1. Select Patient *", list(pt_map.keys()))
                sel_dept_label = st.selectbox("2. Select Department *", list(dept_map.keys()))
                
                # Fetch doctors belonging to selected department
                dept_id = dept_map[sel_dept_label]
                avail_doctors = doctor_module.get_all_doctors(dept_id=dept_id, status_filter='ACTIVE')
                
                if avail_doctors:
                    doc_map = {f"Dr. {d['doctor_name']} (Fee: ₹{d['consultation_fee']:.2f})": d['doctor_id'] for d in avail_doctors}
                    sel_doc_label = st.selectbox("3. Select Doctor *", list(doc_map.keys()))
                else:
                    st.error("No active doctors in this department.")
                    sel_doc_label = None

            with col_b2:
                appt_date = st.date_input("4. Select Date *", min_value=datetime.date.today(), value=datetime.date.today())
                selected_slot = st.selectbox("5. Select Time Slot *", TIME_SLOTS)
                notes = st.text_area("6. Symptoms / Notes", placeholder="Brief description of concern...")
                
            if sel_doc_label and st.button("Confirm & Book Appointment", type="primary"):
                try:
                    patient_id = pt_map[sel_pt_label]
                    doctor_id = doc_map[sel_doc_label]
                    date_str = appt_date.strftime("%Y-%m-%d")
                    
                    appt_id = appointment_module.book_appointment(patient_id, doctor_id, date_str, selected_slot, notes)
                    st.success(f"🎉 Appointment booked successfully! Booking Reference ID: **{appt_id}**")
                    st.balloons()
                except AppointmentSlotUnavailableError as ase:
                    st.error(f"❌ Slot Unavailable: {ase}")
                except (ValidationError, HospitalAppError) as e:
                    st.error(f"❌ Booking Error: {e}")

    # --- Tab 2: View Appointments ---
    with appt_tab2:
        st.subheader("🔍 Appointment Directory & Filters")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            use_date_filter = st.checkbox("Filter by Date")
            filter_date = st.date_input("Appointment Date", datetime.date.today()) if use_date_filter else None
        with col_f2:
            all_docs = doctor_module.get_all_doctors()
            doc_filter_map = {"All Doctors": None}
            for d in all_docs:
                doc_filter_map[f"Dr. {d['doctor_name']}"] = d['doctor_id']
            sel_doc_filter_label = st.selectbox("Filter by Doctor", list(doc_filter_map.keys()))
            filter_doc_id = doc_filter_map[sel_doc_filter_label]
        with col_f3:
            filter_status = st.selectbox("Filter Status", ["ALL", "BOOKED", "COMPLETED", "CANCELLED", "NO_SHOW"])
            status_val = None if filter_status == "ALL" else filter_status
            
        date_val = filter_date.strftime("%Y-%m-%d") if filter_date else None
        appts = appointment_module.get_all_appointments(date_filter=date_val, doctor_id=filter_doc_id, status_filter=status_val)
        
        if appts:
            df_appts = pd.DataFrame(appts)
            df_appts.rename(columns={
                "appointment_id": "Appt ID",
                "appointment_date": "Date",
                "time_slot": "Slot",
                "status": "Status",
                "patient_name": "Patient Name",
                "patient_phone": "Patient Phone",
                "doctor_name": "Doctor Name",
                "dept_name": "Department",
                "payment_status": "Payment Status",
                "notes": "Notes"
            }, inplace=True)
            cols = ["Appt ID", "Date", "Slot", "Status", "Patient Name", "Patient Phone", "Doctor Name", "Department", "Payment Status", "Notes"]
            st.dataframe(df_appts[cols], use_container_width=True)
        else:
            st.info("No matching appointments found.")

    # --- Tab 3: Reschedule / Cancel ---
    with appt_tab3:
        st.subheader("🔄 Reschedule or Cancel Appointment")
        active_appts = appointment_module.get_all_appointments(status_filter='BOOKED')
        
        if not active_appts:
            st.info("No active 'BOOKED' appointments available to reschedule or cancel.")
        else:
            appt_options = {
                f"Appt #{a['appointment_id']} | {a['appointment_date']} ({a['time_slot']}) | Patient: {a['patient_name']} -> Doctor: Dr. {a['doctor_name']}": a
                for a in active_appts
            }
            selected_appt_str = st.selectbox("Select Appointment", list(appt_options.keys()))
            target_appt = appt_options[selected_appt_str]
            
            st.markdown("---")
            col_rc1, col_rc2 = st.columns(2)
            
            with col_rc1:
                st.markdown("##### 📅 Reschedule Slot")
                new_date = st.date_input("New Date", min_value=datetime.date.today(), value=datetime.date.today(), key="resched_date")
                new_slot = st.selectbox("New Time Slot", TIME_SLOTS, key="resched_slot")
                
                if st.button("Confirm Reschedule", type="primary"):
                    try:
                        appointment_module.reschedule_appointment(
                            target_appt['appointment_id'], 
                            new_date.strftime("%Y-%m-%d"), 
                            new_slot
                        )
                        st.success("✅ Appointment rescheduled successfully!")
                        st.rerun()
                    except (AppointmentSlotUnavailableError, HospitalAppError) as e:
                        st.error(f"❌ Error: {e}")

            with col_rc2:
                st.markdown("##### ❌ Cancel Booking")
                st.warning("Cancelling will update status to 'CANCELLED' and free the doctor's slot.")
                if st.button("Cancel Appointment", type="secondary"):
                    try:
                        appointment_module.cancel_appointment(target_appt['appointment_id'])
                        st.success("✅ Appointment cancelled.")
                        st.rerun()
                    except HospitalAppError as e:
                        st.error(f"❌ Error: {e}")

    # --- Tab 4: Mark Status ---
    with appt_tab4:
        st.subheader("✅ Consultation Status Update")
        booked_appts = appointment_module.get_all_appointments(status_filter='BOOKED')
        
        if not booked_appts:
            st.info("No pending booked appointments to update.")
        else:
            b_map = {
                f"Appt #{a['appointment_id']} | {a['patient_name']} with Dr. {a['doctor_name']} on {a['appointment_date']} ({a['time_slot']})": a
                for a in booked_appts
            }
            sel_b_str = st.selectbox("Select Appointment to Mark", list(b_map.keys()))
            selected_b_appt = b_map[sel_b_str]
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                if st.button("Mark as COMPLETED (Consultation Done)", type="primary"):
                    try:
                        appointment_module.update_appointment_status(selected_b_appt['appointment_id'], 'COMPLETED')
                        st.success("✅ Appointment marked as COMPLETED! Bill can now be generated.")
                        st.rerun()
                    except HospitalAppError as e:
                        st.error(f"Error: {e}")
            with col_m2:
                if st.button("Mark as NO_SHOW (Patient Absent)", type="secondary"):
                    try:
                        appointment_module.update_appointment_status(selected_b_appt['appointment_id'], 'NO_SHOW')
                        st.warning("Appointment marked as NO_SHOW.")
                        st.rerun()
                    except HospitalAppError as e:
                        st.error(f"Error: {e}")


# ==========================================
# 6. BILLING MODULE
# ==========================================
elif menu_choice == "Billing":
    st.title("💳 Consultation Billing & Payments")
    
    bill_tab1, bill_tab2 = st.tabs(["Generate Bill", "View & Pay Bills"])
    
    # --- Tab 1: Generate Bill ---
    with bill_tab1:
        st.subheader("🧾 Generate Consultation Bill")
        st.info("💡 PDF Requirement: Bills can ONLY be generated for appointments marked as **COMPLETED**.")
        
        completed_appts = appointment_module.get_all_appointments(status_filter='COMPLETED')
        
        if not completed_appts:
            st.warning("No completed appointments found that require billing. Mark an appointment as COMPLETED first.")
        else:
            # Filter out appointments that already have a bill generated
            unbilled_appts = [a for a in completed_appts if not a.get('bill_id')]
            
            if not unbilled_appts:
                st.success("All completed appointments have already been billed!")
            else:
                unbilled_map = {
                    f"Appt #{a['appointment_id']} | Patient: {a['patient_name']} | Dr. {a['doctor_name']} (Base Fee: ₹{a['consultation_fee']:.2f})": a
                    for a in unbilled_appts
                }
                sel_unbilled_str = st.selectbox("Select Completed Appointment to Bill", list(unbilled_map.keys()))
                target_unbilled = unbilled_map[sel_unbilled_str]
                
                base_fee = float(target_unbilled['consultation_fee'])
                
                with st.form("generate_bill_form"):
                    st.write(f"**Patient Name:** {target_unbilled['patient_name']}")
                    st.write(f"**Doctor:** Dr. {target_unbilled['doctor_name']} ({target_unbilled['dept_name']})")
                    st.write(f"**Base Consultation Fee:** ₹{base_fee:.2f}")
                    
                    extra_charges = st.number_input("Optional Extra Charges (Lab, Medicines, Services) ₹", min_value=0.0, value=0.0, step=50.0)
                    total_calculated = base_fee + extra_charges
                    
                    st.subheader(f"Total Amount Payable: ₹{total_calculated:.2f}")
                    
                    gen_btn = st.form_submit_button("Generate Bill")
                    if gen_btn:
                        try:
                            bill_id = billing_module.generate_bill(target_unbilled['appointment_id'], extra_charges)
                            st.success(f"🎉 Bill generated successfully! Bill ID: **{bill_id}** | Total Amount: **₹{total_calculated:.2f}**")
                            st.rerun()
                        except BillingError as be:
                            st.warning(f"⚠️ Billing Error: {be}")
                        except HospitalAppError as he:
                            st.error(f"❌ Error: {he}")

    # --- Tab 2: View & Pay Bills ---
    with bill_tab2:
        st.subheader("📋 Bills Directory & Payment Processing")
        
        status_filter_choice = st.radio("Filter Bills", ["ALL", "PENDING", "PAID"], horizontal=True)
        filter_val = None if status_filter_choice == "ALL" else status_filter_choice
        
        all_bills = billing_module.get_all_bills(payment_status_filter=filter_val)
        
        if all_bills:
            df_bills = pd.DataFrame(all_bills)
            df_bills.rename(columns={
                "bill_id": "Bill ID",
                "appointment_id": "Appt ID",
                "patient_name": "Patient Name",
                "doctor_name": "Doctor Name",
                "dept_name": "Department",
                "amount": "Amount (₹)",
                "payment_status": "Payment Status",
                "billed_at": "Billed Date"
            }, inplace=True)
            cols = ["Bill ID", "Appt ID", "Patient Name", "Doctor Name", "Department", "Amount (₹)", "Payment Status", "Billed Date"]
            st.dataframe(df_bills[cols], use_container_width=True)
            
            # Action: Mark Bill as PAID
            pending_bills = [b for b in all_bills if b['payment_status'] == 'PENDING']
            if pending_bills:
                st.markdown("---")
                st.markdown("#### 💳 Process Payment")
                p_map = {f"Bill #{b['bill_id']} - Patient: {b['patient_name']} (Amount: ₹{b['amount']:.2f})": b['bill_id'] for b in pending_bills}
                sel_pay_str = st.selectbox("Select Pending Bill to Mark as PAID", list(p_map.keys()))
                pay_bill_id = p_map[sel_pay_str]
                
                if st.button("Mark Bill as PAID", type="primary"):
                    try:
                        billing_module.mark_bill_paid(pay_bill_id)
                        st.success(f"✅ Bill #{pay_bill_id} marked as PAID!")
                        st.rerun()
                    except HospitalAppError as e:
                        st.error(f"Error: {e}")
        else:
            st.info("No bill records found.")


# ==========================================
# 7. REPORTS MODULE
# ==========================================
elif menu_choice == "Reports":
    st.title("📊 Management & Financial Reports")
    
    rep_tab1, rep_tab2, rep_tab3, rep_tab4, rep_tab5 = st.tabs([
        "Today's Appointments", 
        "Date Range Search", 
        "Doctor Appointment Counts", 
        "Revenue Summary", 
        "Cancelled / No-Show Stats"
    ])
    
    # --- Report 1: Today's Appointments ---
    with rep_tab1:
        st.subheader("📅 Today's Appointments Report")
        t_appts = reports_module.get_today_appointments()
        if t_appts:
            st.dataframe(pd.DataFrame(t_appts), use_container_width=True)
        else:
            st.info("No appointments scheduled for today.")

    # --- Report 2: Date Range Search ---
    with rep_tab2:
        st.subheader("📆 Appointments in Date Range")
        col_dr1, col_dr2 = st.columns(2)
        with col_dr1:
            start_date = st.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=7))
        with col_dr2:
            end_date = st.date_input("End Date", datetime.date.today())
            
        if start_date > end_date:
            st.error("Start Date cannot be later than End Date.")
        else:
            range_appts = reports_module.get_appointments_by_date_range(
                start_date.strftime("%Y-%m-%d"), 
                end_date.strftime("%Y-%m-%d")
            )
            if range_appts:
                st.dataframe(pd.DataFrame(range_appts), use_container_width=True)
            else:
                st.info("No appointments found in the selected date range.")

    # --- Report 3: Doctor Appointment Counts ---
    with rep_tab3:
        st.subheader("🩺 Doctor-wise Appointment Summary")
        doc_counts = reports_module.get_doctor_wise_appointment_counts()
        if doc_counts:
            df_dc = pd.DataFrame(doc_counts)
            df_dc.rename(columns={
                "doctor_id": "Doctor ID",
                "doctor_name": "Doctor Name",
                "dept_name": "Department",
                "total_appointments": "Total Booked",
                "completed_count": "Completed",
                "booked_count": "Pending Booked",
                "cancelled_count": "Cancelled",
                "noshow_count": "No-Show"
            }, inplace=True)
            st.dataframe(df_dc, use_container_width=True)
        else:
            st.info("No doctor appointment data available.")

    # --- Report 4: Revenue Summary ---
    with rep_tab4:
        st.subheader("💰 Revenue & Billing Summary")
        rev = reports_module.get_revenue_summary()
        if rev:
            df_rev = pd.DataFrame(rev)
            df_rev.rename(columns={
                "payment_status": "Payment Status",
                "bill_count": "Count",
                "total_amount": "Total Amount (₹)"
            }, inplace=True)
            st.dataframe(df_rev, use_container_width=True)
        else:
            st.info("No billing revenue data available.")

    # --- Report 5: Cancelled / No-Show Stats ---
    with rep_tab5:
        st.subheader("📉 Cancelled & No-Show Statistics")
        cn_stats = reports_module.get_cancelled_noshow_stats()
        if cn_stats:
            st.dataframe(pd.DataFrame(cn_stats), use_container_width=True)
        else:
            st.info("No cancellation or no-show records found.")