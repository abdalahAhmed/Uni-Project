from rest_framework import generics, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Classroom, Course, ClassSchedule, Table, TableSchedule, DoctorAppointment
from .serializers import ClassroomSerializer, CourseSerializer, ClassScheduleSerializer, TableSerializer, TableScheduleSerializer, DoctorAppointmentSerializer
from datetime import datetime
from rest_framework.permissions import IsAuthenticated, AllowAny
from accounts.serializers import AdminSerializer
from accounts.models import CustomUser
from rest_framework import permissions
from django.shortcuts import get_object_or_404


class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = Classroom.objects.all()
    serializer_class = ClassroomSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
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
        Table.objects.filter(name=f"جدول {classroom_name}").delete()
        return response


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]


class ClassScheduleViewSet(viewsets.ModelViewSet):
    queryset = ClassSchedule.objects.all()
    serializer_class = ClassScheduleSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        active_table = Table.objects.filter(active=True).first()
        if active_table:
            queryset = queryset.filter(table_schedules__table=active_table, table_schedules__is_active=True).distinct()

        classroom_id = self.request.query_params.get('classroom')
        if classroom_id:
            queryset = queryset.filter(classroom_id=classroom_id)

        doctor_id = self.request.query_params.get('doctor')
        if doctor_id:
            queryset = queryset.filter(course__doctor__id=doctor_id)

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

        table_id = self.request.query_params.get('table_id')
        if table_id:
            queryset = queryset.filter(table_schedules__table_id=table_id)

        return queryset

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        schedule = self.get_object()
        schedule.is_canceled = True
        schedule.note = request.data.get('note', '')
        schedule.save()
        return Response({'status': 'lecture canceled', 'note': schedule.note})

    @action(detail=True, methods=['post'])
    def notify(self, request, pk=None):
        schedule = self.get_object()
        note = request.data.get('note', '')
        if note:
            schedule.note = note
            schedule.save()
            return Response({'status': 'note sent', 'note': schedule.note})
        return Response({'error': 'No note provided'}, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
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

        table_schedule, created = TableSchedule.objects.get_or_create(table=table, class_schedule=class_schedule)
        if not created:
            return Response({"error": "This lecture is already added to the table"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 'schedule added to table', 'table': table.name, 'class_schedule': class_schedule.course.name})

    @action(detail=True, methods=['post'])
    def set_active(self, request, pk=None):
        table = self.get_object()
        Table.objects.update(active=False)
        table.active = True
        table.save()
        return Response({'status': 'active table set', 'table': table.name})


class TableScheduleViewSet(viewsets.ModelViewSet):
    queryset = TableSchedule.objects.all()
    serializer_class = TableScheduleSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        table_id = self.request.query_params.get('table')
        if table_id:
            return TableSchedule.objects.filter(table_id=table_id)
        return TableSchedule.objects.all()


class DoctorAppointmentViewSet(viewsets.ModelViewSet):
    queryset = DoctorAppointment.objects.all()
    serializer_class = DoctorAppointmentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        doctor_id = self.request.query_params.get('doctor')
        if doctor_id:
            return DoctorAppointment.objects.filter(doctor_id=doctor_id)

        user = self.request.user
        if user.is_authenticated and hasattr(user, 'role') and user.role == 'Doctor':
            return DoctorAppointment.objects.filter(doctor=user)

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
        doctor = request.user
        queryset = ClassSchedule.objects.filter(
            course__doctor=doctor,
            table_schedules__is_active=True
        ).select_related('course', 'classroom').order_by('day', 'start_time')

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
        doctor = request.user
        weekday_map = {6: 'SUN', 0: 'MON', 1: 'TUE', 2: 'WED', 3: 'THU'}
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
        doctor = request.user
        total_lectures = ClassSchedule.objects.filter(course__doctor=doctor).count()
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
    queryset = CustomUser.objects.filter(role='Admin')
    serializer_class = AdminSerializer
    permission_classes = [IsAuthenticated]

