from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from learning.models import UserContentProgress, UserTestProgress, UserAnswer, Content
from landing.models import CustomUser
from learning.models import Test, Question, Answer

class Command(BaseCommand):
    help = "Отмечает все материалы и тесты как завершённые для указанного пользователя"

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Имя пользователя (username)')

    def handle(self, *args, **options):
        username = options['username']
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            raise CommandError(f"Пользователь с username '{username}' не найден")

        self.stdout.write(f"Начинаем выставление прогресса для пользователя: {user.username}")

        # 1. Контент
        contents = Content.objects.all()
        content_progress = [
            UserContentProgress(user=user, content=content, is_started=True, is_completed=True)
            for content in contents
        ]
        UserContentProgress.objects.bulk_create(content_progress, ignore_conflicts=True)
        self.stdout.write(f"✔ Добавлено {len(content_progress)} записей прогресса по контенту")

        # 2. Тесты
        tests = Test.objects.all()
        test_progress = [
            UserTestProgress(user=user, test=test, score=100, attempts=1, is_passed=True, last_attempt=timezone.now())
            for test in tests
        ]
        UserTestProgress.objects.bulk_create(test_progress, ignore_conflicts=True)
        self.stdout.write(f"✔ Добавлено {len(test_progress)} записей прогресса по тестам")

        # 3. Ответы на вопросы
        questions = Question.objects.all()
        answers = []

        for question in questions:
            correct_answer = (
                question.answers.filter(is_correct=True).first()
                if question.question_type in ['SC', 'MC']
                else None
            )
            if correct_answer:
                answers.append(UserAnswer(
                    user=user,
                    question=question,
                    answer=correct_answer,
                    is_correct=True
                ))

        UserAnswer.objects.bulk_create(answers, ignore_conflicts=True)
        self.stdout.write(f"✔ Добавлено {len(answers)} ответов на вопросы")

        self.stdout.write(self.style.SUCCESS(f"✅ Прогресс пользователя '{username}' успешно отмечен как завершённый."))
