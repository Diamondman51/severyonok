from django.urls import path
from .views import CategoryListCreateAPIView, ProductListCreateAPIView, CardListView, CardCreateView, \
    CommentListCreateView, CommentRetrieveUpdateDestroyView, OrderCreateView, DiscountCreateView, MyOrderListAPIView

urlpatterns = [
    path('categories/', CategoryListCreateAPIView.as_view(), name='category-list-create'),
    path('products/', ProductListCreateAPIView.as_view(), name='product-list-create'),
    path('cards/', CardCreateView.as_view(), name='card-create'),
    path('my-cards/', CardListView.as_view(), name='my-cards'),
    path('comments/', CommentListCreateView.as_view(), name='comment-list'),
    path('comments/<int:pk>/', CommentRetrieveUpdateDestroyView.as_view(), name='comment-detail'),
    path('orders/', OrderCreateView.as_view(), name='order-create'),
    path('discounts/', DiscountCreateView.as_view(), name='discount-create'),
    path('my-order-list/', MyOrderListAPIView.as_view()),
]
