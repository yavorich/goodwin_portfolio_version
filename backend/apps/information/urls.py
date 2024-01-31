from django.urls import path

from . import views


urlpatterns = [
    path("operations/", views.OperationAPIView.as_view(), name="operation-list"),
    path("programs/", views.ProgramAPIView.as_view(), name="program-list"),
    path("wallet/", views.WalletAPIView.as_view(), name="wallet-detail"),
]
