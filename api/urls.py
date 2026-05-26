from django.urls import path
from .views import (
    RegistroUsuarioView, 
    ProdutoListarView, 
    ProdutoCreateView, 
    LoginUsuarioView,
    PerfilUsuarioView,
    ProdutoReservarView,
    UsuarioReservasView,
    ReservaDetailView  # Importando a nova View aqui
)

urlpatterns = [
    # Rotas de Listagem (GET)
    path('produtos', ProdutoListarView.as_view(), name='listar_produtos_sem_barra'),
    path('produtos/', ProdutoListarView.as_view(), name='listar_produtos'),

    # Rota de Criação (POST)
    path('produtos/novo', ProdutoCreateView.as_view(), name='cadastrar_produto_sem_barra'),
    path('produtos/novo/', ProdutoCreateView.as_view(), name='cadastrar_produto'),

    # Rotas de Edição de Produtos (PUT)
    path('produtos/<str:pk>', ProdutoCreateView.as_view(), name='atualizar_produto_sem_barra'),
    path('produtos/<str:pk>/', ProdutoCreateView.as_view(), name='atualizar_produto'),

    # Rotas de Criação de Reserva (POST)
    path('produtos/<str:pk>/reservar', ProdutoReservarView.as_view(), name='reservar_produto_sem_barra'),
    path('produtos/<str:pk>/reservar/', ProdutoReservarView.as_view(), name='reservar_produto'),

    # ROTAS PARA ATUALIZAR STATUS DA RESERVA (PUT)
    path('reservas/<str:pk>', ReservaDetailView.as_view(), name='atualizar_reserva_sem_barra'),
    path('reservas/<str:pk>/', ReservaDetailView.as_view(), name='atualizar_reserva'),

    # Rotas de Usuário (Registro e Login)
    path('usuarios/registrar/', RegistroUsuarioView.as_view(), name='registrar_usuario'),
    path('usuarios/login/', LoginUsuarioView.as_view(), name='login_usuario'),
    
    # Rotas de Perfil
    path('usuarios/perfil/<str:uid>', PerfilUsuarioView.as_view(), name='perfil_usuario_sem_barra'),
    path('usuarios/perfil/<str:uid>/', PerfilUsuarioView.as_view(), name='perfil_usuario'),
    
    # Rotas do Histórico de Reservas do Usuário (GET)
    path('usuarios/perfil/<str:uid>/reservas', UsuarioReservasView.as_view(), name='usuario_reservas_sem_barra'),
    path('usuarios/perfil/<str:uid>/reservas/', UsuarioReservasView.as_view(), name='usuario_reservas'),
]