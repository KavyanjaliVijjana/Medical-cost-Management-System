from pydantic import BaseModel


class DemoLoginRequest(BaseModel):
    email: str = "demo@medicalcost.local"


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: str
    is_demo: bool

    model_config = {"from_attributes": True}
