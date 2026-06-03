from ninja import Router
from ninja_jwt.authentication import JWTAuth

from .schemas import UserOut

router = Router()


@router.get("/me/", response=UserOut, auth=JWTAuth())
def me(request):
    return request.auth
