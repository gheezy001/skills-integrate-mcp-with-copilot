"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from base64 import urlsafe_b64decode, urlsafe_b64encode
from hashlib import sha256
import hmac
import json
import os
import time
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

teacher_auth = HTTPBearer(auto_error=False)
TOKEN_LIFETIME_SECONDS = 8 * 60 * 60


class TeacherCredentials(BaseModel):
    username: str
    password: str


def _teacher_configured():
    return all(os.getenv(key) for key in (
        "TEACHER_USERNAME", "TEACHER_PASSWORD", "TEACHER_TOKEN_SECRET"
    ))


def _encode_token_part(value: bytes) -> str:
    return urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _create_teacher_token(username: str) -> str:
    payload = _encode_token_part(json.dumps({
        "sub": username,
        "exp": int(time.time()) + TOKEN_LIFETIME_SECONDS,
    }).encode("utf-8"))
    secret = os.environ["TEACHER_TOKEN_SECRET"].encode("utf-8")
    signature = hmac.new(secret, payload.encode("ascii"), sha256).digest()
    return f"{payload}.{_encode_token_part(signature)}"


def require_teacher(
    credentials: HTTPAuthorizationCredentials | None = Depends(teacher_auth),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Teacher authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not _teacher_configured():
        raise HTTPException(status_code=503, detail="Teacher login is not configured")

    try:
        payload_part, signature_part = credentials.credentials.split(".", 1)
        secret = os.environ["TEACHER_TOKEN_SECRET"].encode("utf-8")
        expected_signature = hmac.new(
            secret, payload_part.encode("ascii"), sha256
        ).digest()
        actual_signature = urlsafe_b64decode(
            signature_part + "=" * (-len(signature_part) % 4)
        )
        if not hmac.compare_digest(expected_signature, actual_signature):
            raise ValueError("Invalid token signature")

        payload = json.loads(urlsafe_b64decode(
            payload_part + "=" * (-len(payload_part) % 4)
        ))
        if (payload.get("sub") != os.environ["TEACHER_USERNAME"] or
                payload.get("exp", 0) <= time.time()):
            raise ValueError("Expired or invalid token")
        return payload["sub"]
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired teacher session",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


@app.post("/auth/login")
def teacher_login(credentials: TeacherCredentials):
    if not _teacher_configured():
        raise HTTPException(status_code=503, detail="Teacher login is not configured")

    username_matches = hmac.compare_digest(
        credentials.username, os.environ["TEACHER_USERNAME"]
    )
    password_matches = hmac.compare_digest(
        credentials.password, os.environ["TEACHER_PASSWORD"]
    )
    if not (username_matches and password_matches):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {
        "access_token": _create_teacher_token(credentials.username),
        "token_type": "bearer",
    }


@app.get("/auth/me")
def get_teacher_session(username: str = Depends(require_teacher)):
    return {"username": username}

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str,
    _teacher: str = Depends(require_teacher),
):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    _teacher: str = Depends(require_teacher),
):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
