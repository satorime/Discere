import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Course, Enrollment, Deck, Flashcard, FlashcardProgress, Quiz, QuizQuestion, QuizAttempt
from .forms import SignUpForm
from . import ai_utils


# ──────────────────────────────────────────────
# Auth Views
# ──────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data.get('username'),
                password=form.cleaned_data.get('password')
            )
            if user is not None:
                login(request, user)
                return redirect('dashboard')
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


# ──────────────────────────────────────────────
# Dashboard & Courses
# ──────────────────────────────────────────────

@login_required(login_url='login')
def dashboard_view(request):
    enrolled_courses = Enrollment.objects.filter(student=request.user).select_related('course')
    enrolled_ids = enrolled_courses.values_list('course_id', flat=True)
    available_courses = Course.objects.filter(is_active=True).exclude(id__in=enrolled_ids)[:3]
    recent_decks = Deck.objects.filter(created_by=request.user).order_by('-updated_at')[:3]
    context = {
        'enrolled_courses': enrolled_courses,
        'available_courses': available_courses,
        'enrolled_count': enrolled_courses.count(),
        'completed_count': enrolled_courses.filter(progress=100).count(),
        'deck_count': Deck.objects.filter(created_by=request.user).count(),
        'recent_decks': recent_decks,
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
    context = {'course': course, 'enrollment': enrollment, 'active_page': 'courses'}
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


# ──────────────────────────────────────────────
# Deck Views
# ──────────────────────────────────────────────

@login_required(login_url='login')
def decks_view(request):
    decks = Deck.objects.filter(created_by=request.user).order_by('-updated_at')
    context = {'decks': decks, 'active_page': 'flashcards'}
    return render(request, 'users/decks.html', context)


@login_required(login_url='login')
def create_deck_view(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        mode = request.POST.get('mode', 'manual')

        if not title:
            messages.error(request, 'Deck title is required.')
            return render(request, 'users/create_deck.html', {'active_page': 'flashcards'})

        if mode == 'ai':
            text_input = request.POST.get('text_input', '').strip()
            pdf_file = request.FILES.get('pdf_file')
            num_cards = int(request.POST.get('num_cards', 10))
            num_cards = max(5, min(num_cards, 20))

            # Extract text from PDF or use text input
            source_text = ''
            if pdf_file:
                try:
                    source_text = ai_utils.extract_pdf_text(pdf_file)
                except Exception:
                    messages.error(request, 'Could not read the PDF. Please try again or paste text instead.')
                    return render(request, 'users/create_deck.html', {'active_page': 'flashcards'})
            elif text_input:
                source_text = text_input

            if not source_text:
                messages.error(request, 'Please upload a PDF or paste some text.')
                return render(request, 'users/create_deck.html', {'active_page': 'flashcards'})

            # Generate flashcards with AI
            try:
                cards_data = ai_utils.generate_flashcards(source_text, num_cards)
            except Exception as e:
                messages.error(request, f'AI generation failed: {str(e)}. Check your GROQ_API_KEY.')
                return render(request, 'users/create_deck.html', {'active_page': 'flashcards'})

            deck = Deck.objects.create(title=title, description=description, created_by=request.user)
            for card in cards_data:
                if card.get('front') and card.get('back'):
                    Flashcard.objects.create(deck=deck, front=card['front'], back=card['back'])
            messages.success(request, f'Deck "{title}" created with {deck.card_count()} flashcards!')
        else:
            # Manual mode — create blank deck, user adds cards on deck detail page
            deck = Deck.objects.create(title=title, description=description, created_by=request.user)
            messages.success(request, f'Deck "{title}" created! Add flashcards below.')

        return redirect('deck_detail', deck_id=deck.id)

    return render(request, 'users/create_deck.html', {'active_page': 'flashcards'})


@login_required(login_url='login')
def deck_detail_view(request, deck_id):
    deck = get_object_or_404(Deck, id=deck_id, created_by=request.user)
    flashcards = deck.flashcards.all()
    quizzes = deck.quizzes.all()
    mastered = deck.mastered_count(request.user)
    context = {
        'deck': deck,
        'flashcards': flashcards,
        'quizzes': quizzes,
        'mastered': mastered,
        'active_page': 'flashcards',
    }
    return render(request, 'users/deck_detail.html', context)


@login_required(login_url='login')
def delete_deck_view(request, deck_id):
    deck = get_object_or_404(Deck, id=deck_id, created_by=request.user)
    deck.delete()
    messages.success(request, f'Deck "{deck.title}" deleted.')
    return redirect('decks')


@login_required(login_url='login')
@require_POST
def add_flashcard_view(request, deck_id):
    deck = get_object_or_404(Deck, id=deck_id, created_by=request.user)
    front = request.POST.get('front', '').strip()
    back = request.POST.get('back', '').strip()
    if front and back:
        Flashcard.objects.create(deck=deck, front=front, back=back)
        messages.success(request, 'Flashcard added.')
    else:
        messages.error(request, 'Both front and back are required.')
    return redirect('deck_detail', deck_id=deck_id)


@login_required(login_url='login')
def delete_flashcard_view(request, card_id):
    card = get_object_or_404(Flashcard, id=card_id, deck__created_by=request.user)
    deck_id = card.deck_id
    card.delete()
    messages.success(request, 'Flashcard deleted.')
    return redirect('deck_detail', deck_id=deck_id)


# ──────────────────────────────────────────────
# Study (Flashcard) Views
# ──────────────────────────────────────────────

@login_required(login_url='login')
def study_view(request, deck_id):
    deck = get_object_or_404(Deck, id=deck_id, created_by=request.user)
    flashcards = list(deck.flashcards.values('id', 'front', 'back'))
    progress_qs = FlashcardProgress.objects.filter(
        student=request.user, flashcard__deck=deck
    ).values('flashcard_id', 'status')
    progress_map = {p['flashcard_id']: p['status'] for p in progress_qs}
    for card in flashcards:
        card['status'] = progress_map.get(card['id'], 'new')
    context = {
        'deck': deck,
        'flashcards_json': json.dumps(flashcards),
        'active_page': 'flashcards',
    }
    return render(request, 'users/study.html', context)


@login_required(login_url='login')
@require_POST
def update_card_progress_view(request, card_id):
    flashcard = get_object_or_404(Flashcard, id=card_id, deck__created_by=request.user)
    status = request.POST.get('status', 'learning')
    if status not in ('new', 'learning', 'mastered'):
        status = 'learning'
    FlashcardProgress.objects.update_or_create(
        student=request.user,
        flashcard=flashcard,
        defaults={'status': status}
    )
    return JsonResponse({'ok': True})


# ──────────────────────────────────────────────
# Quiz Views
# ──────────────────────────────────────────────

@login_required(login_url='login')
def generate_quiz_view(request, deck_id):
    deck = get_object_or_404(Deck, id=deck_id, created_by=request.user)
    flashcards = list(deck.flashcards.values('front', 'back'))
    if len(flashcards) < 4:
        messages.error(request, 'You need at least 4 flashcards to generate a quiz.')
        return redirect('deck_detail', deck_id=deck_id)

    num_questions = min(int(request.GET.get('n', 5)), 10)
    try:
        questions_data = ai_utils.generate_quiz(flashcards, num_questions)
    except Exception as e:
        messages.error(request, f'Quiz generation failed: {str(e)}')
        return redirect('deck_detail', deck_id=deck_id)

    quiz = Quiz.objects.create(deck=deck, title=f'{deck.title} Quiz')
    for q in questions_data:
        QuizQuestion.objects.create(
            quiz=quiz,
            question=q.get('question', ''),
            option_a=q.get('option_a', ''),
            option_b=q.get('option_b', ''),
            option_c=q.get('option_c', ''),
            option_d=q.get('option_d', ''),
            correct_answer=q.get('correct_answer', 'A').upper(),
            explanation=q.get('explanation', ''),
        )

    return redirect('take_quiz', quiz_id=quiz.id)


@login_required(login_url='login')
def take_quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, deck__created_by=request.user)
    questions = list(quiz.questions.values(
        'id', 'question', 'option_a', 'option_b', 'option_c', 'option_d'
    ))
    if request.method == 'POST':
        answers = {}
        score = 0
        all_questions = quiz.questions.all()
        for q in all_questions:
            selected = request.POST.get(f'q_{q.id}', '')
            is_correct = selected.upper() == q.correct_answer
            if is_correct:
                score += 1
            answers[str(q.id)] = {
                'selected': selected.upper(),
                'correct': q.correct_answer,
                'is_correct': is_correct,
                'question': q.question,
                'explanation': q.explanation,
                'option_a': q.option_a,
                'option_b': q.option_b,
                'option_c': q.option_c,
                'option_d': q.option_d,
            }
        attempt = QuizAttempt.objects.create(
            quiz=quiz, student=request.user,
            score=score, total=all_questions.count(),
            answers=answers
        )
        return redirect('quiz_result', attempt_id=attempt.id)

    context = {
        'quiz': quiz,
        'questions_json': json.dumps(questions),
        'active_page': 'flashcards',
    }
    return render(request, 'users/quiz.html', context)


@login_required(login_url='login')
def quiz_result_view(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    context = {
        'attempt': attempt,
        'answers': attempt.answers,
        'active_page': 'flashcards',
    }
    return render(request, 'users/quiz_result.html', context)
