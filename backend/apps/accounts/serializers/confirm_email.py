from rest_framework.serializers import Serializer, CharField


class UserEmailConfirmSerializer(Serializer):
    confirmation_code = CharField(min_length=6, max_length=6)
