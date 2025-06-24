from fastapi import Depends
from app.db.session import get_db


def get_current_user():
    return None