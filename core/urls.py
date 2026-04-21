from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('checkin/', views.checkin, name='checkin'),
    path('os/<int:os_id>/', views.os_detail, name='os_detail'),
    path('os/<int:os_id>/status/', views.atualizar_status, name='atualizar_status'),
    path('os/<int:os_id>/finalizar/', views.finalizar_servico, name='finalizar_servico'),
    path('os/<int:os_id>/adicionar-peca/', views.adicionar_peca, name='adicionar_peca'),
    path('os/<int:os_id>/adicionar-historico/', views.adicionar_historico, name='adicionar_historico'),
    path('os/<int:os_id>/mudar-status/', views.atualizar_status, name='mudar_status'),
    path('os/<int:os_id>/adicionar-foto/', views.adicionar_foto, name='adicionar_foto'),
    path('foto/<int:foto_id>/remover/', views.remover_foto, name='remover_foto'),
    path('os/<int:os_id>/atualizar-mao-obra/', views.atualizar_mao_obra, name='atualizar_mao_obra'),
    path('historico/', views.historico_geral, name='historico_geral'),
    path('metricas/', views.metricas, name='metricas'),
    path('fichas/', views.fichas_motor, name='fichas_motor'),
    path('fichas/<int:id>/', views.ficha_detail, name='ficha_detail'),
    path('metricas/relatorio/', views.gerar_relatorio, name='gerar_relatorio'),
]
