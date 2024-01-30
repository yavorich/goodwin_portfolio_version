from rest_framework.generics import RetrieveUpdateAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.accounts.models import User
from apps.accounts.serializers import (
    ProfileRetrieveSerializer,
    ProfileUpdateSerializer,
    PasswordChangeSerializer,
)


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


class PasswordChangeAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(
            data=request.data, context={"user": request.user}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.data["new_password"])
        request.user.save()
        return Response({"success": "Пароль успешно обновлен"})
