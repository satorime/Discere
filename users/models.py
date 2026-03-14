from django.db import models
from django.contrib.auth.models import User


class Course(models.Model):
    CATEGORY_CHOICES = [
        ('programming', 'Programming'),
        ('design', 'Design'),
        ('business', 'Business'),
        ('science', 'Science'),
        ('language', 'Language'),
        ('mathematics', 'Mathematics'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_teaching')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def enrolled_count(self):
        return self.enrollments.count()


class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    progress = models.IntegerField(default=0)  # 0-100

    class Meta:
        unique_together = ['student', 'course']

    def __str__(self):
        return f"{self.student.username} - {self.course.title}"


# ──────────────────────────────────────────────
# Flashcard & Quiz Models
# ──────────────────────────────────────────────

class Deck(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='decks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def card_count(self):
        return self.flashcards.count()

    def mastered_count(self, user):
        return FlashcardProgress.objects.filter(
            flashcard__deck=self, student=user, status='mastered'
        ).count()


class Flashcard(models.Model):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name='flashcards')
    front = models.TextField()
    back = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.deck.title}: {self.front[:50]}"


class FlashcardProgress(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('learning', 'Learning'),
        ('mastered', 'Mastered'),
    ]
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flashcard_progress')
    flashcard = models.ForeignKey(Flashcard, on_delete=models.CASCADE, related_name='progress')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    last_reviewed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'flashcard']


class Quiz(models.Model):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def question_count(self):
        return self.questions.count()


class QuizQuestion(models.Model):
    ANSWER_CHOICES = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question = models.TextField()
    option_a = models.TextField()
    option_b = models.TextField()
    option_c = models.TextField()
    option_d = models.TextField()
    correct_answer = models.CharField(max_length=1, choices=ANSWER_CHOICES)
    explanation = models.TextField(blank=True)

    def __str__(self):
        return self.question[:80]


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    score = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    answers = models.JSONField(default=dict)
    completed_at = models.DateTimeField(auto_now_add=True)

    def percentage(self):
        if self.total == 0:
            return 0
        return round((self.score / self.total) * 100)
