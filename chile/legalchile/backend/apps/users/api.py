from ninja import Router
from ninja_jwt.authentication import HttpBearer

from .models import User
from .schemas import UserOut

router = Router()


@router.get("/me/", response=UserOut, auth=HttpBearer())
def me(request):
    return request.auth
