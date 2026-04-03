from django.urls import path
from .views import ProdutoListarView, ProdutoCreateView, RegistroUsuarioView

urlpatterns = [
    path('produtos/', ProdutoListarView.as_view(), name='listar_produtos'),
    path('produtos/novo/', ProdutoCreateView.as_view(), name='criar_produto'),
    path('usuarios/registrar/', RegistroUsuarioView.as_view(), name='registrar_usuario'),
]