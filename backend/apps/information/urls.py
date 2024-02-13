from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("programs", views.ProgramViewSet, basename="programs")
router.register(
    "programs/(?P<program_pk>[^/.]+)/replenishments",
    views.ProgramReplenishmentViewSet,
    basename="program-replenishments",
)
router.register("wallet/frozen", views.FrozenItemViewSet, basename="wallet-frozen")


urlpatterns = [
    path("operations/", views.OperationAPIView.as_view(), name="operation-list"),
    path(
        "operations/<int:pk>/confirm/",
        views.OperationConfirmAPIView.as_view(),
        name="operation-confirm",
    ),
    path("wallet/", views.WalletAPIView.as_view(), name="wallet-detail"),
] + router.urls
