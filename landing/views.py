from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import SignUpForm, LoginForm
from .models import Group


def test(request):
    return render(request, 'test.html')

# Create your views here.
def landing(request):
    return redirect('login')
def fix_urls(request):
    return redirect('login')
def loginform(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = LoginForm(data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)  # Проверяем учетные данные
            if user is not None:
                login(request, user)  # Выполняем вход
                return redirect('home')  # Перенаправляем на главную страницу
    return render(request, 'start/login.html', {'form': form})

def reg(request):
    if request.user.is_authenticated:
        return redirect('home')  # Убедитесь, что 'home' правильно определен в urls.py

    groups = Group.objects.all()

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            group_name = request.POST.get('group')
            if group_name:
                try:
                    group = Group.objects.get(name=group_name)
                    user.group = group
                except Group.DoesNotExist:
                    pass

            user.save()
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()

    return render(request, 'start/reg.html', {
        'form': form,
        'groups': groups
    })

def page_not_found(request):
    return render(request, 'start/reg.html')