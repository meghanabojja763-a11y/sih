import streamlit as st
import pandas as pd
import random
import uuid
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------- Utility Functions ----------
def generate_unique_employee_id():
    return "E" + str(uuid.uuid4()).split('-')[0]

def add_employee(employees_df, new_employee, employee_file):
    new_employee['EmployeeID'] = generate_unique_employee_id()
    employees_df = pd.concat([employees_df, pd.DataFrame([new_employee])], ignore_index=True)
    st.success(f"Added new employee with ID {new_employee['EmployeeID']}")
    employees_df.to_csv(employee_file, index=False)
    return employees_df

def update_employee(employees_df, employee_id, updated_fields, employee_file):
    if employee_id not in employees_df['EmployeeID'].values:
        st.error(f"EmployeeID {employee_id} not found.")
        return employees_df
    for key, val in updated_fields.items():
        employees_df.loc[employees_df['EmployeeID'] == employee_id, key] = val
    st.success(f"Updated employee {employee_id}.")
    employees_df.to_csv(employee_file, index=False)
    return employees_df

def delete_employee(employees_df, employee_id, employee_file):
    if employee_id not in employees_df['EmployeeID'].values:
        st.error(f"EmployeeID {employee_id} not found.")
        return employees_df
    employees_df = employees_df.drop(employees_df[employees_df['EmployeeID'] == employee_id].index)
    st.success(f"Deleted employee {employee_id}.")
    employees_df.to_csv(employee_file, index=False)
    return employees_df

def add_project(projects_df, new_project, project_file):
    projects_df = pd.concat([projects_df, pd.DataFrame([new_project])], ignore_index=True)
    st.success(f"Added new project '{new_project['Project Name']}'")
    projects_df.to_csv(project_file, index=False)
    return projects_df

def move_employee_to_assigned(employee_id, employees_df, employee_file, assigned_file="assigned_employees.csv"):
    if employee_id not in employees_df['EmployeeID'].values:
        return employees_df
    try:
        assigned_df = pd.read_csv(assigned_file)
        if assigned_df.empty or list(assigned_df.columns) != list(employees_df.columns):
            assigned_df = pd.DataFrame(columns=employees_df.columns)
    except:
        assigned_df = pd.DataFrame(columns=employees_df.columns)
    emp_row = employees_df[employees_df['EmployeeID'] == employee_id]
    assigned_df = pd.concat([assigned_df, emp_row], ignore_index=True)
    assigned_df.to_csv(assigned_file, index=False)
    employees_df = employees_df.drop(emp_row.index)
    employees_df.to_csv(employee_file, index=False)
    return employees_df

@st.cache_data
def load_employees(path):
    try:
        df = pd.read_csv(path)
        if df.empty:
            st.warning("Employee file is empty.")
            return pd.DataFrame()
        return df
    except Exception as e:
        st.warning(f"Error reading employees file: {e}")
        return pd.DataFrame()

@st.cache_data
def load_projects(path):
    try:
        df = pd.read_csv(path)
        if df.empty:
            st.warning("Project file is empty.")
            return pd.DataFrame()
        df['Deadline'] = pd.to_datetime(df['Deadline'], errors='coerce')
        return df
    except Exception as e:
        st.warning(f"Error reading projects file: {e}")
        return pd.DataFrame()

# ------------ Streamlit UI ------------

st.sidebar.header("📂 Upload CSV Files")
employee_file_upload = st.sidebar.file_uploader("Upload Employee CSV", type=["csv"])
project_file_upload = st.sidebar.file_uploader("Upload Project CSV", type=["csv"])

if employee_file_upload is not None and project_file_upload is not None:
    employee_file_upload.seek(0)
    project_file_upload.seek(0)
    employee_file = "Employee_with_ID_with_random_skills.csv"
    project_file = "project_tasks_500.csv"
    with open(employee_file, "wb") as f:
        f.write(employee_file_upload.getbuffer())
    with open(project_file, "wb") as f:
        f.write(project_file_upload.getbuffer())
else:
    st.warning("Please upload both Employee and Project CSV files to proceed.")
    st.stop()

employees = load_employees(employee_file)
projects = load_projects(project_file)

st.title("Employee and Project Management with ML Skill Matching")

# Example for Add New Employee (you can replicate Update and Delete similarly)
if st.sidebar.checkbox("Add New Employee"):
    with st.form("add_employee_form"):
        education = st.text_input("Education")
        joining_year = st.number_input("Joining Year", 1950, datetime.now().year)
        city = st.text_input("City")
        payment_tier = st.number_input("Payment Tier", 1)
        age = st.number_input("Age", 18)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        ever_benched = st.selectbox("Ever Benched", ["Yes", "No"])
        experience = st.number_input("Experience in Current Domain (years)", 0)
        leave_or_not = st.selectbox("Leave or Not", [0, 1])
        skills = st.text_input("Skills (comma separated)")
        submit = st.form_submit_button("Add Employee")
        if submit:
            new_employee = {
                'Education': education,
                'JoiningYear': joining_year,
                'City': city,
                'PaymentTier': payment_tier,
                'Age': age,
                'Gender': gender,
                'EverBenched': ever_benched,
                'ExperienceInCurrentDomain': experience,
                'LeaveOrNot': leave_or_not,
                'skills': skills
            }
            employees = add_employee(employees, new_employee, employee_file)
            employees = load_employees(employee_file)

# ML Skill Matching Assignment
if not employees.empty and not projects.empty:
    projects_sorted = projects.sort_values(by='Deadline').reset_index(drop=True)
    assignments = []
    employee_project_map = {}

    employee_corpus = employees['skills'].fillna("").tolist()
    project_corpus = projects_sorted['Skills Required'].fillna("").tolist()

    vectorizer = TfidfVectorizer()
    combined_corpus = employee_corpus + project_corpus
    vectorizer.fit(combined_corpus)

    employee_vectors = vectorizer.transform(employee_corpus)
    project_vectors = vectorizer.transform(project_corpus)

    for idx, task in projects_sorted.iterrows():
        project_vec = project_vectors[idx]
        similarities = cosine_similarity(project_vec, employee_vectors).flatten()

        assigned_emps = set(employee_project_map.keys())
        available_indices = [i for i, e_id in enumerate(employees['EmployeeID']) if e_id not in assigned_emps]

        if not available_indices:
            assigned_employee = None
        else:
            max_sim = -1
            best_emp_idx = None
            for i in available_indices:
                if similarities[i] > max_sim:
                    max_sim = similarities[i]
                    best_emp_idx = i
            assigned_employee = employees.iloc[best_emp_idx]['EmployeeID']
            employee_project_map.setdefault(assigned_employee, set()).add(task['Project Name'])
            employees = move_employee_to_assigned(assigned_employee, employees, employee_file)

        assignments.append({
            'Project Name': task['Project Name'],
            'Deadline': task['Deadline'],
            'Sub Task': task['Sub Task'],
            'Skills Required': task['Skills Required'],
            'Assigned EmployeeID': assigned_employee
        })

    df_assignments = pd.DataFrame(assignments)
    df_assignments.to_csv("project_task_assignments.csv", index=False)
    st.success("Project assignments completed with ML-driven skill matching.")
    st.dataframe(df_assignments)
else:
    st.warning("Employee or Project data is empty. Please upload valid CSVs.")
