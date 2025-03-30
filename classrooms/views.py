from rest_framework import generics, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Classroom, Course, ClassSchedule, Table, TableSchedule, DoctorAppointment
from .serializers import ClassroomSerializer, CourseSerializer, ClassScheduleSerializer, TableSerializer, TableScheduleSerializer, DoctorAppointmentSerializer
from datetime import datetime
from rest_framework.permissions import IsAuthenticated, AllowAny  # ✅ أضف AllowAny
from accounts.serializers import AdminSerializer
from accounts.models import CustomUser
from rest_framework import permissions




# ViewSet لإدارة القاعات
class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = Classroom.objects.all()
    serializer_class = ClassroomSerializer
    permission_classes = [AllowAny]  # ✅ السماح لأي شخص (حتى بدون تسجيل دخول)
 
    def create(self, request, *args, **kwargs):
        # إنشاء القاعة
        response = super().create(request, *args, **kwargs)

        # إنشاء جدول جديد بنفس اسم القاعة
        classroom_name = response.data.get('name')
        if classroom_name:
            Table.objects.create(
                name=f"جدول {classroom_name}",
                description=f"جدول مخصص للقاعة {classroom_name}"
            )

        return response

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        old_name = instance.name
        response = super().update(request, *args, **kwargs)

        # تحديث اسم الجدول إذا كان بنفس اسم القاعة القديمة
        new_name = request.data.get('name')
        if new_name and old_name != new_name:
            try:
                table = Table.objects.get(name=f"جدول {old_name}")
                table.name = f"جدول {new_name}"
                table.description = f"جدول مخصص للقاعة {new_name}"
                table.save()
            except Table.DoesNotExist:
                pass

        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        classroom_name = instance.name
        response = super().destroy(request, *args, **kwargs)

        # حذف الجدول إذا كان مرتبط باسم القاعة
        Table.objects.filter(name=f"جدول {classroom_name}").delete()

        return response


# ViewSet لإدارة الكورسات
class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]


# ViewSet لإدارة الجدول الدراسي
class ClassScheduleViewSet(viewsets.ModelViewSet):
    queryset = ClassSchedule.objects.all()
    serializer_class = ClassScheduleSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()

        # فلترة حسب الجدول النشط
        active_table = Table.objects.filter(active=True).first()
        if active_table:
            queryset = queryset.filter(table_schedules__table=active_table, table_schedules__is_active=True).distinct()

        # فلترة حسب القاعة
        classroom_id = self.request.query_params.get('classroom')
        if classroom_id:
            queryset = queryset.filter(classroom_id=classroom_id)

        # فلترة حسب الدكتور
        doctor_id = self.request.query_params.get('doctor')
        if doctor_id:
            queryset = queryset.filter(course__doctor__id=doctor_id)

        # فلترة حسب اليوم
        today_only = self.request.query_params.get('today')
        day_param = self.request.query_params.get('day')

        weekday_map = {
            6: 'SUN',
            0: 'MON',
            1: 'TUE',
            2: 'WED',
            3: 'THU',
            4: 'FRI',
            5: 'SAT'
        }

        if today_only == '1':
            current_day = weekday_map.get(datetime.today().weekday())
            queryset = queryset.filter(day=current_day)
        elif day_param in [d[0] for d in ClassSchedule.DAYS_OF_WEEK]:
            queryset = queryset.filter(day=day_param)

        # فلترة حسب الجدول
        table_id = self.request.query_params.get('table_id')
        if table_id:
            queryset = queryset.filter(table_schedules__table_id=table_id)

        return queryset

    # إجراء: إلغاء محاضرة
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        schedule = self.get_object()
        schedule.is_canceled = True
        schedule.note = request.data.get('note', '')
        schedule.save()
        return Response({'status': 'lecture canceled', 'note': schedule.note})

    # إجراء: إرسال ملاحظة للطلاب
    @action(detail=True, methods=['post'])
    def notify(self, request, pk=None):
        schedule = self.get_object()
        note = request.data.get('note', '')
        if note:
            schedule.note = note
            schedule.save()
            return Response({'status': 'note sent', 'note': schedule.note})
        return Response({'error': 'No note provided'}, status=status.HTTP_400_BAD_REQUEST)

    # تعديل: ربط المحاضرة تلقائيًا بالجدول النشط عند الإنشاء
    def create(self, request, *args, **kwargs):
        # إنشاء المحاضرة
        response = super().create(request, *args, **kwargs)

        # الحصول على الجدول النشط
        active_table = Table.objects.filter(active=True).first()

        if active_table:
            class_schedule = ClassSchedule.objects.get(id=response.data['id'])
            TableSchedule.objects.create(table=active_table, class_schedule=class_schedule)

        return response


class TableViewSet(viewsets.ModelViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=['post'])
    def add_schedule(self, request, pk=None):
        table = self.get_object()
        class_schedule_id = request.data.get('class_schedule_id')

        try:
            class_schedule = ClassSchedule.objects.get(id=class_schedule_id)
        except ClassSchedule.DoesNotExist:
            return Response({"error": "Class schedule not found"}, status=status.HTTP_404_NOT_FOUND)

        # ربط المحاضرة بالجدول
        table_schedule, created = TableSchedule.objects.get_or_create(table=table, class_schedule=class_schedule)
        if not created:
            return Response({"error": "This lecture is already added to the table"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 'schedule added to table', 'table': table.name, 'class_schedule': class_schedule.course.name})

    # إجراء لتحديث الجدول النشط
    @action(detail=True, methods=['post'])
    def set_active(self, request, pk=None):
        table = self.get_object()

        # إلغاء تفعيل جميع الجداول الأخرى
        Table.objects.update(active=False)

        # تفعيل الجدول الحالي
        table.active = True
        table.save()

        return Response({'status': 'active table set', 'table': table.name})


class TableScheduleViewSet(viewsets.ModelViewSet):
    queryset = TableSchedule.objects.all()
    serializer_class = TableScheduleSerializer
    permission_classes = [AllowAny]

    # إجراء لعرض الجداول مع المحاضرات
    def get_queryset(self):
        table_id = self.request.query_params.get('table')
        if table_id:
            return TableSchedule.objects.filter(table_id=table_id)
        return TableSchedule.objects.all()


# DoctorAppointments ViewSet
class DoctorAppointmentViewSet(viewsets.ModelViewSet):
    queryset = DoctorAppointment.objects.all()
    serializer_class = DoctorAppointmentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        # ✅ دعم فلترة بالمستخدم المحدد (وضع العرض)
        doctor_id = self.request.query_params.get('doctor')
        if doctor_id:
            return DoctorAppointment.objects.filter(doctor_id=doctor_id)

        # ✅ دعم وضع تسجيل الدخول (الدكتور يشوف مواعيده فقط)
        user = self.request.user
        if user.is_authenticated and hasattr(user, 'role') and user.role == 'Doctor':
            return DoctorAppointment.objects.filter(doctor=user)

        # ❌ غير مصرح له أو لم يحدد دكتور
        return DoctorAppointment.objects.none()

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def update_appointment(self, request, pk=None):
        appointment = self.get_object()
        appointment.available = request.data.get('available', appointment.available)
        appointment.save()
        return Response({'status': 'appointment updated', 'available': appointment.available})



class DoctorDashboardViewSet(viewsets.ViewSet):
    serializer_class = ClassScheduleSerializer
    permission_classes = [AllowAny]
    
    def list(self, request):
        """
        عرض جدول المحاضرات الكامل للدكتور
        """
        doctor = request.user
        queryset = ClassSchedule.objects.filter(
            course__doctor=doctor,
            table_schedules__is_active=True
        ).select_related('course', 'classroom').order_by('day', 'start_time')
        
        # فلترة حسب اليوم إذا طلب
        day = request.query_params.get('day')
        if day:
            queryset = queryset.filter(day=day)
        
        serializer = self.serializer_class(queryset, many=True)
        return Response({
            'doctor': {
                'id': doctor.id,
                'name': f"{doctor.first_name} {doctor.last_name}",
                'email': doctor.email
            },
            'schedule': serializer.data
        })

    @action(detail=False, methods=['get'])
    def today(self, request):
        """
        عرض محاضرات اليوم فقط
        """
        doctor = request.user
        weekday_map = {
            6: 'SUN', 0: 'MON', 1: 'TUE', 2: 'WED', 3: 'THU'
        }
        today = weekday_map.get(datetime.today().weekday())
        
        queryset = ClassSchedule.objects.filter(
            course__doctor=doctor,
            day=today,
            table_schedules__is_active=True
        ).select_related('course', 'classroom').order_by('start_time')
        
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        إلغاء محاضرة مع إضافة ملاحظة
        """
        schedule = get_object_or_404(
            ClassSchedule, 
            pk=pk,
            course__doctor=request.user
        )
        schedule.is_canceled = True
        schedule.note = request.data.get('note', '')
        schedule.save()
        return Response({
            'status': 'success',
            'message': 'تم إلغاء المحاضرة بنجاح',
            'lecture': self.serializer_class(schedule).data
        })

    @action(detail=True, methods=['post'])
    def add_note(self, request, pk=None):
        """
        إضافة/تعديل ملاحظة على المحاضرة
        """
        schedule = get_object_or_404(
            ClassSchedule, 
            pk=pk,
            course__doctor=request.user
        )
        note = request.data.get('note')
        if not note:
            return Response(
                {'error': 'يجب إدخال ملاحظة'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        schedule.note = note
        schedule.save()
        return Response({
            'status': 'success',
            'message': 'تم تحديث الملاحظة بنجاح',
            'lecture': self.serializer_class(schedule).data
        })

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        إحصائيات محاضرات الدكتور
        """
        doctor = request.user
        total_lectures = ClassSchedule.objects.filter(
            course__doctor=doctor
        ).count()
        
        active_lectures = ClassSchedule.objects.filter(
            course__doctor=doctor,
            is_canceled=False,
            table_schedules__is_active=True
        ).count()
        
        canceled_lectures = ClassSchedule.objects.filter(
            course__doctor=doctor,
            is_canceled=True
        ).count()
        
        return Response({
            'total_lectures': total_lectures,
            'active_lectures': active_lectures,
            'canceled_lectures': canceled_lectures
        })


class AdminsViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.filter(role='Admin')  # تأكد إن عندك حقل role
    serializer_class = AdminSerializer
    permission_classes = [IsAuthenticated]  # أو AllowAny لو عايز مؤقتًا