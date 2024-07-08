from django.urls import path
from apps.gdw_site.views import (
    SiteProgramsAPIView,
    CalculatorAPIView,
    FundStatsAPIView,
    TopupPeriodListAPIView,
    SiteAnswerAPIView,
    SiteContactsAPIView,
    SiteNewsViewSet,
    SocialContactsViewSet,
    RedirectLinksAPIView,
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("news", SiteNewsViewSet, basename="site-news")
router.register("social", SocialContactsViewSet, basename="social-contacts")

urlpatterns = [
    path("programs/", SiteProgramsAPIView.as_view(), name="site-programs"),
    path("calculator/", CalculatorAPIView.as_view(), name="calculator"),
    path("graph/", FundStatsAPIView.as_view(), name="fund-graph"),
    path("topup-periods/", TopupPeriodListAPIView.as_view(), name="topup-periods"),
    path("faq/", SiteAnswerAPIView.as_view(), name="site-faq"),
    path("contacts/", SiteContactsAPIView.as_view(), name="site-contacts"),
    path("auth-links/", RedirectLinksAPIView.as_view(), name="redirect-links"),
] + router.urls
