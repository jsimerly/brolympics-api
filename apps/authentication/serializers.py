from rest_framework import serializers
from authentication.models import FirebaseUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = FirebaseUser
        fields = ['uid', 'email', 'phone', 'first_name', 'last_name', 'display_name', 'img', 'is_available', 'date_joined']