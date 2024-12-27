from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from . import views
from .models import User, UserProfile, SmsVerification
from django.contrib.auth.password_validation import validate_password
import requests
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'password', 'confirm_password', 'number_card', 'role', 'birth_day', 'gender',
                  'region', 'populated_area']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.get('confirm_password')
        if password != confirm_password:
            raise ValidationError("Parollar bir-biriga mos emas!")
        return attrs

    def to_representation(self, instance):
        data = super(UserSerializer, self).to_representation(instance)
        data['password'] = instance.password  # Parolni qo'shish
        return data


###################### sms kodni tekshirish ########################

class VerifyCodeSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=13)
    code = serializers.CharField(max_length=4)

    def validate(self, attrs):
        phone = attrs['phone']
        code = attrs['code']

        try:
            verification = SmsVerification.objects.get(user__phone=phone)
        except SmsVerification.DoesNotExist:
            raise serializers.ValidationError("SMS kodi topilmadi.")

        if not verification.is_code_valid(code):
            raise serializers.ValidationError("SMS kodi noto'g'ri yoki muddati o'tgan.")

        return attrs

     ####################### EDIT PROFILE ###################

class ChangeUserInformation(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'confirm_password']

    def validate(self, data):
        password = data.get('password', None)
        confirm_password = data.get('confirm_password', None)
        if password !=confirm_password:
            raise ValidationError(
                {
                    "message": "Parolingiz va tasdiqlash parolingiz bir-biriga teng emas"
                }
            )
        if password:
            validate_password(password)
            validate_password(confirm_password)

        return data

    def validate_username(self, username):
        if len(username) < 5 or len(username) > 30:
            raise ValidationError(
                {
                    "message": "Foydalanuvchi nomi 5 dan 30 gacha belgidan iborat bo'lishi kerak"
                }
            )
        if username.isdigit():
            raise ValidationError(
                {
                    "message": "Ushbu foydalanuvchi nomi butunlay raqamli"
                }
            )
        return username

    def update(self, instance, validated_data):

        instance.password = validated_data.get('password', instance.password)
        instance.username = validated_data.get('username', instance.username)
        if validated_data.get('password'):
            instance.set_password(validated_data.get('password'))

        instance.save()
        return instance


    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['phone', 'password', 'confirm_password']



##################### reset-password ##########################

class PhoneSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=13)

class CodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=4)

class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=128)
    confirm_password = serializers.CharField(max_length=128)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
