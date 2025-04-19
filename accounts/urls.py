from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    # تسجيل وإنشاء الحساب
    RegisterView,
    UserProfileView,

    # واجهات الدكتور
    DoctorScheduleToday,
    DoctorCurrentLecture,

    # واجهات المشرف (Admin)
    AdminLectureListCreateView,
    AdminLectureDetailView,
    AdminClassroomListView,

    # عرض الدكاترة
    DoctorListView,
)

urlpatterns = [
    # التسجيل والدخول باستخدام JWT
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    #  الملف الشخصي
    path('profile/', UserProfileView.as_view(), name='user_profile'),

    # واجهات الدكتور
    path('schedule/today/', DoctorScheduleToday.as_view(), name='doctor_schedule_today'),
    path('schedule/now/', DoctorCurrentLecture.as_view(), name='doctor_current_lecture'),
    #  واجهات المشرف (Admin)
    path('admin/lectures/', AdminLectureListCreateView.as_view(), name='admin_lecture_list_create'),
    path('admin/lectures/<int:pk>/', AdminLectureDetailView.as_view(), name='admin_lecture_detail'),
    path('admin/classrooms/', AdminClassroomListView.as_view(), name='admin_classroom_list'),

    # ✅ قائمة الدكاترة (لاستخدامها في تبويب Add Course مثلاً)
    path('doctors/', DoctorListView.as_view(), name='doctor_list'),
    
]
