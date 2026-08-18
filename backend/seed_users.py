"""
One-off script to create user accounts for the team.

Usage:
    python3 seed_users.py

Edit the USERS list below with real teammate emails before running.
Safe to re-run — skips any email that already exists.
"""

from database import SessionLocal, engine, Base
from db_models import User
from auth import hash_password

# Create the users table if it doesn't exist yet
Base.metadata.create_all(bind=engine)

USERS = [
    {"email": "aditya@sih-team.local", "password": "TestPass123", "full_name": "Aditya"},
    # add the other 5 teammates here
]

db = SessionLocal()

for u in USERS:
    existing = db.query(User).filter(User.email == u["email"]).first()
    if existing:
        print(f"Skipping {u['email']} (already exists)")
        continue

    user = User(
        email=u["email"],
        hashed_password=hash_password(u["password"]),
        full_name=u.get("full_name"),
    )
    db.add(user)
    print(f"Created {u['email']}")

db.commit()
db.close()