from rest_framework import serializers
from .models import CustomUser
from django.contrib.auth.password_validation import validate_password

# ✅ قائمة الأدوار المسموحة
VALID_ROLES = ['Doctor', 'Admin']

# ✅ قائمة ألقاب العرض الممكنة
VALID_TITLES = ['دكتور', 'محاضر', 'مهندس']


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    display_title = serializers.ChoiceField(
        choices=VALID_TITLES,
        required=False,
        allow_blank=True,
        allow_null=True
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'role', 'display_title')

    def validate_email(self, value):
        if not any(value.endswith(suffix) for suffix in ['.edu', '@university-domain.com']):
            raise serializers.ValidationError("يجب أن يكون البريد الإلكتروني تابعًا للجامعة (ينتهي بـ .edu)")
        return value

    def validate_role(self, value):
        if value not in VALID_ROLES:
            raise serializers.ValidationError("الدور يجب أن يكون إما 'Doctor' أو 'Admin'.")
        return value

    def validate(self, data):
        # ✅ تأكد من وجود اللقب إذا كان الدور Doctor
        if data['role'] == 'Doctor':
            if not data.get('display_title'):
                raise serializers.ValidationError({
                    'display_title': 'يرجى اختيار اللقب (دكتور / محاضر / مهندس)'
                })
        return data

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data['role'],
            display_title=validated_data.get('display_title', ''),
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'display_title']


class AdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'full_name', 'phone', 'password']
        read_only_fields = ['id']

    def create(self, validated_data):
        validated_data['role'] = 'Admin'
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user
