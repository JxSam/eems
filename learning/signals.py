from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Content, Test
from content_reader.models import Practical, PracticalFile
from landing.models import CustomUser
import logging

logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=Content)
def invalidate_content_cache(sender, **kwargs):
    # Удаляем общие кэши
    cache.delete('total_courses')

    # Вместо cache.keys() используем явное удаление или другой подход
    # Вариант 1: Удаляем все ключи по шаблону (если используете Redis)
    try:
        cache.delete_pattern('dashboard_data_*')  # Работает только с Redis
    except AttributeError:
        logger.warning("delete_pattern not available, falling back to manual cache invalidation")
        # Вариант 2: Ведем список ключей в отдельном кэш-ключе
        dashboard_keys = cache.get('all_dashboard_keys', set())
        for key in dashboard_keys:
            cache.delete(key)
        cache.delete('all_dashboard_keys')


@receiver([post_save, post_delete], sender=Test)
def invalidate_test_cache(sender, **kwargs):
    cache.delete('total_tests')
    # Аналогично предыдущей функции
    try:
        cache.delete_pattern('dashboard_data_*')
    except AttributeError:
        dashboard_keys = cache.get('all_dashboard_keys', set())
        for key in dashboard_keys:
            cache.delete(key)
        cache.delete('all_dashboard_keys')


@receiver([post_save, post_delete], sender=Practical)
def invalidate_practical_cache(sender, **kwargs):
    cache.delete('total_practicals')
    # Аналогично предыдущим функциям
    try:
        cache.delete_pattern('dashboard_data_*')
    except AttributeError:
        dashboard_keys = cache.get('all_dashboard_keys', set())
        for key in dashboard_keys:
            cache.delete(key)
        cache.delete('all_dashboard_keys')


@receiver([post_save, post_delete], sender=PracticalFile)
def invalidate_user_practical_cache(sender, instance, **kwargs):
    # Очищаем кэш только для конкретного пользователя
    user_id = instance.user.id
    cache.delete(f"user_progress_{user_id}")
    cache.delete(f"dashboard_data_{user_id}")

    # Обновляем список ключей, если используем второй подход
    dashboard_keys = cache.get('all_dashboard_keys', set())
    dashboard_keys.discard(f"dashboard_data_{user_id}")
    cache.set('all_dashboard_keys', dashboard_keys)


@receiver([post_save, post_delete], sender=CustomUser)
def invalidate_students_cache(sender, **kwargs):
    cache.delete('students_progress_data')