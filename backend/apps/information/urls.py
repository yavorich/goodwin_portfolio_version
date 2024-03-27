from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views
from .views.operations import OperationReplenishmentConfirmView

router = DefaultRouter()
router.register("programs", views.ProgramViewSet, basename="programs")
router.register(
    "programs/(?P<program_pk>[^/.]+)/replenishments",
    views.ProgramReplenishmentViewSet,
    basename="program-replenishments",
)
router.register("wallet/frozen", views.FrozenItemViewSet, basename="wallet-frozen")
router.register("wallet", views.WalletViewSet, basename="wallet")


urlpatterns = [
    path("operations/", views.OperationAPIView.as_view(), name="operation-list"),
    path(
        "operations/<int:pk>/confirm/",
        views.OperationConfirmAPIView.as_view(),
        name="operation-confirm",
    ),
    path(
        "operations/replenishment/<int:pk>/",
        OperationReplenishmentConfirmView.as_view(),
        name="operation-replenishment",
    ),
    path("wallet/", views.WalletAPIView.as_view(), name="wallet-detail"),
    path(
        "wallet/transfer/to/",
        views.WalletTransferAPIView.as_view(),
        name="wallet-transfer-user",
    ),
] + router.urls
