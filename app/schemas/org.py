from pydantic import BaseModel


class OrgSignUp(BaseModel):
    name: str
    admin_email: str
    admin_password: str
    subdomain: str
