import os
from django.core.files.storage import FileSystemStorage
from django.core.validators import FileExtensionValidator
from landing.models import CustomUser
from learning.models import Competency
from django.urls import reverse
from django.db import models
from django.utils.text import slugify
from transliterate import translit

class Practical(models.Model):
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
        related_name='practicals',
        verbose_name="Компетенции"
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = translit(self.title, 'ru', reversed=True)
            base_slug = slugify(base_slug)
            slug = base_slug
            counter = 1
            # Проверка на уникальность
            while Practical.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('practical_step_preview', kwargs={'slug': self.slug})

    def get_absolute_url_edit(self):
        return reverse('practical_edit', kwargs={'slug': self.slug})

    def __str__(self):
        return f"{self.number} - {self.title}"

class Practical_text(models.Model):
    practical = models.ForeignKey(Practical, null=False, on_delete=models.CASCADE)
    step = models.IntegerField(default=1)
    title = models.CharField(max_length=250)
    body = models.TextField()
    download = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} - Шаг {self.step}"

    def get_absolute_url(self):
        return reverse('practical_step_preview', kwargs={
            'slug': self.practical.slug,
            'step': self.step
        })

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['practical', 'step'], name='unique_step_per_practical')
        ]
        ordering = ['step']

class Practical_work(models.Model):
    practical = models.ForeignKey(Practical, null=False, on_delete=models.CASCADE)
    step = models.IntegerField(default=1)
    task = models.TextField(verbose_name="Текст задания")
    hint = models.TextField(verbose_name="Подсказка", blank=True)
    expected_output = models.CharField(
        verbose_name="Ожидаемый вывод",
        max_length=255,
        blank=True
    )

    def save(self, *args, **kwargs):
        if self.expected_output:
            self.expected_output = self.expected_output.lower().replace(" ", "")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Практическая работа - Шаг {self.step}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['practical', 'step'], name='unique_practical_work_step')
        ]
        ordering = ['step']
        verbose_name = 'Практический редактор'
        verbose_name_plural = 'Практические редакторы'

class PracticalFileStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        if self.exists(name):
            os.remove(os.path.join(self.location, name))
        return name

class PracticalFile(models.Model):
    practical = models.ForeignKey(Practical, on_delete=models.CASCADE)
    step = models.IntegerField()
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    SCORE_CHOICES = [(i, str(i)) for i in range(2, 6)]  # [(2, "2"), (3, "3"), ...]
    score = models.IntegerField(choices=SCORE_CHOICES, null=True, blank=True)
    file = models.FileField(
        upload_to='practical_files/',
        storage=PracticalFileStorage(),
        validators=[FileExtensionValidator(allowed_extensions=['doc', 'docx', 'docs', 'txt'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(verbose_name="Комментарий", blank=True, null=True)

    def __str__(self):
        return f"Файл для {self.practical.title} (шаг {self.step})"

    def filename(self):
        return os.path.basename(self.file.name)

    class Meta:
        unique_together = ('practical', 'step', 'user')