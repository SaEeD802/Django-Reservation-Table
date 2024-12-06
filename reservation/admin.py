from django.contrib import admin
from .models import Restaurant, Table, Reservation

# Register your models here.

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'capacity']
    search_fields = ['name', 'address']

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['restaurant', 'number', 'capacity']
    list_filter = ['restaurant']

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['user', 'table', 'date', 'time', 'status']
    list_filter = ['status', 'date']
    search_fields = ['user__username', 'table__restaurant__name']
