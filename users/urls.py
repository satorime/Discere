from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home_view, name='home'),

    # Dashboard & Courses
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('courses/', views.courses_view, name='courses'),
    path('courses/<int:course_id>/', views.course_detail_view, name='course_detail'),
    path('courses/<int:course_id>/enroll/', views.enroll_view, name='enroll'),
    path('profile/', views.profile_view, name='profile'),

    # Decks
    path('flashcards/', views.decks_view, name='decks'),
    path('flashcards/create/', views.create_deck_view, name='create_deck'),
    path('flashcards/<int:deck_id>/', views.deck_detail_view, name='deck_detail'),
    path('flashcards/<int:deck_id>/delete/', views.delete_deck_view, name='delete_deck'),
    path('flashcards/<int:deck_id>/add-card/', views.add_flashcard_view, name='add_flashcard'),
    path('flashcards/card/<int:card_id>/delete/', views.delete_flashcard_view, name='delete_flashcard'),

    # Study
    path('flashcards/<int:deck_id>/study/', views.study_view, name='study'),
    path('flashcards/card/<int:card_id>/progress/', views.update_card_progress_view, name='update_card_progress'),

    # Quiz
    path('flashcards/<int:deck_id>/generate-quiz/', views.generate_quiz_view, name='generate_quiz'),
    path('quiz/<int:quiz_id>/', views.take_quiz_view, name='take_quiz'),
    path('quiz/result/<int:attempt_id>/', views.quiz_result_view, name='quiz_result'),
]
