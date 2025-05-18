from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import CustomUser
from classrooms.models import ClassSchedule, Classroom
from .serializers import RegisterSerializer, UserSerializer
from classrooms.serializers import ClassScheduleSerializer, ClassroomSerializer
from datetime import datetime


def get_day_code():
    weekday_map = {
        6: 'SUN',
        0: 'MON',
        1: 'TUE',
        2: 'WED',
        3: 'THU',
        4: 'FRI',
        5: 'SAT'
    }
    return weekday_map.get(datetime.today().weekday())


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class CustomTokenObtainPairView(TokenObtainPairView):
    pass


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def put(self, request):
        user = request.user
        data = request.data
        user.username = data.get("username", user.username)
        user.email = data.get("email", user.email)

        if "old_password" in data and "new_password" in data:
            old_password = data["old_password"]
            new_password = data["new_password"]

            if not user.check_password(old_password):
                return Response({"error": "كلمة المرور القديمة غير صحيحة."}, status=status.HTTP_400_BAD_REQUEST)

            if len(new_password) < 6:
                return Response({"error": "يجب أن تكون كلمة المرور الجديدة 6 أحرف على الأقل."}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)

        user.save()
        return Response({"message": "تم تحديث الحساب بنجاح."}, status=status.HTTP_200_OK)


class DoctorScheduleToday(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user
        if not user.is_authenticated or user.role != 'Doctor':
            return Response({'detail': '⚠️ ليس لديك صلاحية كـ Doctor'}, status=403)

        today_code = get_day_code()
        schedule = ClassSchedule.objects.filter(doctor=user, day=today_code)
        serializer = ClassScheduleSerializer(schedule, many=True)
        return Response(serializer.data)


class DoctorCurrentLecture(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user
        if not user.is_authenticated or user.role != 'Doctor':
            return Response({'detail': '⚠️ ليس لديك صلاحية كـ Doctor'}, status=403)

        now = datetime.now().time()
        today_code = get_day_code()

        current_lecture = ClassSchedule.objects.filter(
            doctor=user,
            day=today_code,
            start_time__lte=now,
            end_time__gte=now
        ).first()

        if current_lecture:
            return Response(ClassScheduleSerializer(current_lecture).data)

        return Response({"message": "🚫 لا توجد محاضرة حالياً."}, status=status.HTTP_204_NO_CONTENT)


class AdminProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'Admin':
            return Response({'detail': '⚠️ صلاحيات غير كافية (Admin فقط)'}, status=403)

        return Response(UserSerializer(request.user).data)


class AdminLectureListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ClassScheduleSerializer

    def get_queryset(self):
        if self.request.user.role != 'Admin':
            return ClassSchedule.objects.none()
        return ClassSchedule.objects.all()


class AdminLectureDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ClassScheduleSerializer

    def get_queryset(self):
        if self.request.user.role != 'Admin':
            return ClassSchedule.objects.none()
        return ClassSchedule.objects.all()


# ✅ تعديل هنا لدعم العرض بدون تسجيل دخول
class AdminClassroomListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ClassroomSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated or user.role == 'Admin':
            return Classroom.objects.all()
        return Classroom.objects.none()


class DoctorListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return CustomUser.objects.filter(role='Doctor')
        if getattr(user, 'role', None) == 'Admin':
            return CustomUser.objects.filter(role='Doctor')
        return CustomUser.objects.none()
        
        
        
        
        
        
from django.http import JsonResponse
from accounts.models import CustomUser

@csrf_exempt  # ⬅️ هذا مهم جداً
def reset_admin_password(request):
    if request.method != 'GET':  # نسمح فقط بـ GET لمزيد من الأمان
        return JsonResponse({'status': '❌ Invalid method'}, status=405)
    
    try:
        user = CustomUser.objects.get(username='Naif')
        user.set_password('Abdallaht')
        user.save()
        return JsonResponse({'status': '✅ Password reset successfully'})
    except CustomUser.DoesNotExist:
        return JsonResponse({'status': '❌ User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': '❌ Error', 'details': str(e)}, status=500)
✅ ثم: