from django.urls import path
from .views import (
    RegistroUsuarioView, 
    ProdutoListarView, 
    ProdutoCreateView, 
    LoginUsuarioView,
    PerfilUsuarioView,
    ProdutoReservarView,
    UsuarioReservasView,
    ReservaDetailView,
    DashboardStatsView,
    ListaTodasReservasView 
)

urlpatterns = [
    # Rotas de Produtos
    path('produtos/', ProdutoListarView.as_view(), name='listar_produtos'),
    path('produtos/novo/', ProdutoCreateView.as_view(), name='cadastrar_produto'),
    path('produtos/<str:pk>/', ProdutoCreateView.as_view(), name='atualizar_produto'),

    # Rotas de Reservas (Criação e Atualização de Status)
    path('produtos/<str:pk>/reservar/', ProdutoReservarView.as_view(), name='reservar_produto'),
    path('reservas/<str:pk>/', ReservaDetailView.as_view(), name='atualizar_reserva'),

    # Rotas de Autenticação e Usuário
    path('usuarios/registrar/', RegistroUsuarioView.as_view(), name='registrar_usuario'),
    path('usuarios/login/', LoginUsuarioView.as_view(), name='login_usuario'),
    
    # Rotas de Perfil e Histórico do Cliente
    path('usuarios/perfil/<str:uid>/', PerfilUsuarioView.as_view(), name='perfil_usuario'),
    path('usuarios/perfil/<str:uid>/reservas/', UsuarioReservasView.as_view(), name='usuario_reservas'),

    # Rotas do Dashboard / Painel do Administrador
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard_stats'),
    path('dashboard/reservas/', ListaTodasReservasView.as_view(), name='dashboard_reservas'), # <-- NOVA ROTA AQUI
]