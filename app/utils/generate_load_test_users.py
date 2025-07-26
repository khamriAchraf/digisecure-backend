import random
import sys
import uuid

from sqlalchemy.orm import sessionmaker

from app.core.security import get_password_hash
from app.db.models import Role, User
from app.db.session import engine

Session = sessionmaker(bind=engine)
session = Session()

NUM_USERS = 5000
BATCH_SIZE = 500

# Fetch all roles
roles = session.query(Role).all()
if not roles:
    print("No roles found in the database. Please seed roles first.", flush=True)
    sys.exit(1)


def print_progress_bar(iteration, total, length=40):
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = "█" * filled_length + "-" * (length - filled_length)
    print(f"\rProgress: |{bar}| {percent}% ({iteration}/{total})", end="", flush=True)
    if iteration == total:
        print(flush=True)


users_created = 0
for batch_start in range(0, NUM_USERS, BATCH_SIZE):
    users_to_add = []
    for _ in range(BATCH_SIZE):
        user_uuid = uuid.uuid4().hex
        username = f"user_{user_uuid}"
        email = f"{username}@example.com"
        password = uuid.uuid4().hex  # random password
        full_name = username
        hashed_password = get_password_hash(password)
        status = "active"
        role = random.choice(roles)
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            status=status,
            role_id=role.id,
        )
        users_to_add.append(user)
    session.bulk_save_objects(users_to_add)
    session.commit()
    users_created += BATCH_SIZE
    print_progress_bar(
        users_created if users_created < NUM_USERS else NUM_USERS, NUM_USERS
    )

session.close()
print(f"Inserted {NUM_USERS} users for load testing.", flush=True)
