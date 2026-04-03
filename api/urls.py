from django.urls import path
from .views import RegistroUsuarioView, ProdutoListarView, ProdutoCreateView

urlpatterns = [
    path('produtos/', ProdutoListarView.as_view(), name='listar_produtos'),
    path('produtos/novo/', ProdutoCreateView.as_view(), name='cadastrar_produto'),
    path('usuarios/registrar/', RegistroUsuarioView.as_view(), name='registrar_usuario'),
]