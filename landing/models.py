from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Count, Avg, Sum

class Group(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Название группы',
        help_text='Например: ОФ-409-079-4-1'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['name']

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('teacher', 'Преподаватель'),
        ('student', 'Студент'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Номер телефона',
        help_text='Введите номер телефона'
    )

    telegram = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Telegram',
        help_text='Telegram username (например, @username)'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Группа',
        help_text='Группа студента (если применимо)'
    )

    def completed_contents_count(self):
        return self.content_progress.filter(is_completed=True).count()

    def average_test_score(self):
        avg = self.test_progress.aggregate(avg_score=Avg('score'))['avg_score']
        return round(avg, 2) if avg else 0

    def total_test_attempts(self):
        return self.test_progress.aggregate(total=Sum('attempts'))['total'] or 0

    def __str__(self):
        return self.username