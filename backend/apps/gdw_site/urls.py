from django.urls import path
from apps.gdw_site.views import SiteProgramsAPIView, CalculatorAPIView

urlpatterns = [
    path("programs/", SiteProgramsAPIView.as_view(), name="site-programs"),
    path("calculator/", CalculatorAPIView.as_view(), name="calculator"),
]
