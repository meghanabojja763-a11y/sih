import streamlit as st
import pandas as pd
import random
import uuid
from datetime import datetime

# (Other utility functions omitted for brevity, same as above except with messages removed)

def move_employee_back_to_employees(employee_id, employee_file="Employee_with_ID_with_random_skills.csv", assigned_file="assigned_employees.csv", completed_file="completed_employees.csv"):
    employees_df = pd.read_csv(employee_file)
    try:
        assigned_df = pd.read_csv(assigned_file)
    except FileNotFoundError:
        # Assigned file missing, just return employees_df
        return employees_df

    if employee_id not in assigned_df['EmployeeID'].values:
        # Employee is not currently assigned; no message to UI
        return employees_df

    emp_row = assigned_df[assigned_df['EmployeeID'] == employee_id]

    # Add back to employees.csv
    employees_df = pd.concat([employees_df, emp_row], ignore_index=True)
    employees_df.to_csv(employee_file, index=False)

    # Remove from assigned.csv
    assigned_df = assigned_df.drop(emp_row.index)
    assigned_df.to_csv(assigned_file, index=False)

    # Add to completed.csv
    try:
        completed_df = pd.read_csv(completed_file)
    except FileNotFoundError:
        completed_df = pd.DataFrame(columns=emp_row.columns)
    completed_df = pd.concat([completed_df, emp_row], ignore_index=True)
    completed_df.to_csv(completed_file, index=False)

    # No UI message, silent success
    return employees_df

# Use your existing upload, add, update, delete employee/project code here, omitting messages as desired

# Assignment logic:
projects_sorted = projects.sort_values(by='Deadline').reset_index(drop=True)
assignments = []
employee_project_map = {}

try:
    assigned_employees_df = pd.read_csv("assigned_employees.csv")
    assigned_ids = set(assigned_employees_df['EmployeeID'].values)
except FileNotFoundError:
    assigned_employees_df = pd.DataFrame(columns=employees.columns)
    assigned_ids = set()

for i, task in projects_sorted.iterrows():
    available_employees = [
        e for e in employees['EmployeeID'].tolist()
        if e not in assigned_ids and task['Project Name'] not in employee_project_map.get(e, set())
    ]
    if not available_employees:
        assigned_employee = None
    else:
        assigned_employee = random.choice(available_employees)
        employee_project_map.setdefault(assigned_employee, set()).add(task['Project Name'])
        employees = move_employee_to_assigned(assigned_employee, employees, employee_file)
        # Update assigned_ids for next loops
        assigned_ids.add(assigned_employee)

    assignments.append({
        'Project Name': task['Project Name'],
        'Deadline': task['Deadline'],
        'Sub Task': task['Sub Task'],
        'Skills Required': task['Skills Required'],
        'Assigned EmployeeID': assigned_employee
    })

df_assignments = pd.DataFrame(assignments)
df_assignments.to_csv("project_task_assignments.csv", index=False)
# Save latest assigned employees
employees_assigned = pd.read_csv("assigned_employees.csv")
employees_assigned.to_csv("assigned_employees.csv", index=False)

# Auto-move back employees if deadline passed (silent)
today = pd.to_datetime(datetime.now().date())

try:
    assigned_employees_df = pd.read_csv("assigned_employees.csv")
except FileNotFoundError:
    assigned_employees_df = pd.DataFrame(columns=employees.columns)

assignments_df = pd.read_csv("project_task_assignments.csv")
assignments_df['Deadline'] = pd.to_datetime(assignments_df['Deadline'], errors='coerce')

for _, row in assignments_df.iterrows():
    if pd.notnull(row['Deadline']) and row['Deadline'] < today and pd.notnull(row['Assigned EmployeeID']):
        emp_id = row['Assigned EmployeeID']
        employees = move_employee_back_to_employees(emp_id, employee_file)

# Mark Task Completed UI without messages
if st.sidebar.checkbox("Mark Task Completed"):
    emp_complete = st.text_input("Enter EmployeeID who completed task").strip()
    if st.button("Mark Completed"):
        employees = move_employee_back_to_employees(emp_complete, employee_file)

# Display only the CSV tables
st.success("Assignments saved to project_task_assignments.csv")
st.dataframe(df_assignments)

try:
    assigned_emps = pd.read_csv("assigned_employees.csv")
    st.write("Currently Assigned Employees")
    st.dataframe(assigned_emps)
except FileNotFoundError:
    st.write("No assigned employees yet.")

try:
    completed_emps = pd.read_csv("completed_employees.csv")
    st.write("Completed Employees")
    st.dataframe(completed_emps)
except FileNotFoundError:
    st.write("No completed employees yet.")
