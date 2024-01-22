from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from accounts.models import User
from accounts.serializers import ProfileRetrieveSerializer, ProfileUpdateSerializer


class ProfileAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = {
        "GET": ProfileRetrieveSerializer,
        "PATCH": ProfileUpdateSerializer,
    }
    queryset = User.objects.all()

    def get_serializer_class(self):
        return self.serializer_class[self.request.method]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context

    def get_object(self):
        return get_object_or_404(User, pk=self.request.user.pk)
