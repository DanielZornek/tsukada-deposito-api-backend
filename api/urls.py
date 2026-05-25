from django.urls import path
from .views import (
    RegistroUsuarioView, 
    ProdutoListarView, 
    ProdutoCreateView, 
    LoginUsuarioView,
    PerfilUsuarioView,
    ProdutoReservarView,
    UsuarioReservasView 
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

    # Rotas de Reserva (POST) - Dá baixa no estoque e cria o documento na coleção 'reservas'
    path('produtos/<str:pk>/reservar', ProdutoReservarView.as_view(), name='reservar_produto_sem_barra'),
    path('produtos/<str:pk>/reservar/', ProdutoReservarView.as_view(), name='reservar_produto'),

    # Rotas de Usuário (Registro e Login)
    path('usuarios/registrar/', RegistroUsuarioView.as_view(), name='registrar_usuario'),
    path('usuarios/login/', LoginUsuarioView.as_view(), name='login_usuario'),
    
    # Rotas de Perfil (PUT para atualizar / DELETE para excluir conta)
    path('usuarios/perfil/<str:uid>', PerfilUsuarioView.as_view(), name='perfil_usuario_sem_barra'),
    path('usuarios/perfil/<str:uid>/', PerfilUsuarioView.as_view(), name='perfil_usuario'),
    
    # Rotas do Histórico de Reservas do Usuário (GET para renderizar no perfil do app)
    path('usuarios/perfil/<str:uid>/reservas', UsuarioReservasView.as_view(), name='usuario_reservas_sem_barra'),
    path('usuarios/perfil/<str:uid>/reservas/', UsuarioReservasView.as_view(), name='usuario_reservas'),
]