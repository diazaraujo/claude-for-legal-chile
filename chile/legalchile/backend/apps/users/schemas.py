from ninja import Schema
from datetime import datetime


class UserOut(Schema):
    id: int
    email: str
    first_name: str
    last_name: str
    date_joined: datetime
