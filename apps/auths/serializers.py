from rest_framework import serializers
from apps.auths.models import User

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "first_name", 'last_name', 'password')

    def create(self, validated_data: dict) -> User:
        user = User.objects.create_user(
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=validated_data["password"],
        )
        return user