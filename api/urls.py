from django.urls import path
from .views import (
    RegistroUsuarioView, 
    ProdutoListarView, 
    ProdutoCreateView, 
    LoginUsuarioView
)

urlpatterns = [
    # Rotas de Listagem (GET)
    path('produtos', ProdutoListarView.as_view(), name='listar_produtos_sem_barra'),
    path('produtos/', ProdutoListarView.as_view(), name='listar_produtos'),

    # Rota de Criação (POST) - Aponta para a CreateView sem ID
    path('produtos/novo', ProdutoCreateView.as_view(), name='cadastrar_produto_sem_barra'),
    path('produtos/novo/', ProdutoCreateView.as_view(), name='cadastrar_produto'),

    # Rotas de Edição (PUT) - Capturam o ID (pk) do produto enviado pelo React Native
    path('produtos/<str:pk>', ProdutoCreateView.as_view(), name='atualizar_produto_sem_barra'),
    path('produtos/<str:pk>/', ProdutoCreateView.as_view(), name='atualizar_produto'),

    # Rotas de Usuário
    path('usuarios/registrar/', RegistroUsuarioView.as_view(), name='registrar_usuario'),
    path('usuarios/login/', LoginUsuarioView.as_view(), name='login_usuario'),
]