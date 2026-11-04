# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Configure teacher login credentials and a signing secret in the environment. Do not commit real credentials:

   ```
   export TEACHER_USERNAME="teacher"
   export TEACHER_PASSWORD="replace-with-a-strong-password"
   export TEACHER_TOKEN_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
   ```

3. Run the application:

   ```
   python app.py
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/auth/login`                                                      | Sign in as a teacher and receive an expiring bearer token            |
| GET    | `/auth/me`                                                         | Validate the current teacher session                                |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Register a student (teacher token required)                          |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a student (teacher token required)                    |

The browser keeps the teacher token for the current tab session. The API requires it for both roster-changing endpoints; hiding controls in the page is not the security boundary. Students can still view activities and participant lists without signing in.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
