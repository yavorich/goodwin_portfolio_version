from django.urls import path
from apps.gdw_site.views import (
    SiteProgramsAPIView,
    CalculatorAPIView,
    FundStatsAPIView,
    TopupPeriodListAPIView,
    SiteAnswerAPIView,
)

urlpatterns = [
    path("programs/", SiteProgramsAPIView.as_view(), name="site-programs"),
    path("calculator/", CalculatorAPIView.as_view(), name="calculator"),
    path("graph/", FundStatsAPIView.as_view(), name="fund-graph"),
    path("topup-periods/", TopupPeriodListAPIView.as_view(), name="topup-periods"),
    path("faq/", SiteAnswerAPIView.as_view(), name="faq"),
]
