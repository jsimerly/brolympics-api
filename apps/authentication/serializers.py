from rest_framework import serializers
from authentication.models import FirebaseUser

class UserSerializer(serializers.ModelSerializer):
    account_complete = serializers.SerializerMethodField()
    class Meta:
        model = FirebaseUser
        fields = ['uid', 'email', 'phone', 'first_name', 'last_name', 'display_name', 'img', 'is_available', 'date_joined', 'account_complete']

    def get_account_complete(self, obj):
        return bool(obj.display_name and obj.first_name and obj.last_name)