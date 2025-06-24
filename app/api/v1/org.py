import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models.org import Org
from app.db.session import get_db
from app.schemas.org import OrgSignUp
from app.services import org_service

router = APIRouter(prefix="/org", tags=["org"])


@router.post("/signup")
def org_signup(org: OrgSignUp, db: Session = Depends(get_db)):
    # 1. Check if org/subdomain exists
    if (
        db.query(Org)
        .filter((Org.name == org.name) | (Org.subdomain == org.subdomain))
        .first()
    ):
        raise HTTPException(
            status_code=400, detail="Org name or subdomain already exists"
        )
    # 2. Generate schema, user, password
    schema_name = f"org_{secrets.token_hex(4)}"
    db_user = f"user_{secrets.token_hex(4)}"
    db_password = secrets.token_urlsafe(16)
    # 3. Create schema, user, tables
    org_service.create_org_schema_and_user(
        db, schema_name, db_user, db_password, org.admin_email, org.admin_password
    )
    # 4. Store org metadata
    new_org = Org(
        name=org.name,
        schema_name=schema_name,
        db_user=db_user,
        db_password=db_password,
        admin_email=org.admin_email,
        subdomain=org.subdomain,
    )
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    return {"message": "Org created", "org_id": new_org.id}
