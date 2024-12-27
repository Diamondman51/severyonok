from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Category, Product, Card, Comment, Order, Discount
from ..register.serializers import UserSerializer


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ['id', 'product', 'percentage', 'start_date', 'end_date']


class ProductSerializer(serializers.ModelSerializer):
    discounts = DiscountSerializer(many=True, read_only=True) ######## aksiya ##########

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'brand', 'title', 'created_at', 'price', 'image', 'card_number', 'category_id', 'discounts', 'status']

    # def validate_image(self, value):
    #     if not value.name.endswith(('jpg', 'jpeg', 'png')):
    #         raise ValidationError("Image must be in JPG, JPEG, or PNG format.")
    #     return     value

class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ['id', 'card_number']

    def validate_card_number(self, value):
        if len(value) < 16:
            raise serializers.ValidationError("Kartaning raqami 16 ta raqamdan kam bo'lmasligi kerak.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'product', 'user', 'created_at', 'comment']
        read_only_fields = ['id', 'created_at']


class OrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = Order
        fields = ['id', 'user', 'product', 'address', 'amount', 'created_at']
        # read_only_fields = ['id', 'created_at']


class MyOderListSerializers(serializers.ModelSerializer):
    user = UserSerializer()
    product = ProductSerializer()
    class Meta:
        model = Order
        fields = ('id', 'user', 'product', 'address', 'amount', 'created_at')






