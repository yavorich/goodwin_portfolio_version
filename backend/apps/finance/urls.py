from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views
from .views.operations import (
    OperationReplenishmentConfirmView,
    OperationReplenishmentStatusView,
    OperationTypeListView,
)

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
    path("operations/", views.OperationHistoryAPIView.as_view(), name="operation-list"),
    path(
        "operations/<int:pk>/confirm/<str:destination>/",
        views.OperationConfirmAPIView.as_view(),
        name="operation-confirm",
    ),
    path(
        "operations/replenishment/<str:uuid>/",
        OperationReplenishmentConfirmView.as_view(),
        name="operation-replenishment",
    ),
    path(
        "operations/replenishment/<int:pk>/status/",
        OperationReplenishmentStatusView.as_view(),
        name="operation-replenishment-status",
    ),
    path("operations/types/", OperationTypeListView.as_view(), name="operation-types"),
    path("wallet/", views.WalletAPIView.as_view(), name="wallet-detail"),
    path(
        "wallet/transfer/to/",
        views.WalletTransferAPIView.as_view(),
        name="wallet-transfer-user",
    ),
    path(
        "wallet/settings/",
        views.WalletSettingsAPIView.as_view(),
        name="wallet-settings",
    ),
] + router.urls
