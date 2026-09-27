from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('registrar/', views.register_view, name='register'),
    path('entrar/', auth_views.LoginView.as_view(template_name='jogadores/login.html'), name='login'),
    path('sair/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]