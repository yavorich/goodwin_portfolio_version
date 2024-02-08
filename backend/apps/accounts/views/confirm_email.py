from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated

from apps.accounts.serializers import UserEmailConfirmSerializer


class EmailConfirmAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserEmailConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.data["confirmation_code"]
        user = request.user

        if code != request.user.temp.email_verify_code:
            raise ValidationError("Verification code is incorrect")

        user.temp.email_verify_code = None
        user.temp.save()

        user.email_is_confirmed = True
        user.save()

        return Response(
            data={"agreement_applied": user.agreement_applied},
            status=status.HTTP_200_OK,
        )
