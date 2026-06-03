from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from ninja_jwt.authentication import HttpBearer
from ninja_jwt.controller import NinjaJWTDefaultController
from ninja_extra import NinjaExtraAPI

api = NinjaExtraAPI(
    title="API",
    version="0.1.0",
    urls_namespace="api",
)
api.register_controllers(NinjaJWTDefaultController)

# Import and register routers
from apps.core.api import router as core_router
from apps.users.api import router as users_router
from apps.corpus.api import router as corpus_router

api.add_router("/", core_router)
api.add_router("/auth/", users_router)
api.add_router("/corpus/", corpus_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
