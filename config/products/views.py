import requests
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from .models import Category, Product, Comment, Order, Discount
from .serializers import CategorySerializer, ProductSerializer, CardSerializer, CommentSerializer, OrderSerializer, \
    DiscountSerializer, MyOderListSerializers
from .models import Card
from rest_framework.permissions import IsAuthenticated


class CategoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    



class ProductListCreateAPIView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    # def perform_create(self, serializer):
    #     user = self.request.user
    #     if user.is_authenticated:
    #         serializer.save(User=user)
    #     else:
    #         raise ValidationError("User must be authenticated to create a product.")
    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            old_status = instance.status
            serializer.save()

            if serializer.validated_data['status'] == 'not_received' and not instance.admin_notified:
                self.notify_admin(instance)
                instance.admin_notified = True
                instance.save()

            self.send_status_message(serializer.validated_data['status'], instance.customer.phone_number)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def send_status_message(self, status, phone_number):
        messages = {
            'in_progress': "Mahsulot yigilyapti.",
            'dispatched': "Mahsulot dostavka junatildi.",
            'received': "Xaridorga berilgan",
            'not_received': "Mahsulot qabul qilinmadi.",
        }

        message = messages.get(status, "Holat aniqlanmadi.")

        self.send_sms(phone_number, message)

    def send_sms(self, phone_number, message):
        payload = {
            'to': phone_number,
            'message': message
        }

        response = requests.post('http://notify.eskiz.uz/api/message/sms/send', json=payload)

        if response.status_code == 200:
            print(f"SMS muvaffaqiyatli yuborildi: {message} - {phone_number}")
        else:
            print(f"SMS yuborishda xato: {response.text}")

    def notify_admin(self, product):
        admin_phone_number = '+998950038031'
        subject = "Mahsulot qabul qilinmadi"
        message = f"{product.name} mahsuloti qabul qilinmadi. Iltimos, nazorat qiling."

        self.send_sms(admin_phone_number, message)


class CardCreateView(generics.CreateAPIView):
    queryset = Card.objects.all()
    serializer_class = CardSerializer


class CardListView(generics.ListAPIView):
    serializer_class = CardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Card.objects.filter(user=self.request.user)


class CommentListCreateView(generics.ListCreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CommentRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(user=self.request.user)


class OrderCreateView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    # permission_classes = [IsAuthenticated]


class DiscountCreateView(generics.CreateAPIView):
    queryset = Discount.objects.all()
    serializer_class = DiscountSerializer
    permission_classes = [IsAuthenticated]


class MyOrderListAPIView(ListAPIView):
    queryset = Order.objects.all()
    serializer_class = MyOderListSerializers

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Order.objects.filter(user=user)
        else:
            return Order.objects.none()


