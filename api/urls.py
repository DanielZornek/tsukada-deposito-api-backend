from django.urls import path
from .views import RegistroUsuarioView, ProdutoListarView, ProdutoCreateView, LoginUsuarioView

urlpatterns = [
    path('produtos', ProdutoListarView.as_view(), name='listar_produtos_sem_barra'),
    path('produtos/', ProdutoListarView.as_view(), name='listar_produtos'),
    
    path('produtos/novo', ProdutoCreateView.as_view(), name='cadastrar_produto_sem_barra'), # <-- Sem barra
    path('produtos/novo/', ProdutoCreateView.as_view(), name='cadastrar_produto'),         # <-- Com barra
    
    path('usuarios/registrar/', RegistroUsuarioView.as_view(), name='registrar_usuario'),
    path('usuarios/login/', LoginUsuarioView.as_view(), name='login_usuario'),
]