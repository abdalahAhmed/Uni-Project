from django.db import models
from accounts.models import CustomUser  # Custom user model

# جدول القاعات
class Classroom(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200, blank=True)
    capacity = models.CharField(max_length=100, verbose_name="السعة", default="")



    def __str__(self):
        return f"{self.name} ({self.capacity} مقعد)"


# جدول الكورسات
class Course(models.Model):
    name = models.CharField(max_length=100, verbose_name="اسم الكورس")
    code = models.CharField(max_length=20, unique=True, verbose_name="رمز الكورس")
    description = models.TextField(blank=True, null=True, verbose_name="وصف الكورس")
    
    
    doctor = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role__iexact': 'Doctor'},  # فقط المستخدمين الذين دورهم Doctor
        related_name='courses_as_doctor',
        verbose_name="الدكتور المسؤول"
    )
    
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name="القاعة"
    )

    num_students = models.CharField(max_length=100, verbose_name="عدد الطلاب", default="")
    
    def __str__(self):
        return f"{self.code} - {self.name}"


# جدول المحاضرات (الجدول الدراسي)
class ClassSchedule(models.Model):
    DAYS_OF_WEEK = [
        ('SUN', 'Sunday'),
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
    ]

    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='schedules'  # الربط بين الكورس والجدول
    )
    day = models.CharField(max_length=3, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_canceled = models.BooleanField(default=False, verbose_name='تم الإلغاء')
    note = models.CharField(max_length=255, blank=True, null=True, verbose_name='ملاحظة الدكتور')

    class Meta:
        ordering = ['day', 'start_time']  # ترتيب الجدول حسب الأيام والتوقيت

    def __str__(self):
        status = "❌ ملغاة" if self.is_canceled else "✅ نشطة"
        return f"{self.course.name} - {self.classroom.name} ({self.day}) [{status}]"


# جدول الجداول (Represents the scheduling table)
class Table(models.Model):
    name = models.CharField(max_length=255, verbose_name="اسم الجدول")  # اسم الجدول
    description = models.TextField(blank=True, null=True, verbose_name="وصف الجدول")  # وصف الجدول إن أردت
    active = models.BooleanField(default=False, verbose_name="جدول نشط")  # تحديد الجدول النشط

    def __str__(self):
        return f"{self.name} {'(نشط)' if self.active else ''}"


# جدول ربط الجداول بالمحاضرات
class TableSchedule(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name="table_schedules")  # ربط الجدول مع جدول المحاضرات
    class_schedule = models.ForeignKey(ClassSchedule, on_delete=models.CASCADE, related_name="table_schedules")
    is_active = models.BooleanField(default=True)  # تحديد ما إذا كانت المحاضرة نشطة في الجدول

    class Meta:
        unique_together = ('table', 'class_schedule')  # منع التكرار
        ordering = ['table', 'class_schedule__day', 'class_schedule__start_time']

    def __str__(self):
        return f"📅 {self.table.name} - {self.class_schedule.course.name} ({self.class_schedule.day} {self.class_schedule.start_time})"


# نموذج مواعيد الدكتور
class DoctorAppointment(models.Model):
    doctor = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role__iexact': 'Doctor'},  # التأكد من أن المواعيد تخص دكتور
        related_name='appointments',
        verbose_name="الدكتور المسؤول"
    )
    location = models.CharField(max_length=255, verbose_name="المكان")  # المكان (مثل المكتب، القاعة)
    appointment_date = models.DateField(verbose_name="تاريخ الموعد")  # تاريخ الموعد
    appointment_time = models.TimeField(verbose_name="وقت الموعد")  # وقت الموعد
    available = models.BooleanField(default=True, verbose_name="هل الموعد متاح؟")  # هل الموعد متاح للحجز؟
    
    # وصف الموعد (اختياري)
    description = models.TextField(blank=True, null=True, verbose_name="وصف الموعد")

    class Meta:
        ordering = ['appointment_date', 'appointment_time']  # ترتيب المواعيد حسب التاريخ والوقت

    def __str__(self):
        return f"موعد {self.doctor.username} في {self.location} بتاريخ {self.appointment_date} الساعة {self.appointment_time}"
