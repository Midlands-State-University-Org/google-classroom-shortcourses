from django.urls import path
from . import views
from .views import error_page, create_class

urlpatterns = [
    path('home/', views.home, name='home'),
    path('', views.landing_page, name='landing'),
    path('courses/', views.courses, name='courses'),
    path('course/<int:courseid>/', views.course_detail, name='course_detail'),
    path('course/checkout/<int:courseid>/', views.course_checkout, name='course_checkout'),
    path('login/', views.google_classroom_login, name='login'),
    path('oauth2callback/', views.oauth2callback, name='oauth2callback'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('error-page/', error_page, name='error_page'),
    path('create-class/', create_class, name='create_class'),
    path('logout/', views.logout_view, name='logout'),
]
