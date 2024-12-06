from django.db import models
from django.contrib.auth.models import User

class Restaurant(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام رستوران")
    description = models.TextField(verbose_name="توضیحات")
    address = models.TextField(verbose_name="آدرس")
    phone = models.CharField(max_length=20, verbose_name="شماره تماس")
    image = models.ImageField(upload_to='restaurants/', verbose_name="تصویر")
    capacity = models.PositiveIntegerField(verbose_name="ظرفیت")
    opening_time = models.TimeField(verbose_name="ساعت شروع کار")
    closing_time = models.TimeField(verbose_name="ساعت پایان کار")
    
    class Meta:
        verbose_name = "رستوران"
        verbose_name_plural = "رستوران‌ها"
    
    def __str__(self):
        return self.name
    
    def get_remaining_capacity(self, date, time):
        # محاسبه مجموع تعداد مهمان‌های رزرو شده برای این تاریخ و ساعت
        reserved_guests = Reservation.objects.filter(
            table__restaurant=self,
            date=date,
            time=time,
            status='confirmed'
        ).aggregate(total_guests=models.Sum('guests'))['total_guests'] or 0
        
        # محاسبه ظرفیت باقی‌مانده
        return self.capacity - reserved_guests

class Table(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, verbose_name="رستوران")
    number = models.PositiveIntegerField(verbose_name="شماره میز")
    capacity = models.PositiveIntegerField(verbose_name="ظرفیت")
    
    class Meta:
        verbose_name = "میز"
        verbose_name_plural = "میزها"
    
    def __str__(self):
        return f"میز {self.number} - {self.restaurant.name}"

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار تایید'),
        ('confirmed', 'تایید شده'),
        ('cancelled', 'لغو شده'),
    ]
    
    DURATION_CHOICES = [
        (60, '۱ ساعت'),
        (90, '۱.۵ ساعت'),
        (120, '۲ ساعت'),
        (150, '۲.۵ ساعت'),
        (180, '۳ ساعت'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر")
    table = models.ForeignKey(Table, on_delete=models.CASCADE, verbose_name="میز")
    date = models.DateField(verbose_name="تاریخ")
    time = models.TimeField(verbose_name="ساعت شروع")
    end_time = models.TimeField(verbose_name="ساعت پایان", null=True)
    duration = models.PositiveIntegerField(verbose_name="مدت زمان (دقیقه)", choices=DURATION_CHOICES, default=60)
    guests = models.PositiveIntegerField(verbose_name="تعداد مهمان‌ها")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="وضعیت")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    
    class Meta:
        verbose_name = "رزرو"
        verbose_name_plural = "رزروها"
    
    def save(self, *args, **kwargs):
        if self.time and self.duration:
            # محاسبه ساعت پایان
            from datetime import datetime, timedelta
            start_datetime = datetime.combine(datetime.today(), self.time)
            end_datetime = start_datetime + timedelta(minutes=self.duration)
            self.end_time = end_datetime.time()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"رزرو {self.user.username} برای {self.table}"
