from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Restaurant, Table, Reservation
from datetime import datetime, timedelta
from django.db.models import Q

def home(request):
    restaurants = Restaurant.objects.all()[:6]  # نمایش 6 رستوران در صفحه اصلی
    return render(request, 'reservation/home.html', {'restaurants': restaurants})

def restaurant_list(request):
    restaurants = Restaurant.objects.all()
    return render(request, 'reservation/restaurant_list.html', {'restaurants': restaurants})

def restaurant_detail(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    remaining_capacity = None
    tables = Table.objects.filter(restaurant=restaurant).order_by('number')
    reserved_tables = []
    
    date = request.GET.get('date')
    time = request.GET.get('time')
    duration = request.GET.get('duration', 60)  # پیش‌فرض ۱ ساعت
    
    if date and time:
        try:
            # تبدیل زمان به datetime
            time_obj = datetime.strptime(time, '%H:%M').time()
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
            duration = int(duration)
            
            # محاسبه زمان پایان
            start_datetime = datetime.combine(date_obj, time_obj)
            end_datetime = start_datetime + timedelta(minutes=duration)
            end_time = end_datetime.time()
            
            # پرینت مقادیر برای دیباگ
            print(f"Selected time: {time_obj}")
            print(f"End time: {end_time}")
            print(f"Restaurant opening time: {restaurant.opening_time}")
            print(f"Restaurant closing time: {restaurant.closing_time}")
            print(f"Time comparisons:")
            print(f"Start hour check: {time_obj.hour} < {restaurant.opening_time.hour}")
            print(f"Start minute check: {time_obj.hour} == {restaurant.opening_time.hour} and {time_obj.minute} < {restaurant.opening_time.minute}")
            print(f"End hour check: {end_time.hour} > {restaurant.closing_time.hour}")
            print(f"End minute check: {end_time.hour} == {restaurant.closing_time.hour} and {end_time.minute} > {restaurant.closing_time.minute}")
            
            # گرفتن میزهای رزرو شده که با این بازه زمانی تداخل دارند
            reserved_tables = Table.objects.filter(
                restaurant=restaurant,
                reservation__date=date,
                reservation__status='confirmed'
            ).filter(
                Q(
                    reservation__time__lt=end_time,
                    reservation__end_time__gt=time_obj
                )
            ).values_list('id', flat=True)
            
            remaining_capacity = restaurant.get_remaining_capacity(date, time)
        except (ValueError, TypeError):
            messages.error(request, 'لطفاً تاریخ و زمان معتبر وارد کنید.')
    
    context = {
        'restaurant': restaurant,
        'remaining_capacity': remaining_capacity,
        'selected_date': date,
        'selected_time': time,
        'selected_duration': duration,
        'tables': tables,
        'reserved_tables': reserved_tables,
        'duration_choices': Reservation.DURATION_CHOICES,
    }
    return render(request, 'reservation/restaurant_detail.html', context)

@login_required
def make_reservation(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    
    if request.method == 'POST':
        date = request.POST.get('date')
        time = request.POST.get('time')
        duration = int(request.POST.get('duration', 60))
        guests = int(request.POST.get('guests'))
        table_id = request.POST.get('table')
        
        if not all([date, time, table_id]):
            messages.error(request, 'لطفاً تمام فیلدها را پر کنید.')
            return redirect('reservation:restaurant_detail', pk=restaurant_id)
        
        table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
        
        # بررسی ظرفیت میز
        if guests > table.capacity:
            messages.error(request, f'ظرفیت میز انتخاب شده ({table.capacity} نفر) کمتر از تعداد مهمان‌های شماست.')
            return redirect('reservation:restaurant_detail', pk=restaurant_id)
        
        try:
            # تبدیل زمان به datetime
            time_obj = datetime.strptime(time, '%H:%M').time()
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
            
            # محاسبه زمان پایان
            start_datetime = datetime.combine(date_obj, time_obj)
            end_datetime = start_datetime + timedelta(minutes=duration)
            end_time = end_datetime.time()
            
            # پرینت مقادیر برای دیباگ
            print(f"Selected time: {time_obj}")
            print(f"End time: {end_time}")
            print(f"Restaurant opening time: {restaurant.opening_time}")
            print(f"Restaurant closing time: {restaurant.closing_time}")
            print(f"Time comparisons:")
            print(f"Start hour check: {time_obj.hour} < {restaurant.opening_time.hour}")
            print(f"Start minute check: {time_obj.hour} == {restaurant.opening_time.hour} and {time_obj.minute} < {restaurant.opening_time.minute}")
            print(f"End hour check: {end_time.hour} > {restaurant.closing_time.hour}")
            print(f"End minute check: {end_time.hour} == {restaurant.closing_time.hour} and {end_time.minute} > {restaurant.closing_time.minute}")
            
            # بررسی ساعت کاری رستوران
            if (time_obj.hour < restaurant.opening_time.hour or 
                (time_obj.hour == restaurant.opening_time.hour and time_obj.minute < restaurant.opening_time.minute) or
                end_time.hour > restaurant.closing_time.hour or
                (end_time.hour == restaurant.closing_time.hour and end_time.minute > restaurant.closing_time.minute)):
                messages.error(request, 'زمان انتخاب شده خارج از ساعت کاری رستوران است.')
                return redirect('reservation:restaurant_detail', pk=restaurant_id)
            
            # بررسی تداخل زمانی
            conflicting_reservation = Reservation.objects.filter(
                table=table,
                date=date,
                status='confirmed'
            ).filter(
                Q(
                    time__lt=end_time,
                    end_time__gt=time_obj
                )
            ).first()
            
            if conflicting_reservation:
                messages.error(request, 'این میز در بازه زمانی انتخاب شده رزرو شده است.')
                return redirect('reservation:restaurant_detail', pk=restaurant_id)
            
            # ایجاد رزرو
            reservation = Reservation.objects.create(
                user=request.user,
                table=table,
                date=date,
                time=time_obj,
                duration=duration,
                guests=guests,
                status='confirmed'
            )
            messages.success(request, 'رزرو شما با موفقیت ثبت شد.')
            return redirect('reservation:my_reservations')
            
        except (ValueError, TypeError):
            messages.error(request, 'لطفاً تاریخ و زمان معتبر وارد کنید.')
            return redirect('reservation:restaurant_detail', pk=restaurant_id)
    
    return redirect('reservation:restaurant_detail', pk=restaurant_id)

@login_required
def my_reservations(request):
    reservations = Reservation.objects.filter(user=request.user).order_by('-date', '-time')
    return render(request, 'reservation/my_reservations.html', {'reservations': reservations})
