from django.urls import path
from . import views

app_name = 'reservation'

urlpatterns = [
    path('', views.home, name='home'),
    path('restaurants/', views.restaurant_list, name='restaurant_list'),
    path('restaurant/<int:pk>/', views.restaurant_detail, name='restaurant_detail'),
    path('reserve/<int:restaurant_id>/', views.make_reservation, name='make_reservation'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
]
