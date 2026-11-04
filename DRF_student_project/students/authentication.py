
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from .models import ArchivedUser


class ActiveUserJWTAuthentication(JWTAuthentication):

    def get_user(self, validated_token):
        user = super().get_user(validated_token)

        if not user.is_active:
            raise AuthenticationFailed(
                "This account is inactive."
            )

        if ArchivedUser.objects.filter(user=user).exists():
            raise AuthenticationFailed(
                "This account has been archived."
            )

        return user
