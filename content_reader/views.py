from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from learning.models import Competency, Content, Subcontent, Answer, Test, Question, Video, MatchingPair
from .models import Practical, Practical_text, Practical_work
from django.http import JsonResponse
from django.core.exceptions import ValidationError
import json, re


# Функция проверки роли преподователя
def check_teacher_role(user):
    if user.role != 'teacher':
        return redirect('zapret')
    return None  # Если роль - преподаватель, то возвращаем None (не делаем перенаправления)

# Главная страница редактора
@login_required
def editor_course(request):
    redirect_response = check_teacher_role(request.user)
    if redirect_response:
        return redirect_response

    contents = Content.objects.filter
    context = {
        "contents": contents,
        "title": "Главная страница блога",
        "description": "Описание для главной страницы",
    }
    return render(request, 'editor.html', context)

# Страница создания нового обучаающего блока
@login_required
def create(request):
    redirect_response = check_teacher_role(request.user)
    if redirect_response:
        return redirect_response

    error = None
    if request.method == 'POST':
        title = request.POST.get('title')
        number = request.POST.get('number')
        description = request.POST.get('description')
        image = request.FILES.get('image')

        if Content.objects.filter(number=number).exists():
            error = f'Тема с номером {number} уже существует!'
        else:
            # Создание Content — slug сгенерируется автоматически
            content = Content.objects.create(
                title=title,
                number=number,
                description=description,
                image=image,
                owner=request.user
            )
            # После сохранения у объекта уже есть slug
            return redirect('edit_course', slug=content.slug)

    return render(request, 'lection/create.html', {'error': error})

# Страница редактирования существующих обучающих блоков
@login_required
def content_edit(request, slug):
    redirect_response = check_teacher_role(request.user)
    if redirect_response:
        return redirect_response

    content = get_object_or_404(Content, slug=slug)
    error = None
    all_competencies = Competency.objects.all()

    if request.method == 'POST' and 'delete' not in request.POST:
        title = request.POST.get('title')
        number = request.POST.get('number')
        description = request.POST.get('description')
        image = request.FILES.get('image')
        selected_competencies = request.POST.getlist('competencies')

        if Content.objects.filter(number=number).exclude(slug=content.slug).exists():
            error = f'Тема с номером {number} уже существует!'
        else:
            content.title = title
            content.number = number
            content.description = description

            if image:
                content.image = image

            content.save()
            content.competencies.clear()
            for comp_id in selected_competencies:
                competency = Competency.objects.get(id=comp_id)
                content.competencies.add(competency)

            # Перенаправление на редактирование курса
            return redirect('edit_course', slug=content.slug)

    if request.method == 'POST' and 'delete' in request.POST:
        # Удаление всех зависимых объектов
        content.subcontent_set.all().delete()
        content.delete()
        messages.success(request, f'Тема "{content.title}" успешно удалена.')
        return redirect('editor')

    context = {
        'post': content,
        'error': error,
        'all_competencies': all_competencies,
        'selected_competencies': [c.id for c in content.competencies.all()]
    }
    return render(request, 'lection/edit.html', context)

# Страница редактирования содержимого обучающих блоков
@login_required
def edit_course(request, slug):
    redirect_response = check_teacher_role(request.user)
    if redirect_response:
        return redirect_response

    content = get_object_or_404(Content, slug=slug)

    if request.method == 'GET':
        subcontents = Subcontent.objects.filter(content=content).order_by('step')
        tests = Test.objects.filter(content=content).order_by('step').prefetch_related('questions__answers')
        videos = Video.objects.filter(content=content).order_by('step')
        all_steps = []
        all_steps.extend([('text', s.step) for s in Subcontent.objects.filter(content=content)])
        all_steps.extend([('test', t.step) for t in Test.objects.filter(content=content)])
        all_steps.extend([('video', v.step) for v in Video.objects.filter(content=content)])
        all_steps.sort(key=lambda x: x[1])

        return render(request, 'lection/create_step2.html', {
            'content': content,
            'subcontents': subcontents,
            'tests': tests,
            'steps': all_steps,
            'videos': videos
        })

    # Обработка AJAX запросов
    elif request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Обработка удаления блока
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                if data.get('action') == 'delete':
                    block_type = data.get('type')
                    block_id = data.get('id')

                    if block_type == 'text':
                        Subcontent.objects.filter(id=block_id, content=content).delete()
                    elif block_type == 'test':
                        Test.objects.filter(id=block_id, content=content).delete()
                    elif block_type == 'video':
                        Video.objects.filter(id=block_id, content=content).delete()

                    return JsonResponse({'success': True})

            # Обработка сохранения блока
            block_type = request.POST.get('type')
            block_id = request.POST.get('id')

            if block_type == 'text':
                # Валидация данных
                title = request.POST.get('title', '').strip()
                body = request.POST.get('body', '').strip()
                step = request.POST.get('step')

                if not title or not body or not step:
                    return JsonResponse({'success': False, 'error': 'Все поля обязательны для заполнения'})

                try:
                    step = int(step)
                except ValueError:
                    return JsonResponse({'success': False, 'error': 'Номер страницы должен быть числом'})

                # Проверка на уникальность step
                if Test.objects.filter(content=content, step=step).exists():
                    return JsonResponse({'success': False, 'error': f'Step {step} уже используется в тесте'})

                # Сохранение или обновление Subcontent
                if block_id:
                    subcontent = get_object_or_404(Subcontent, id=block_id, content=content)
                    subcontent.title = title
                    subcontent.body = body
                    subcontent.step = step
                    subcontent.save()
                else:
                    subcontent = Subcontent.objects.create(
                        content=content,
                        title=title,
                        body=body,
                        step=step
                    )

                return JsonResponse({'success': True, 'id': subcontent.id})


            elif block_type == 'video':

                video_url = request.POST.get('title', '').strip()

                step = request.POST.get('step')

                if not video_url or not step:
                    return JsonResponse({'success': False, 'error': 'Все поля обязательны для заполнения'})

                try:

                    step = int(step)

                    # Проверяем валидность URL видео

                    if not video_url.startswith('https://vkvideo.ru/video') or '_' not in video_url:
                        return JsonResponse({'success': False, 'error': 'Неверный формат ссылки на видео'})

                except ValueError:

                    return JsonResponse({'success': False, 'error': 'Номер страницы должен быть числом'})

                # Проверка на уникальность step

                if Test.objects.filter(content=content, step=step).exists():
                    return JsonResponse({'success': False, 'error': f'Step {step} уже используется в тесте'})

                if Subcontent.objects.filter(content=content, step=step).exists():
                    return JsonResponse({'success': False, 'error': f'Step {step} уже используется в текстовом блоке'})

                # Сохранение или обновление Video

                if block_id:

                    video = get_object_or_404(Video, id=block_id, content=content)

                    video.step = step

                    video.url = video_url  # теперь сохраняем только URL

                    video.save()

                else:

                    video = Video.objects.create(

                        content=content,

                        step=step,

                        url=video_url  # теперь сохраняем только URL

                    )

                return JsonResponse({'success': True, 'id': video.id})

            elif block_type == 'test':
                title = request.POST.get('title', '').strip()
                step = request.POST.get('step')
                questions_data = request.POST.get('questions', '[]')
                # Валидация
                if not title:
                    return JsonResponse({'success': False, 'error': 'Введите название теста'})
                try:
                    step = int(step)
                    questions = json.loads(questions_data)
                except (ValueError, TypeError) as e:
                    return JsonResponse({'success': False, 'error': f'Ошибка в данных: {str(e)}'})
                # Проверка вопросов
                if len(questions) == 0:
                    return JsonResponse({'success': False, 'error': 'Добавьте хотя бы один вопрос'})
                for q in questions:
                    if not q.get('text', '').strip():
                        return JsonResponse({'success': False, 'error': 'Все вопросы должны содержать текст'})
                    if q.get('type') == 'MC':
                        valid_answers = [a for a in q.get('answers', []) if a.get('text', '').strip()]
                        if len(valid_answers) < 2:
                            return JsonResponse(
                                {'success': False, 'error': 'Каждый вопрос должен иметь минимум 2 ответа'})
                        correct_answers = [a for a in valid_answers if a.get('is_correct', False)]
                        if len(correct_answers) != 1:
                            return JsonResponse(
                                {'success': False, 'error': 'Каждый вопрос должен иметь ровно 1 правильный ответ'})
                        # Для вопросов на дополнение
                    elif q.get('type') == 'FB':
                        if not q.get('correct_answer', '').strip():
                            return JsonResponse(
                                {'success': False, 'error': 'Для вопросов на дополнение укажите правильный ответ'})
                    elif q.get("type") == "MT":
                        pairs = q.get("pairs", [])
                        if len(pairs) < 2:
                            return JsonResponse(
                                {"success": False, "error": "Вопрос на соответствие должен содержать минимум 2 пары"}
                            )
                        for pair in pairs:
                            if not pair.get("term", "").strip() or not pair.get("definition", "").strip():
                                return JsonResponse(
                                    {"success": False,
                                     "error": "Все пары соответствия должны содержать и термин, и определение"}
                                )
                # Создание/обновление теста
                with transaction.atomic():
                    if block_id:
                        test = get_object_or_404(Test, id=block_id, content=content)
                        test.title = title
                        test.step = step
                        test.save()
                    else:
                        test = Test.objects.create(
                            content=content,
                            title=title,
                            step=step
                        )

                    # Обновляем вопросы и ответы
                    test.questions.all().delete()
                    for q_data in questions:
                        question = Question.objects.create(
                            test=test,
                            text=q_data['text'].strip(),
                            question_type=q_data.get('type', 'MC'),
                            correct_answer=q_data.get('correct_answer', '') if q_data.get('type') == 'FB' else None
                        )

                        if q_data.get('type') == 'MC':
                            for a_data in q_data['answers']:
                                if a_data['text'].strip():
                                    Answer.objects.create(
                                        question=question,
                                        text=a_data['text'].strip(),
                                        is_correct=a_data.get('is_correct', False)
                                    )
                        elif q_data.get("type") == "MT":
                            for pair in q_data.get("pairs", []):
                                if pair["term"].strip() and pair["definition"].strip():
                                    MatchingPair.objects.create(
                                        question=question,
                                        term=pair["term"].strip(),
                                        definition=pair["definition"].strip(),
                                        order=q_data.get("pairs", []).index(pair)
                                    )
                return JsonResponse({'success': True, 'id': test.id})
            return JsonResponse({'success': False, 'error': 'Invalid block type'})
        except ValidationError as e:
            return JsonResponse({'success': False, 'error': str(e)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def get_test_questions(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    questions = []

    # Используем prefetch_related для оптимизации запросов
    for question in test.questions.all().prefetch_related('answers', 'matching_pairs'):
        question_data = {
            'id': question.id,
            'text': question.text,
            'type': question.question_type,
        }

        if question.question_type == 'MC':
            question_data['answers'] = [{
                'id': a.id,
                'text': a.text,
                'is_correct': a.is_correct
            } for a in question.answers.all()]
        elif question.question_type == 'FB':
            question_data['correct_answer'] = question.correct_answer
        elif question.question_type == 'MT':
            # Добавляем пары соответствия, сортируя по полю order
            question_data['pairs'] = [{
                'id': p.id,
                'term': p.term,
                'definition': p.definition
            } for p in question.matching_pairs.all().order_by('order')]

        questions.append(question_data)

    return JsonResponse({'questions': questions})

#Редактор практических работ
@login_required
def practical_editor(request):
    redirect_response = check_teacher_role(request.user)
    if redirect_response:
        return redirect_response

    contents = Practical.objects.filter
    context = {
        "contents": contents,
        "title": "Главная страница блога",
        "description": "Описание для главной страницы",
    }
    return render(request, 'practical_editor.html', context)

#Страница создания новой практической работы
@login_required
def practical_create(request):
    redirect_response = check_teacher_role(request.user)
    if redirect_response:
        return redirect_response

    error = None
    if request.method == 'POST':
        title = request.POST.get('title')
        number = request.POST.get('number')
        description = request.POST.get('description')
        image = request.FILES.get('image')

        if Practical.objects.filter(number=number).exists():
            error = f'Тема с номером {number} уже существует!'
        else:
            # Создание Content — slug сгенерируется автоматически
            content = Practical.objects.create(
                title=title,
                number=number,
                description=description,
                image=image,
                owner=request.user
            )
            # После сохранения у объекта уже есть slug
            return redirect('more_practical_edit', slug=content.slug)

    return render(request, 'practical_editor/create.html', {'error': error})

#Редактирование практических работ
@login_required
def practical_edit(request, slug):
    redirect_response = check_teacher_role(request.user)
    if redirect_response:
        return redirect_response

    content = get_object_or_404(Practical, slug=slug)
    error = None
    all_competencies = Competency.objects.all()

    if request.method == 'POST' and 'delete' not in request.POST:
        title = request.POST.get('title')
        number = request.POST.get('number')
        description = request.POST.get('description')
        image = request.FILES.get('image')
        selected_competencies = request.POST.getlist('competencies')

        if Practical.objects.filter(number=number).exclude(slug=content.slug).exists():
            error = f'Тема с номером {number} уже существует!'
        else:
            content.title = title
            content.number = number
            content.description = description
            content.competencies.clear()
            for comp_id in selected_competencies:
                competency = Competency.objects.get(id=comp_id)
                content.competencies.add(competency)

            if image:
                content.image = image

            content.save()
            # Перенаправление на редактирование курса
            return redirect('more_practical_edit', slug=content.slug)

    if request.method == 'POST' and 'delete' in request.POST:
        # Удаление всех зависимых объектов
        # content.subcontent_set.all().delete()
        content.delete()
        messages.success(request, f'Тема "{content.title}" успешно удалена.')
        return redirect('practical_editor')

    context = {
        'post': content,
        'error': error,
        'all_competencies': all_competencies,
        'selected_competencies': [c.id for c in content.competencies.all()]
    }
    return render(request, 'practical_editor/edit.html', context)


#Страница редактирования содержимого практики
@login_required
def edit_practical_more(request, slug):
    redirect_response = check_teacher_role(request.user)
    if redirect_response:
        return redirect_response

    practical = get_object_or_404(Practical, slug=slug)

    if request.method == 'GET':
        all_steps = []
        all_steps.extend([('text', s.step) for s in Practical_text.objects.filter(practical=practical)])
        all_steps.extend([('work', s.step) for s in Practical_work.objects.filter(practical=practical)])
        all_steps.sort(key=lambda x: x[1])

        texts = Practical_text.objects.filter(practical=practical).order_by('step')
        works = Practical_work.objects.filter(practical=practical).order_by('step')

        return render(request, 'practical_editor/create_step2.html', {
            'practical': practical,
            'steps': all_steps,
            'texts': texts,
            'works': works
        })

    elif request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Удаление блока
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                if data.get('action') == 'delete':
                    step_id = data.get('id')
                    block_type = data.get('type')

                    if block_type == 'text':
                        Practical_text.objects.filter(id=step_id, practical=practical).delete()
                    elif block_type == 'work':
                        Practical_work.objects.filter(id=step_id, practical=practical).delete()

                    return JsonResponse({'success': True})

            # Определяем тип блока
            block_type = request.POST.get('type')
            block_id = request.POST.get('id')
            step = request.POST.get('step')

            if not step:
                return JsonResponse({'success': False, 'error': 'Номер шага обязателен'})

            try:
                step = int(step)
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Номер шага должен быть числом'})

            if block_type == 'text':
                # Обработка текстового блока
                title = request.POST.get('title', '').strip()
                body = request.POST.get('body', '').strip()
                download = request.POST.get('download', 'off') == 'on'  # Получаем значение чекбокса

                if not title or not body:
                    return JsonResponse({'success': False, 'error': 'Все поля обязательны для заполнения'})

                # Проверка уникальности step
                if not block_id and Practical_text.objects.filter(practical=practical, step=step).exists():
                    return JsonResponse({'success': False, 'error': f'Шаг {step} уже существует'})

                if block_id:
                    step_obj = get_object_or_404(Practical_text, id=block_id, practical=practical)
                    step_obj.title = title
                    step_obj.body = body
                    step_obj.step = step
                    step_obj.download = download  # Обновляем поле download
                    step_obj.save()
                else:
                    step_obj = Practical_text.objects.create(
                        practical=practical,
                        title=title,
                        body=body,
                        step=step,
                        download=download  # Устанавливаем поле download при создании
                    )

            elif block_type == 'work':
                # Обработка блока практической работы
                task = request.POST.get('task', '').strip()
                hint = request.POST.get('hint', '').strip()
                expected_output = request.POST.get('expected_output', '').strip()

                if not task:
                    return JsonResponse({'success': False, 'error': 'Поле "Текст задания" обязательно'})

                # Проверка уникальности step
                if not block_id and Practical_work.objects.filter(practical=practical, step=step).exists():
                    return JsonResponse({'success': False, 'error': f'Шаг {step} уже существует'})

                if block_id:
                    step_obj = get_object_or_404(Practical_work, id=block_id, practical=practical)
                    step_obj.task = task
                    step_obj.hint = hint
                    step_obj.expected_output = expected_output
                    step_obj.step = step
                    step_obj.save()
                else:
                    step_obj = Practical_work.objects.create(
                        practical=practical,
                        task=task,
                        hint=hint,
                        expected_output=expected_output,
                        step=step
                    )

            else:
                return JsonResponse({'success': False, 'error': 'Неизвестный тип блока'})

            return JsonResponse({'success': True, 'id': step_obj.id, 'type': block_type})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Неверный запрос'})
