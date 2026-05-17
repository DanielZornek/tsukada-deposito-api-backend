from django.urls import path
from .views import RegistroUsuarioView, ProdutoListarView, ProdutoCreateView, LoginUsuarioView

urlpatterns = [
    path('produtos/', ProdutoListarView.as_view(), name='listar_produtos'),
    path('produtos/novo/', ProdutoCreateView.as_view(), name='cadastrar_produto'),
    path('usuarios/registrar/', RegistroUsuarioView.as_view(), name='registrar_usuario'),
    path('usuarios/login/', LoginUsuarioView.as_view(), name='login_usuario'),
]