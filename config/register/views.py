from django.contrib.auth.hashers import check_password
from rest_framework.exceptions import ValidationError
from rest_framework.generics import UpdateAPIView, CreateAPIView, GenericAPIView
from rest_framework.views import APIView
from .models import User, UserProfile, SmsVerification
from .serializers import UserSerializer, ChangeUserInformation, LogoutSerializer, \
    UserProfileSerializer, ResetPasswordSerializer, CodeSerializer, PhoneSerializer, VerifyCodeSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import generics, permissions, status, views
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer
from rest_framework.response import Response
import requests
from rest_framework import views, status

User = get_user_model()

class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        serializer.save(role=self.request.data.get('role', 'user'))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        if user.phone:
            code = user.create_verify_code()
            self.send_sms(user.phone, code)  # SMS yuborish

        return Response({
            "message": "Foydalanuvchi muvaffaqiyatli ro'yxatdan o'tdi.",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone": user.phone,
                "number_card": user.number_card,
                "birth_day": user.birth_day,
                "gender": user.gender,
                "region": user.region,
                "populated_area": user.populated_area,
                "password": request.data.get('password'),
                "confirm_password": request.data.get('confirm_password')
            },
            "sms_code": code,
            "access": str(refresh.access_token),  # Access token
            "refresh": str(refresh)  # Refresh token
        }, status=status.HTTP_201_CREATED)


    def send_sms(self, phone, code):
        # Eskiz SMS API autentifikatsiya
        auth_url = "http://notify.eskiz.uz/api/auth/login"
        auth_payload = {
            'email': 'imronhoja336@mail.ru',
            'password': 'ombeUIUC8szPawGi3TXgCjDXDD0uAIx2AmwLlX9M'
        }

        auth_response = requests.post(auth_url, data=auth_payload)
        auth_data = auth_response.json()

        if 'data' in auth_data:
            token = auth_data['data']['token']
            sms_url = "http://notify.eskiz.uz/api/message/sms/send"
            sms_payload = {
                'mobile_phone': str(phone),
                'message': f"Envoy ilovasiga ro‘yxatdan o‘tish uchun tasdiqlash kodi: {code}",
                'from': '4546',
                'callback_url': 'http://0000.uz/test.php'
            }

            sms_headers = {
                'Authorization': f'Bearer {token}'
            }

            sms_response = requests.post(sms_url, headers=sms_headers, data=sms_payload)
            if sms_response.status_code == 200:
                print("SMS muvaffaqiyatli jo'natildi.")
            else:
                print("SMS jo'natishda xato:", sms_response.text)
        else:
            print("Autentifikatsiya xatosi:", auth_data)



class LoginAPIView(APIView):
    def post(self, request):
        phone = request.data.get('phone')
        password = request.data.get('password')

        if not phone or not password:
            return Response({'error': 'Telefon raqami yoki parol ko\'rsatilmagan.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(phone=phone).first()

        if not user:
            return Response({'message': 'Bunday foydalanuvchi topilmadi!'}, status=status.HTTP_404_NOT_FOUND)

        if check_password(password, user.password):
            return Response({
                'token': user.token()['access'],
                'role': user.role,
                "message": 'ok'
            }, status=status.HTTP_200_OK)

        return Response({'error': 'Parolingiz xato'}, status=status.HTTP_400_BAD_REQUEST)

####################   bu login da agar user bazada bulsa  tru yoki false qaytaradi #####################

class CheckUserView(views.APIView):
    def post(self, request):
        phone = request.data.get('phone')

        if not phone:
            return Response({"error": "Telefon raqami kerak."}, status=status.HTTP_400_BAD_REQUEST)

        user_exists = User.objects.filter(phone=phone).exists()

        return Response({"exists": user_exists}, status=status.HTTP_200_OK)


############################################################################################

class VerifyCodeView(generics.GenericAPIView):
    serializer_class = VerifyCodeSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone']
        code = serializer.validated_data['code']

        try:
            user = User.objects.get(phone=phone)
            if user.code == code:
                return Response({"message": "Kod tasdiqlandi. Parolni tiklashni davom eting."},
                                status=status.HTTP_200_OK)
            else:
                return Response({"error": "Yaroqsiz kod."}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "Foydalanuvchi topilmadi."}, status=status.HTTP_404_NOT_FOUND)


class LogOutAPIView(APIView):
    serializer_class = LogoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        try:
            refresh_token = self.request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'success': True, 'message': "Muvaffaqiyatli hisobingizdan chiqdingiz!"}, status=205)
        except TokenError:
            return Response(status=400)


class UserDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()

    def delete(self, request, *args, **kwargs):
        user = self.request.user
        user.delete()
        return Response({'success': True, 'message': "Muvaffaqiyatli hisobdan o'chirildingiz!"},status=status.HTTP_204_NO_CONTENT)


class UserUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def put(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class VerifyCodeAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        code = self.request.data.get('code')
        self.check_verify(user, code)

        user.is_confirmed = True  # Kod to'g'ri bo'lsa tasdiqlash
        user.save()

        return Response(
            data={
                "success": True,
                "access": user.token()['access'],
                "refresh": user.token()['refresh']
            }
        )

    @staticmethod
    def check_verify(user, code):
        # Code va telefon raqami orqali tekshirish
        verifies = User.objects.filter(code=code, phone=user.phone, is_confirmed=False)
        print("Verifies queryset: ", verifies)
        print("Phone", user.phone)
        print("Code", user.code)

        if not verifies.exists():
            data = {
                "message": "Tasdiqlash kodingiz xato yoki eskirgan"
            }
            raise ValidationError(data)
        else:
            # Kod to'g'ri bo'lsa, tasdiqlashni yangilaymiz
            user.save()
        if user.is_confirmed == False:
            verifies.update(is_confirmed=True)
            return  verifies
        return True


####################  EDIT PROFILE #################

class ChangeUserInformationView(UpdateAPIView):
    serializer_class = ChangeUserInformation
    http_method_names = ['patch', 'put']

    def get_object(self):
        if not self.request.user.is_authenticated:
            raise AuthenticationFailed('Foydalanuvchi autentifikatsiya qilinmagan')
        return self.request.user

    def update(self, request, *args, **kwargs):
        super(ChangeUserInformationView, self).update(request, *args, **kwargs)
        data = {
            'success': True,
            "message": "Foydalanuvchi muvaffaqiyatli yangilandi",
        }
        return Response(data, status=200)

    def partial_update(self, request, *args, **kwargs):
        super(ChangeUserInformationView, self).partial_update(request, *args, **kwargs)
        data = {
            'success': True,
            "message": "Foydalanuvchi muvaffaqiyatli yangilandi",
            'auth_status': self.request.user.auth_status,
        }
        return Response(data, status=200)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


#####################  reset-password ########################

class SendCodeView(generics.GenericAPIView):
    serializer_class = PhoneSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']

        try:
            user = User.objects.get(phone=phone)
            request.session['phone'] = phone  # Telefon raqamini sessiyada saqlash
            code = user.create_verify_code()  # Generate and save the code

            # Send the verification code via SMS
            self.send_sms(phone, code)

            return Response({"message": "Tasdiqlash kodi yuborildi.", "access": user.token()['access']}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "Foydalanuvchi topilmadi."}, status=status.HTTP_404_NOT_FOUND)

    def send_sms(self, phone, code):
        # Eskiz SMS API autentifikatsiya
        auth_url = "http://notify.eskiz.uz/api/auth/login"
        auth_payload = {
            'email': 'imronhoja336@mail.ru',
            'password': 'ombeUIUC8szPawGi3TXgCjDXDD0uAIx2AmwLlX9M'
        }

        auth_response = requests.post(auth_url, data=auth_payload)
        auth_data = auth_response.json()

        if 'data' in auth_data:
            token = auth_data['data']['token']
            sms_url = "http://notify.eskiz.uz/api/message/sms/send"
            sms_payload = {
                'mobile_phone': str(phone),
                'message': f"Envoy ilovasiga ro‘yxatdan o‘tish uchun tasdiqlash kodi: {code}",
                'from': '4546',
                'callback_url': 'http://0000.uz/test.php'
            }

            sms_headers = {
                'Authorization': f'Bearer {token}'
            }

            sms_response = requests.post(sms_url, headers=sms_headers, data=sms_payload)
            if sms_response.status_code == 200:
                print("SMS muvaffaqiyatli jo'natildi.")
            else:
                print("SMS jo'natishda xato:", sms_response.text)
        else:
            print("Autentifikatsiya xatosi:", auth_data)

# class VerifyCodeView(generics.GenericAPIView):
#     serializer_class = CodeSerializer
#
#     def post(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         code = serializer.validated_data['code']
#
#         phone = request.session.get('phone')
#         if not phone:
#             return Response({"error": "Telefon raqami ko'rsatilmagan."}, status=status.HTTP_400_BAD_REQUEST)
#
#         # Access tokenni olish
#         token = request.META.get('HTTP_AUTHORIZATION')
#         if not token or not token.startswith('Bearer '):
#             return Response({"error": "Token taqdim etilmagan."}, status=status.HTTP_401_UNAUTHORIZED)
#
#         try:
#             user = User.objects.get(phone=phone)
#             if user.code == code:
#                 return Response({"message": "Kod tasdiqlandi. Parolni tiklashni davom eting."}, status=status.HTTP_200_OK)
#             else:
#                 return Response({"error": "Yaroqsiz kod."}, status=status.HTTP_400_BAD_REQUEST)
#         except User.DoesNotExist:
#             return Response({"error": "Foydalanuvchi topilmadi."}, status=status.HTTP_404_NOT_FOUND)
#

class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = request.session.get('phone')
        if not phone:
            return Response({"error": "Telefon raqami ko'rsatilmagan."}, status=status.HTTP_400_BAD_REQUEST)

        # Access tokenni olish
        token = request.META.get('HTTP_AUTHORIZATION')
        if not token or not token.startswith('Bearer '):
            return Response({"error": "Token taqdim etilmagan."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = User.objects.get(phone=phone)
            user.set_password(serializer.validated_data['new_password'])  # Yangi parolni o'rnatish
            user.save()
            return Response({"message": "Parol muvaffaqiyatli tiklandi."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "Foydalanuvchi topilmadi."}, status=status.HTTP_404_NOT_FOUND)















