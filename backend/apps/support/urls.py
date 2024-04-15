from django.urls import path

from apps.support.views import ListSupportView

urlpatterns = [
    path("contacts/", ListSupportView.as_view(), name="contact-list"),
]
