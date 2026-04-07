from landing.models import CustomUser
from django.urls import reverse
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from transliterate import translit
from django.core.validators import MinValueValidator, MaxValueValidator

class Competency(models.Model):
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Код компетенции",
        help_text="Например: ПК 5.1"
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Название компетенции",
        help_text="Полное название компетенции"
    )

    class Meta:
        verbose_name = "Компетенция"
        verbose_name_plural = "Компетенции"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

class Content(models.Model):
    number = models.IntegerField(unique=True, default=1)
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(default='Описание')
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    visible = models.BooleanField(default=True)
    owner = models.ForeignKey(
        CustomUser, null=True, blank=True, on_delete=models.CASCADE
    )
    competencies = models.ManyToManyField(
        Competency,
        related_name='contents',
        verbose_name="Компетенции"
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = translit(self.title, 'ru', reversed=True)
            base_slug = slugify(base_slug)
            slug = base_slug
            counter = 1
            # Проверка на уникальность
            while Content.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('preview', kwargs={'slug': self.slug})

    def get_absolute_url_edit(self):
        return reverse('edit', kwargs={'slug': self.slug})

    def __str__(self):
        return f"{self.number} - {self.title}"

class Subcontent(models.Model):
    content = models.ForeignKey(Content, null=False, on_delete=models.CASCADE)
    step = models.IntegerField(default=1)
    title = models.CharField(max_length=250)
    body = models.TextField()

    def __str__(self):
        return f"{self.title} - {self.step}"

    def get_absolute_url(self):
        return reverse('preview', kwargs={'slug': self.content.slug, 'step': self.step})

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['content', 'step'], name='unique_step_per_content')
        ]

    def clean(self):
        # Проверка, нет ли такого step в Test
        if Test.objects.filter(content=self.content, step=self.step).exists():
            raise ValidationError(f"Step {self.step} уже используется в Test этого Content.")
        super().clean()

class Test(models.Model):
    content = models.ForeignKey(Content, null=False, on_delete=models.CASCADE)
    step = models.IntegerField()  # Тоже step
    title = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.content.title} - Тест {self.step}"

    class Meta:
        unique_together = ('content', 'step')  # Чтобы не было двух тестов с одним step в рамках Content

    def clean(self):
        # Проверка, нет ли такого step в Subcontent
        if Subcontent.objects.filter(content=self.content, step=self.step).exists():
            raise ValidationError(f"Step {self.step} уже используется в Subcontent этого Content.")
        super().clean()

class Question(models.Model):
    QUESTION_TYPES = (
        ('MC', 'Выбор ответа'),  # Вопрос с выбором ответа
        ('FB', 'Дополнение'),    # Вопрос на дополнение
        ('MT', 'Соответствие'),  # Новый тип - вопрос на соответствие
    )
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=2, choices=QUESTION_TYPES, default='MC')
    correct_answer = models.TextField(blank=True, null=True)  # Для вопросов на дополнение
    def __str__(self):
        return self.text

    def clean(self):
        if self.question_type == 'FB' and not self.correct_answer:
            raise ValidationError("Для вопросов на дополнение необходимо указать правильный ответ")
        if self.question_type == 'MT' and self.answers.exists():
            raise ValidationError("Для вопросов на соответствие не нужно создавать варианты ответов через Answer")
        super().clean()


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

    def clean(self):
        if self.question.question_type == 'FB':
            raise ValidationError("Для вопросов на дополнение не нужно создавать варианты ответов")
        super().clean()

class MatchingPair(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='matching_pairs')
    term = models.CharField(max_length=255)       # Термин (левая колонка)
    definition = models.CharField(max_length=255)  # Определение (правая колонка)
    order = models.PositiveIntegerField(default=0) # Порядок отображения
    class Meta:
        ordering = ['order']
        unique_together = ('question', 'term')  # Термин должен быть уникальным в рамках вопроса
    def __str__(self):
        return f"{self.term} - {self.definition}"

class UserContentProgress(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='content_progress')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='user_progress')
    is_started = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'content']),
            models.Index(fields=['is_completed']),
            models.Index(fields=['is_started']),
        ]

    class Meta:
        unique_together = ('user', 'content')
        verbose_name = 'Прогресс по курсу'
        verbose_name_plural = 'Прогресс по курсам'

    def __str__(self):
        return f"{self.user} - {self.content} ({'завершен' if self.is_completed else 'в процессе'})"



class UserTestProgress(models.Model):
    """Учет прохождения тестов для каждого пользователя"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='test_progress')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='user_progress')
    score = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    attempts = models.PositiveIntegerField(default=0)
    last_attempt = models.DateTimeField(auto_now=True)
    is_passed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'test')
        verbose_name = 'Прогресс по тесту'
        verbose_name_plural = 'Прогресс по тестам'

    def __str__(self):
        return f"{self.user} - {self.test} ({self.score}%, попыток: {self.attempts})"


class UserAnswer(models.Model):
    """Ответы пользователей на вопросы тестов"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='user_answers')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='user_selections')
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)
    matching_answers = models.JSONField(null=True, blank=True)  # Будет хранить пары {term_id: definition_id}

    class Meta:
        unique_together = ('user', 'question')
        verbose_name = 'Ответ пользователя'
        verbose_name_plural = 'Ответы пользователей'

    def __str__(self):
        return f"{self.user} - {self.question} ({'верно' if self.is_correct else 'неверно'})"

    def save(self, *args, **kwargs):
        # Для вопросов на соответствие проверяем правильность
        if self.question.question_type == 'MT' and self.matching_answers:
            correct = True
            for term_id, definition_id in self.matching_answers.items():
                try:
                    pair = MatchingPair.objects.get(id=term_id, question=self.question)
                    if str(pair.definition) != definition_id:
                        correct = False
                        break
                except MatchingPair.DoesNotExist:
                    correct = False
                    break
            self.is_correct = correct
        # Для обычных вопросов с выбором ответа
        elif self.answer:
            self.is_correct = self.answer.is_correct
        # Для вопросов на дополнение
        elif self.question.question_type == 'FB':
            self.is_correct = (self.answer_text == self.question.correct_answer)

        super().save(*args, **kwargs)

class Video(models.Model):
    content = models.ForeignKey(Content, null=False, on_delete=models.CASCADE)
    step = models.IntegerField()
    url = models.CharField(max_length=255)  # теперь храним только URL

    def __str__(self):
        return f"Видео - {self.step}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['content', 'step'], name='unique_video_step_per_content')
        ]

    def clean(self):
        if Test.objects.filter(content=self.content, step=self.step).exists():
            raise ValidationError(f"Step {self.step} уже используется в Test этого Content.")
        if Subcontent.objects.filter(content=self.content, step=self.step).exists():
            raise ValidationError(f"Step {self.step} уже используется в Subcontent этого Content.")
        super().clean()

    def get_video_ids(self):
        """Извлекает ID1 и ID2 из URL типа https://vkvideo.ru/video-209976560_456240490"""
        try:
            parts = self.url.split('o')
            id_part = parts[-1]  # получаем '209976560_456240490'
            id1, id2 = id_part.split('_')
            return id1, id2
        except Exception:
            return None, None
