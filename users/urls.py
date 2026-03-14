from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('courses/', views.courses_view, name='courses'),
    path('courses/<int:course_id>/', views.course_detail_view, name='course_detail'),
    path('courses/<int:course_id>/enroll/', views.enroll_view, name='enroll'),
    path('profile/', views.profile_view, name='profile'),
]
