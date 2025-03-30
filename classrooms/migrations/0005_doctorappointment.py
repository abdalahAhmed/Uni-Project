# Generated by Django 4.2.15 on 2025-03-27 17:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('classrooms', '0004_tableschedule_is_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='DoctorAppointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.CharField(max_length=255, verbose_name='المكان')),
                ('appointment_date', models.DateField(verbose_name='تاريخ الموعد')),
                ('appointment_time', models.TimeField(verbose_name='وقت الموعد')),
                ('available', models.BooleanField(default=True, verbose_name='هل الموعد متاح؟')),
                ('description', models.TextField(blank=True, null=True, verbose_name='وصف الموعد')),
                ('doctor', models.ForeignKey(limit_choices_to={'role__iexact': 'Doctor'}, on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to=settings.AUTH_USER_MODEL, verbose_name='الدكتور المسؤول')),
            ],
            options={
                'ordering': ['appointment_date', 'appointment_time'],
            },
        ),
    ]
