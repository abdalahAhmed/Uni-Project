from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClassroomViewSet,
    CourseViewSet,
    ClassScheduleViewSet,
    TableViewSet,
    TableScheduleViewSet,
    DoctorAppointmentViewSet,
    AdminsViewSet, 
)

# إعداد الراوتر
router = DefaultRouter()
router.register(r'classrooms', ClassroomViewSet, basename='classroom')
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'schedules', ClassScheduleViewSet, basename='schedule')
router.register(r'tables', TableViewSet, basename='table')
router.register(r'table-schedules', TableScheduleViewSet, basename='table-schedule')
router.register(r'doctor-appointments', DoctorAppointmentViewSet, basename='doctor-appointment')
router.register(r'admins', AdminsViewSet, basename='admins')  

# تضمين المسارات
urlpatterns = [
    path('', include(router.urls)),
]
