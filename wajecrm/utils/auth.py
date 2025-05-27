from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from ..models import user  # Import your custom user model

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        """
        Returns the user associated with the given validated token.
        Uses the custom `user` model instead of Django's default User.
        """
        try:
            user_id = validated_token.get("user_id")
            merch_id = validated_token.get("merchID")
            if user_id is None:
                raise InvalidToken("Token contained no recognizable user identification")

            try:
                user_instance = user.objects.get(id=user_id)
                # Attach merchID from token as a separate attribute
                if merch_id is not None:
                    setattr(user_instance, 'merchID_from_token', merch_id)

                return user_instance
            except user.DoesNotExist:
                raise InvalidToken("User not found")

        except Exception as e:
            raise InvalidToken(f"User retrieval failed: {str(e)}")
def get_authenticated_user_from_request(request):
    jwt_authenticator = CustomJWTAuthentication()
    auth_header = request.headers.get('Authorization', '')

    try:
        parts = auth_header.strip().split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None, 'Invalid token format'
        
        token = parts[1].strip()
        validated_token = jwt_authenticator.get_validated_token(token)
        user_instance = jwt_authenticator.get_user(validated_token)
        return user_instance, None
    except Exception as e:
        return None, f'Invalid token: {str(e)}'