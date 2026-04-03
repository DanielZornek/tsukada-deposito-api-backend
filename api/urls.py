from django.urls import path
from .views import RegistroUsuarioView
from api import views

urlpatterns = [
    path('produtos/', views.ProdutoView.as_view(), name='produtos'),
    path('usuarios/registrar/', RegistroUsuarioView.as_view(), name='registrar_usuario'),
]