scikit-learn
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

# Load employees and projects
employees = pd.read_csv('employees.csv')
projects = pd.read_csv('projects.csv')

# Vectorize skills
employee_skills = employees['skills'].fillna('')
project_skills = projects['Skills Required'].fillna('')

vectorizer = TfidfVectorizer(tokenizer=lambda x: x.split(','))
employee_skill_matrix = vectorizer.fit_transform(employee_skills)
project_skill_matrix = vectorizer.transform(project_skills)

# Use KNN to find best employee for each project based on skills similarity
knn = NearestNeighbors(n_neighbors=1, metric='cosine').fit(employee_skill_matrix)

distances, indices = knn.kneighbors(project_skill_matrix)

assignments = []
for i, idx in enumerate(indices.flatten()):
    assigned_employee = employees.iloc[idx]['EmployeeID']
    assignments.append({
        'Project Name': projects.iloc[i]['Project Name'],
        'Deadline': projects.iloc[i]['Deadline'],
        'Sub Task': projects.iloc[i]['Sub Task'],
        'Skills Required': projects.iloc[i]['Skills Required'],
        'Assigned EmployeeID': assigned_employee
    })

assignments_df = pd.DataFrame(assignments)
assignments_df.to_csv('project_task_assignments_ml.csv', index=False)
