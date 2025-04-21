from rest_framework import serializers
from .models import Classroom, Course, ClassSchedule, Table, TableSchedule, DoctorAppointment
from accounts.models import CustomUser  # استخدام CustomUser مباشرة

# Serializer لعرض بيانات القاعات
class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = '__all__'


# Serializer لعرض بيانات المستخدمين من نوع "Doctor"
class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


# Serializer للكورسات

class CourseSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer(read_only=True)
    doctor_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role='Doctor'),
        source='doctor',
        write_only=True
    )

    classroom = ClassroomSerializer(read_only=True)  # للعرض
    classroom_id = serializers.PrimaryKeyRelatedField(  # للكتابة بنفس اسم الحقل في الواجهة
        queryset=Classroom.objects.all(),
        source='classroom',
        write_only=True
    )

    class Meta:
        model = Course
        fields = [
            'id',
            'name',
            'code',
            'description',
            'doctor',
            'doctor_id',
            'classroom',
            'classroom_id',  # نفس اسم الحقل الجاي من React
            'num_students'
        ]

    def create(self, validated_data):
        return Course.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance




# Serializer للجدول الدراسي
class ClassScheduleSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    classroom = ClassroomSerializer(read_only=True)
    table_schedules = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        source='course',
        write_only=True
    )
    classroom_id = serializers.PrimaryKeyRelatedField(
        queryset=Classroom.objects.all(),
        source='classroom',
        write_only=True
    )

    class Meta:
        model = ClassSchedule
        fields = [
            'id',
            'classroom', 'classroom_id',
            'course', 'course_id',
            'day',
            'start_time',
            'end_time',
            'is_canceled',
            'note',
            'table_schedules'
        ]

    def validate(self, data):
        # بيانات أساسية
        classroom = data.get('classroom') or getattr(self.instance, 'classroom', None)
        course = data.get('course') or getattr(self.instance, 'course', None)
        day = data.get('day') or getattr(self.instance, 'day', None)
        start_time = data.get('start_time') or getattr(self.instance, 'start_time', None)
        end_time = data.get('end_time') or getattr(self.instance, 'end_time', None)

        # تحقق من توقيت صحيح
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("🛑 وقت البداية يجب أن يكون قبل وقت النهاية!")

        # تحقق من تداخل في القاعة
        room_conflict = ClassSchedule.objects.filter(
            day=day,
            classroom=classroom,
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        if self.instance:
            room_conflict = room_conflict.exclude(id=self.instance.id)

        if room_conflict.exists():
            raise serializers.ValidationError("⚠️ يوجد محاضرة أخرى في نفس القاعة بهذا الوقت.")

        # تحقق من تداخل في مواعيد الدكتور
        if course and course.doctor:
            doctor_conflict = ClassSchedule.objects.filter(
                day=day,
                course__doctor=course.doctor,
                start_time__lt=end_time,
                end_time__gt=start_time
            )
            if self.instance:
                doctor_conflict = doctor_conflict.exclude(id=self.instance.id)

            if doctor_conflict.exists():
                raise serializers.ValidationError("⚠️ يوجد محاضرة أخرى لهذا الدكتور في هذا الوقت.")

        return data

    def create(self, validated_data):
        return ClassSchedule.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance



# Serializer لعرض بيانات الجداول (Tables)
class TableSerializer(serializers.ModelSerializer):
    active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Table
        fields = ['id', 'name', 'description', 'active']


# Serializer لربط الجداول بالمحاضرات
class TableScheduleSerializer(serializers.ModelSerializer):
    table = TableSerializer(read_only=True)
    class_schedule = ClassScheduleSerializer(read_only=True)

    table_id = serializers.PrimaryKeyRelatedField(
        queryset=Table.objects.all(),
        source='table',
        write_only=True
    )
    class_schedule_id = serializers.PrimaryKeyRelatedField(
        queryset=ClassSchedule.objects.all(),
        source='class_schedule',
        write_only=True
    )

    class Meta:
        model = TableSchedule
        fields = ['id', 'table', 'table_id', 'class_schedule', 'class_schedule_id', 'is_active']

    def validate(self, data):
        table = data.get('table')
        class_schedule = data.get('class_schedule')
        if TableSchedule.objects.filter(table=table, class_schedule=class_schedule).exists():
            raise serializers.ValidationError("⚠️ هذه المحاضرة مضافة بالفعل في الجدول!")
        return data

    def create(self, validated_data):
        return TableSchedule.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ✅ Serializer لعرض بيانات مواعيد الدكتور بعد التعديل
class DoctorAppointmentSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer(read_only=True)

    class Meta:
        model = DoctorAppointment
        fields = ['id', 'doctor', 'location', 'appointment_date', 'appointment_time', 'available', 'description']

    def create(self, validated_data):
        validated_data['doctor'] = self.context['request'].user  # ربط الموعد بالمستخدم الحالي
        return DoctorAppointment.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

