from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Course, Enrollment
from .forms import SignUpForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! You can now sign in.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignUpForm()
    return render(request, 'users/signup.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


@login_required(login_url='login')
def dashboard_view(request):
    enrolled_courses = Enrollment.objects.filter(student=request.user).select_related('course')
    enrolled_ids = enrolled_courses.values_list('course_id', flat=True)
    available_courses = Course.objects.filter(is_active=True).exclude(id__in=enrolled_ids)[:3]
    context = {
        'enrolled_courses': enrolled_courses,
        'available_courses': available_courses,
        'enrolled_count': enrolled_courses.count(),
        'completed_count': enrolled_courses.filter(progress=100).count(),
        'active_page': 'dashboard',
    }
    return render(request, 'users/dashboard.html', context)


@login_required(login_url='login')
def courses_view(request):
    category = request.GET.get('category', '')
    courses = Course.objects.filter(is_active=True)
    if category:
        courses = courses.filter(category=category)
    enrolled_ids = list(Enrollment.objects.filter(student=request.user).values_list('course_id', flat=True))
    context = {
        'courses': courses,
        'enrolled_ids': enrolled_ids,
        'selected_category': category,
        'categories': Course.CATEGORY_CHOICES,
        'active_page': 'courses',
    }
    return render(request, 'users/courses.html', context)


@login_required(login_url='login')
def course_detail_view(request, course_id):
    course = get_object_or_404(Course, id=course_id, is_active=True)
    enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    context = {
        'course': course,
        'enrollment': enrollment,
        'active_page': 'courses',
    }
    return render(request, 'users/course_detail.html', context)


@login_required(login_url='login')
def enroll_view(request, course_id):
    course = get_object_or_404(Course, id=course_id, is_active=True)
    enrollment, created = Enrollment.objects.get_or_create(student=request.user, course=course)
    if created:
        messages.success(request, f'Successfully enrolled in "{course.title}"!')
    else:
        messages.info(request, f'You are already enrolled in "{course.title}".')
    return redirect('course_detail', course_id=course_id)


@login_required(login_url='login')
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    return render(request, 'users/profile.html', {'user': request.user, 'active_page': 'profile'})
