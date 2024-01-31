from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from apps.faq.models import Answer
from apps.faq.serializers import AnswerSerializer


class ListAnswerView(ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Answer.objects.order_by("title")
    serializer_class = AnswerSerializer
