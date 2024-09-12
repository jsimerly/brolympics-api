from firebase_admin import auth, storage
from rest_framework import authentication, exceptions
from django.contrib.auth import get_user_model
from django.db import IntegrityError


User = get_user_model()

from django.db import IntegrityError

class FirebaseAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if not auth_header:
            return None

        id_token = auth_header.split(" ").pop()
        try:
            decoded_token = auth.verify_id_token(id_token, check_revoked=True, clock_skew_seconds=60)
            uid = decoded_token["uid"]
        except Exception as e:
            print(f"Token verification failed: {str(e)}")
            raise exceptions.AuthenticationFailed("Invalid Token")
        
        try:
            user, created = User.objects.get_or_create(uid=uid)
            if created:
                if 'name' in decoded_token:
                    user.display_name = decoded_token['name']
                if 'email' in decoded_token:
                    user.email = decoded_token['email']
                if 'phone_number' in decoded_token:
                    user.phone_number = decoded_token['phone_number']
                if 'picture' in decoded_token:
                    user.img_url = decoded_token['picture']
                if 'firebase' in decoded_token and 'sign_in_provider' in decoded_token['firebase']:
                    user.provider = decoded_token['firebase']['sign_in_provider']
                user.save()
        
        except IntegrityError:
            raise exceptions.AuthenticationFailed("User with this UID already exists")

        return user, id_token


        