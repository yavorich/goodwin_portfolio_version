from django.urls import path

from apps.faq.views import ListAnswerView

urlpatterns = [
    path("faq/", ListAnswerView.as_view(), name="faq")
    # path("faq/<int:id>/", ListAnswerView.as_view(), name="")
]
