from pydantic import BaseModel
class RegisterReq(BaseModel):
    username: str
    email: str
    password: str
    full_name: str | None = None
    hospital: str | None = None
    department: str | None = None


class LoginReq(BaseModel):
    username: str
    password: str



