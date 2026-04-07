from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Count, Avg, Q
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.cache import cache
from .models import Competency, Content, Subcontent, Answer, Test, Question, UserContentProgress, UserTestProgress, Video
from content_reader.models import Practical, Practical_text, PracticalFile
from .forms import UserUpdateForm
from landing.models import CustomUser

@login_required
def message(request):
    User = get_user_model()
    teachers = User.objects.filter(role='teacher').order_by('last_name', 'first_name')
    return render(request, 'message.html', {'teachers': teachers})

def custom_page_not_found(request, exception):
    return render(request, '404.html', status=404)

@login_required
def docs(request):
    # Получаем работы пользователя с оптимизированными запросами
    practical_works = PracticalFile.objects.filter(
        user=request.user
    ).select_related('practical').only(
        'practical__number',
        'practical__title',
        'score',
        'file',
        'uploaded_at',
        'comment'  # Добавляем поле комментария
    ).order_by('-uploaded_at')

    total_practicals = Practical.objects.count()
    completed_practicals = practical_works.count()
    graded_practicals = practical_works.filter(score__isnull=False).count()

    context = {
        'practical_works': practical_works,
        'total_practicals': total_practicals,
        'completed_practicals': completed_practicals,
        'graded_practicals': graded_practicals,
    }
    return render(request, 'docs.html', context)

@login_required
def check_practical(request):
    practicals = Practical.objects.filter(visible=True).order_by('number')
    students = CustomUser.objects.filter(role='student').select_related('group')
    # Предзагружаем файлы студентов
    students = students.prefetch_related('practicalfile_set')
    score_choices = PracticalFile.SCORE_CHOICES

    context = {
        'practicals': practicals,
        'students': students,
        'score_choices': score_choices,
    }
    return render(request, 'check_practical.html', context)

@login_required
@require_POST
def update_practical_score(request):
    practical_id = request.POST.get('practical_id')
    student_id = request.POST.get('student_id')
    file_id = request.POST.get('file_id')
    score = request.POST.get('score')
    comment = request.POST.get('comment', '')

    try:
        if file_id:
            # Обновляем существующий файл
            practical_file = PracticalFile.objects.get(
                id=file_id,
                practical_id=practical_id,
                user_id=student_id
            )
            practical_file.score = score
            practical_file.comment = comment
            practical_file.save()
        else:
            # Создаем новую запись (если файл еще не загружен)
            practical_file = PracticalFile.objects.create(
                practical_id=practical_id,
                user_id=student_id,
                score=score,
                comment=comment
            )

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def information(request):
    return render(request, 'information.html')

@login_required
def settings_page(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ваши данные успешно обновлены!')
            return redirect('settings')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'settings.html', {'form': form})

@login_required
def dash(request):
    # Создаем уникальный ключ кэша для каждого пользователя
    cache_key = f"dashboard_data_{request.user.id}"
    cached_data = cache.get(cache_key)
    # Если данные в кэше - возвращаем их
    if cached_data:
        return render(request, 'dashboard/index.html', cached_data)
    # 1. Основные данные системы (кэшируем на 15 минут)
    total_courses = cache.get_or_set('total_courses', Content.objects.count, 60 * 15)
    total_tests = cache.get_or_set('total_tests', Test.objects.count, 60 * 15)
    total_practicals = cache.get_or_set('total_practicals', Practical.objects.count, 60 * 15)
    # 2. Получаем данные о прогрессе пользователя (кэшируем на 5 минут)
    user_cache_key = f"user_progress_{request.user.id}"
    user_progress_data = cache.get(user_cache_key)
    if not user_progress_data:
        user_progress_data = {
            'content': UserContentProgress.objects.filter(user=request.user),
            'tests': UserTestProgress.objects.filter(user=request.user),
            'practicals': PracticalFile.objects.filter(user=request.user).values('practical').distinct().count()
        }
        cache.set(user_cache_key, user_progress_data, 60 * 5)
    content_stats = user_progress_data['content'].aggregate(
        total_started=Count('id', filter=Q(is_started=True)),
        total_completed=Count('id', filter=Q(is_completed=True))
    )
    test_stats = user_progress_data['tests'].aggregate(
        passed_tests=Count('id', filter=Q(is_passed=True)),
        avg_score=Avg('score')
    )
    # Рассчитываем проценты
    completed_courses = content_stats.get('total_completed', 0)
    started_courses = content_stats.get('total_started', 0)
    course_progress_percent = safe_divide(completed_courses, total_courses)
    completed_tests = test_stats.get('passed_tests', 0)
    avg_test_score = round(test_stats.get('avg_score', 0) or 0, 1)
    test_progress_percent = safe_divide(completed_tests, total_tests)

    # Общий прогресс
    more_progress_complete = completed_courses + completed_tests
    more_progress_total = total_courses + total_tests
    more_progress_percent = safe_divide(more_progress_complete, more_progress_total)

    # Оптимизированные запросы для тем (кэшируем на 5 минут)
    topics_cache_key = f"user_topics_{request.user.id}"
    topics = cache.get(topics_cache_key)

    if not topics:
        topics = get_topics_with_progress(request.user)
        cache.set(topics_cache_key, topics, 60 * 5)

    # Данные для преподавателей (кэшируем на 5 минут)
    students = []
    if request.user.role == 'teacher':
        students_cache_key = 'students_progress_data'
        students = cache.get(students_cache_key)

        if not students:
            students = get_students_progress(total_courses)
            cache.set(students_cache_key, students, 60 * 5)

    user_tests = UserTestProgress.objects.filter(user=request.user).select_related('test')

    # Подготавливаем данные для отображения тестов
    test_results = []
    for test_progress in user_tests:
        test_results.append({
            'test_name': test_progress.test.title,
            'attempts': test_progress.attempts,
            'score': test_progress.score,
            'status': 'Пройден' if test_progress.is_passed else 'Не пройден',
            'last_attempt': test_progress.last_attempt.strftime('%d.%m.%Y %H:%M'),
        })

    context = {
        # Курсы
        'total_courses': total_courses,
        'completed_courses': completed_courses,
        'started_courses': started_courses,
        'course_progress_percent': course_progress_percent,
        # Тесты
        'total_tests': total_tests,
        'completed_tests': completed_tests,
        'test_progress_percent': test_progress_percent,
        'avg_test_score': avg_test_score,
        # Практические работы
        'total_practicals': total_practicals,
        'completed_practicals': user_progress_data['practicals'],
        # Общий прогресс
        'more_progress_percent': more_progress_percent,
        'more_progress_complete': more_progress_complete,
        'more_progress_total': more_progress_total,
        # Дополнительные данные
        'topics': topics,
        'students': students,
        'is_teacher': request.user.role == 'teacher',
        'test_results': test_results,
        'competency_chart_data': get_competency_chart_data(),
        'activity_chart_data': get_activity_chart_data(),
    }
    # Кэшируем полный контекст на 5 минут
    cache.set(cache_key, context, 60 * 5)

    return render(request, 'dashboard/index.html', context)

def get_competency_chart_data():
    """
    Возвращает данные для диаграммы сформированных компетенций
    Серии данные: «Знать», «Уметь», «Владеть»
    """
    competencies = Competency.objects.all()
    results = []

    for comp in competencies:
        # 1. Расчет "Знать" (процент завершения лекций)
        # Получаем все контенты для этой компетенции
        contents = comp.contents.all()

        # Считаем общее количество пользователей и завершенных лекций
        total_users = CustomUser.objects.count()
        completed = UserContentProgress.objects.filter(
            content__in=contents,
            is_completed=True
        ).count()

        # Рассчитываем процент - сколько пользователей завершило ВСЕ лекции этой компетенции
        know_percent = min((completed / (total_users * contents.count())) * 100 if contents.count() > 0 else 0, 100)

        # 2. Расчет "Уметь" (тесты)
        tests = Test.objects.filter(content__in=contents)
        total_tests = tests.count()

        if total_tests > 0:

            # Количество успешно выполненных тестов (например, > 70%)
            passed_tests = UserTestProgress.objects.filter(
                test__in=tests,
                score__gte=70
            ).count()

            # Общее возможное количество тестов (тесты * пользователи)
            total_possible = total_tests * total_users

            # Процент успешных тестов от общего возможного количества
            skill_percent = (passed_tests / total_possible * 100) if total_possible > 0 else 0
        else:
            skill_percent = 0

        # 3. Расчет "Владеть" (оценки практических работ)
        practicals = comp.practicals.all()
        total_practicals = practicals.count()

        if total_practicals > 0:
            # Количество выполненных практических работ
            completed_practicals = PracticalFile.objects.filter(
                practical__in=practicals
            ).count()

            # Процент выполненных работ от общего возможного (пользователи * работы)
            own_percent = min(
                (completed_practicals / (total_users * total_practicals)) * 100,
                100
            )
        else:
            # Если нет практических работ - 0%
            own_percent = 0

        results.append({
            'code': comp.code,
            'name': comp.name,
            'know': round(know_percent),
            'skill': round(skill_percent),
            'own': round(own_percent)
        })

    return results

def get_activity_chart_data():
    """
    Возвращает данные для диаграммы активности студентов:
    - Лекции: процент завершенных лекций относительно общего возможного
    - Тесты: процент успешных тестов (score >= 70) относительно общего возможного
    - Практические: процент успешных практических работ (оценка >=3) относительно общего возможного
    """
    # Получаем общее количество пользователей
    total_users = CustomUser.objects.count()

    # 1. Лекции (процент завершенных лекций)
    total_content = Content.objects.count()
    if total_content > 0 and total_users > 0:
        completed_content = UserContentProgress.objects.filter(is_completed=True).count()
        lectures_percent = min((completed_content / (total_content * total_users)) * 100, 100)
    else:
        lectures_percent = 0

    # 2. Тесты (процент успешных тестов)
    total_tests = Test.objects.count()
    if total_tests > 0 and total_users > 0:
        passed_tests = UserTestProgress.objects.filter(score__gte=70).count()
        tests_percent = min((passed_tests / (total_tests * total_users)) * 100, 100)
    else:
        tests_percent = 0

    # 3. Практические (процент успешных практических работ)
    total_practicals = Practical.objects.count()
    if total_practicals > 0 and total_users > 0:
        passed_practicals = PracticalFile.objects.filter(score__gte=3).count()
        practical_percent = min((passed_practicals / (total_practicals * total_users)) * 100, 100)
    else:
        practical_percent = 0

    return {
        'lectures': round(lectures_percent),
        'tests': round(tests_percent),
        'practical': round(practical_percent)
    }

def safe_divide(numerator, denominator):
    return int((numerator / denominator) * 100) if denominator and denominator > 0 else 0

def get_topics_with_progress(user):
    """Оптимизированная версия без конфликта имен"""
    contents = Content.objects.only('id', 'title', 'slug')
    user_progress = {
        p.content_id: p
        for p in UserContentProgress.objects.filter(
            user=user,
            content__in=contents
        ).select_related('content')
    }
    return [
        {
            'title': content.title,
            'status': get_progress_status(user_progress.get(content.id)),
        }
        for content in contents
    ]

def get_progress_status(progress):
    if not progress:
        return 'not_started'
    return 'completed' if progress.is_completed else 'in_progress'

def get_students_progress(total_courses):
    students = CustomUser.objects.filter(
        role='student'
    ).select_related('group').prefetch_related(
        Prefetch(
            'content_progress',
            queryset=UserContentProgress.objects.filter(is_completed=True),
            to_attr='completed_courses'
        )
    )

    return [
        {
            'username': student.username,
            'group': student.group.name if student.group else '',
            'progress': safe_divide(len(student.completed_courses), total_courses),
        }
        for student in students
    ]

@login_required
def learn(request):
    contents = Content.objects.filter(visible=True)
    context = {
        "contents": contents,
        "title": "Главная страница блога",
        "description": "Описание для главной страницы",
    }
    return render(request, 'dashboard/learn.html', context)

@login_required
def practical(request):
    contents = Practical.objects.filter(visible='1')
    context = {
        "contents": contents,
        "title": "Главная страница блога",
        "description": "Описание для главной страницы",
    }
    return render(request, 'dashboard/practical.html', context)

@login_required
def step_redirect(request, slug):
    # Получаем объект контента по slug
    post = get_object_or_404(Content, slug=slug)
    # Находим первую страницу для этого контента (по шагу step=1)
    first_subcontent = Subcontent.objects.filter(content=post).order_by('step').first()
    if first_subcontent:
        return redirect('preview', slug=post.slug, step=first_subcontent.step)
    else:
        # Если нет страниц, редиректим на сам контент
        return redirect('preview', slug=post.slug)

@login_required
def preview(request, slug, step):
    CContent = get_object_or_404(Content, slug=slug)
    # Получаем все страницы контента
    all_steps = []
    subcontents = Subcontent.objects.filter(content=CContent).values_list('step', flat=True)
    tests = Test.objects.filter(content=CContent).values_list('step', flat=True)
    videos = Video.objects.filter(content=CContent).values_list('step', flat=True)
    all_steps.extend([('text', s) for s in subcontents])
    all_steps.extend([('test', t) for t in tests])
    all_steps.extend([('video', v) for v in videos])
    all_steps.sort(key=lambda x: x[1])
    # Обработка прогресса пользователя
    if request.user.is_authenticated:
        content_progress, created = UserContentProgress.objects.get_or_create(
            user=request.user,
            content=CContent,
            defaults={'is_started': True}
        )
        if not created and not content_progress.is_started:
            content_progress.is_started = True
            content_progress.save()
        if all_steps and step == all_steps[-1][1]:
            content_progress.is_completed = True
            content_progress.save()
    context = {'Content': CContent, 'steps': all_steps, 'current_step': step}
    try:
        SSubcontent = get_object_or_404(Subcontent, content__slug=slug, step=step)
        context.update({
            'Subcontent': SSubcontent,
            'is_text': True,
        })
    except Http404:
        try:
            STest = get_object_or_404(Test, content__slug=slug, step=step)
            context.update({
                'Test': STest,
                'is_test': True,
                'questions': Question.objects.filter(test=STest).prefetch_related('answers')
            })
        except Http404:
            SVideo = get_object_or_404(Video, content__slug=slug, step=step)
            context.update({
                'Video': SVideo,
                'is_video': True
            })

    return render(request, 'dashboard/lection/preview.html', context)

@login_required
def check_test(request, test_id):
    if request.method == 'POST':
        test = get_object_or_404(Test, pk=test_id)
        questions = Question.objects.filter(test=test)
        content = test.content

        results = []
        total_questions = questions.count()
        correct_answers = 0

        test_progress, created = UserTestProgress.objects.get_or_create(
            user=request.user,
            test=test
        )
        test_progress.attempts += 1

        for question in questions:
            if question.question_type == 'MC':
                selected_answer_id = request.POST.get(f'question_{question.id}')
                is_correct = False
                if selected_answer_id:
                    try:
                        selected_answer = Answer.objects.get(pk=selected_answer_id)
                        is_correct = selected_answer.is_correct
                    except Answer.DoesNotExist:
                        is_correct = False
            elif question.question_type == 'FB':
                user_answer = request.POST.get(f'question_{question.id}', '').strip()
                is_correct = user_answer.lower() == question.correct_answer.lower()
            elif question.question_type == 'MT':
                # Проверка соответствия терминов и определений
                user_matches = request.POST.getlist(f'question_{question.id}')
                correct_pairs = {(str(pair.id), str(pair.id)) for pair in question.matching_pairs.all()}

                user_correct = 0
                for match in user_matches:
                    term_id, definition_id = match.split('-', 1)
                    if (term_id, definition_id) in correct_pairs:
                        user_correct += 1

                is_correct = user_correct == len(correct_pairs)

            if is_correct:
                correct_answers += 1

            results.append({
                'question': question.text,
                'is_correct': is_correct,
                'correct_answer': question.correct_answer if question.question_type == 'FB' else None
            })

        score = int((correct_answers / total_questions) * 100) if total_questions > 0 else 0
        test_progress.score = score
        test_progress.is_passed = score >= 80
        test_progress.save()

        check_course_completion(request.user, content)

        return JsonResponse({
            'success': True,
            'results': results,
            'score': score,
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'is_passed': test_progress.is_passed
        })

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def check_course_completion(user, content):
    # Получаем все тесты для этого курса
    tests = Test.objects.filter(content=content)
    # Проверяем, все ли тесты пройдены (score >= 80)
    all_tests_passed = True
    for test in tests:
        try:
            progress = UserTestProgress.objects.get(user=user, test=test)
            if not progress.is_passed:
                all_tests_passed = False
                break
        except UserTestProgress.DoesNotExist:
            all_tests_passed = False
            break
    # Если все тесты пройдены, отмечаем курс как завершенный
    if all_tests_passed:
        content_progress, created = UserContentProgress.objects.get_or_create(
            user=user,
            content=content
        )
        if not content_progress.is_completed:
            content_progress.is_completed = True
            content_progress.completed_at = timezone.now()
            content_progress.save()

@login_required
def zapret(request):
    return render(request, 'dashboard/zapret.html')

@login_required
def practical_step_redirect(request, slug):
    # Получаем объект практики по slug
    practical = get_object_or_404(Practical, slug=slug)
    # Находим первую страницу для этой практики (по шагу step=1)
    first_step = Practical_text.objects.filter(practical=practical).order_by('step').first()
    if first_step:
        return redirect('practical_step_preview', slug=practical.slug, step=first_step.step)
    else:
        return redirect('practical_step_preview', slug=practical.slug)

@login_required
def practical_step_preview(request, slug, step):
    practical = get_object_or_404(Practical, slug=slug)
    step_content = get_object_or_404(Practical_text, practical=practical, step=step)
    all_steps = list(Practical_text.objects.filter(
        practical=practical
    ).order_by('step').values_list('step', flat=True))
    context = {
        'Practical': practical,
        'StepContent': step_content,
        'steps': [('text', s) for s in all_steps],
        'current_step': step,
        'is_Stepcontent': True,
    }
    # Обработка прогресса пользователя
    if request.user.is_authenticated:
        user_file = PracticalFile.objects.filter(
            practical=practical,
            step=step,
            user=request.user
        ).first()
        context['user_file'] = user_file

    return render(request, 'dashboard/practical/preview.html', context)


@csrf_exempt
def upload_practical_file(request, slug, step):
    if request.method == 'POST' and request.FILES.get('file'):
        practical = get_object_or_404(Practical, slug=slug)
        old_file = PracticalFile.objects.filter(
            practical=practical,
            step=step,
            user=request.user
        ).first()
        if old_file:
            old_file.delete()
        new_file = PracticalFile(
            practical=practical,
            step=step,
            user=request.user,
            file=request.FILES['file']
        )
        new_file.save()
        return JsonResponse({
            'success': True,
            'file_url': new_file.file.url,
            'filename': new_file.filename()
        })
    elif request.method == 'DELETE':
        practical = get_object_or_404(Practical, slug=slug)
        file = PracticalFile.objects.filter(
            practical=practical,
            step=step,
            user=request.user
        ).first()
        if file:
            file.delete()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'File not found'}, status=404)

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)