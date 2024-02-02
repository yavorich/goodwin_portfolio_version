from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("programs", views.UserProgramViewSet, basename="user-programs")


urlpatterns = [
    path("operations/", views.OperationAPIView.as_view(), name="operation-list"),
    path(
        "operations/<int:pk>/confirm/",
        views.OperationConfirmAPIView.as_view(),
        name="operation-confirm",
    ),
    path("programs/", views.ProgramAPIView.as_view(), name="program-list"),
    path("wallet/", views.WalletAPIView.as_view(), name="wallet-detail"),
] + router.urls
