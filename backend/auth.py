# Authentication related endpoints
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel
import requests
import os
import logging
from datetime import datetime
from models import User
from config import get_db
from research_threshold_calculator import calculate_initial_thresholds_for_new_user

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRegistration(BaseModel):
    email: str
    password: str
    age: int = None
    gender: str = None
    weight: float = None

class UserLogin(BaseModel):
    email: str
    password: str

@router.post("/register")
def register(user: UserRegistration, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(user.password)
    db_user = User(
        email=user.email,
        password_hash=hashed_password,
        age=user.age,
        gender=user.gender,
        weight=user.weight
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "User registered successfully", "user_id": db_user.user_id}

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not pwd_context.verify(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"message": "Login successful", "user_id": db_user.user_id}

@router.get("/strava/auth")
def strava_auth():
    client_id = os.getenv("STRAVA_CLIENT_ID")
    redirect_uri = os.getenv("STRAVA_REDIRECT_URI")
    scope = "read,activity:read_all,profile:read_all"  # Use profile:read_all instead of email
    auth_url = f"https://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope={scope}"
    return RedirectResponse(auth_url)

@router.get("/strava/callback")
def strava_callback(code: str, db: Session = Depends(get_db)):
    logging.info(f"🔍 BACKEND DEBUG: Strava callback received with code: {code[:10]}...")
    
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")
    redirect_uri = os.getenv("STRAVA_REDIRECT_URI")

    # Exchange code for token
    token_url = "https://www.strava.com/oauth/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code"
    }
    token_response = requests.post(token_url, data=data)
    if token_response.status_code != 200:
        logging.error(f"🔍 BACKEND DEBUG: Failed to get Strava token: {token_response.status_code}")
        raise HTTPException(status_code=400, detail="Failed to get Strava token")

    token_data = token_response.json()
    athlete = token_data.get("athlete", {})
    logging.info(f"🔍 BACKEND DEBUG: Received athlete data: {athlete}")

    # Strava doesn't provide email addresses, so we'll use generated email for backend
    # but let the frontend onboarding form collect the real email
    strava_email = f"{athlete.get('id')}@strava.local"
    logging.info(f"🔍 BACKEND DEBUG: Using generated email for backend: {strava_email}")

    # Check if user exists
    logging.info(f"🔍 BACKEND DEBUG: Looking for existing user with email: {strava_email}")
    
    user = db.query(User).filter(User.email == strava_email).first()
    is_new_user = user is None
    logging.info(f"🔍 BACKEND DEBUG: User exists: {not is_new_user}, is_new_user: {is_new_user}")
    
    if not user:
        # Create new user
        logging.info(f"🔍 BACKEND DEBUG: Creating new user")
        user = User(
            email=strava_email,  # Use generated email for database
            name=f"{athlete.get('firstname')} {athlete.get('lastname')}",
            gender=athlete.get("sex"),
            strava_user_id=str(athlete.get("id")),
            strava_oauth_token=token_data.get("access_token"),
            strava_refresh_token=token_data.get("refresh_token"),
            strava_token_expires_at=token_data.get("expires_at")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logging.info(f"🔍 BACKEND DEBUG: Created new user with ID: {user.user_id}")
    else:
        # Update existing user
        logging.info(f"🔍 BACKEND DEBUG: Updating existing user ID: {user.user_id}")
        user.strava_user_id = str(athlete.get("id"))
        user.strava_oauth_token = token_data.get("access_token")
        user.strava_refresh_token = token_data.get("refresh_token")
        user.strava_token_expires_at = token_data.get("expires_at")
        db.commit()

    # For new users, DON'T trigger immediate activity import
    # Let the frontend handle the onboarding flow first
    if is_new_user:
        logging.info(f"🔍 BACKEND DEBUG: New user {user.user_id} - onboarding required")
    else:
        logging.info(f"🔍 BACKEND DEBUG: Existing user {user.user_id} - no onboarding needed")

    # Redirect to frontend with user info for proper onboarding flow
    # Don't pass email - let user enter their real email in onboarding form
    frontend_url = f"http://localhost:5173/?user_id={user.user_id}&name={athlete.get('firstname')} {athlete.get('lastname')}&gender={athlete.get('sex')}"
    logging.info(f"🔍 BACKEND DEBUG: Redirecting to: {frontend_url}")
    return RedirectResponse(frontend_url)
