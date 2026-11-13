from django.urls import path

from core import views

app_name = "core"

urlpatterns = [
    path("", views.InicioView.as_view(), name="inicio"),
    # Requisito 1 — cidadãos (CRUD da entidade principal)
    path("cidadaos/", views.CidadaoListView.as_view(), name="cidadao-lista"),
    path("cidadaos/novo/", views.CidadaoCreateView.as_view(), name="cidadao-novo"),
    path("cidadaos/<int:pk>/", views.CidadaoDetailView.as_view(), name="cidadao-detalhe"),
    path("cidadaos/<int:pk>/editar/", views.CidadaoUpdateView.as_view(), name="cidadao-editar"),
    path("cidadaos/<int:pk>/excluir/", views.CidadaoDeleteView.as_view(), name="cidadao-excluir"),
    path("cidadaos/<int:pk>/familia/", views.MembrosFamiliaresView.as_view(), name="cidadao-membros"),
    # Requisito 2 — programas sociais
    path("programas/", views.ProgramaListView.as_view(), name="programa-lista"),
    path("programas/novo/", views.ProgramaCreateView.as_view(), name="programa-novo"),
    path("programas/<int:pk>/", views.ProgramaDetailView.as_view(), name="programa-detalhe"),
    path("programas/<int:pk>/editar/", views.ProgramaUpdateView.as_view(), name="programa-editar"),
    path("programas/<int:pk>/excluir/", views.ProgramaDeleteView.as_view(), name="programa-excluir"),
    # Requisito 3 — redes de apoio mútuo
    path("redes/", views.RedeListView.as_view(), name="rede-lista"),
    path("redes/nova/", views.RedeCreateView.as_view(), name="rede-nova"),
    path("redes/<int:pk>/", views.RedeDetailView.as_view(), name="rede-detalhe"),
    path("redes/<int:pk>/editar/", views.RedeUpdateView.as_view(), name="rede-editar"),
    path("redes/<int:pk>/excluir/", views.RedeDeleteView.as_view(), name="rede-excluir"),
    path("redes/<int:rede_pk>/publicar/", views.PostagemCreateView.as_view(), name="postagem-nova"),
    path("postagens/<int:pk>/editar/", views.PostagemUpdateView.as_view(), name="postagem-editar"),
    path("postagens/<int:pk>/excluir/", views.PostagemDeleteView.as_view(), name="postagem-excluir"),
    # Requisito 4 — solicitações
    path("solicitacoes/", views.SolicitacaoListView.as_view(), name="solicitacao-lista"),
    path("solicitacoes/nova/", views.SolicitacaoCreateView.as_view(), name="solicitacao-nova"),
    path("solicitacoes/<int:pk>/editar/", views.SolicitacaoUpdateView.as_view(), name="solicitacao-editar"),
    path("solicitacoes/<int:pk>/excluir/", views.SolicitacaoDeleteView.as_view(), name="solicitacao-excluir"),
    # Requisito 5 — painel de indicadores
    path("painel/", views.PainelIndicadoresView.as_view(), name="painel"),
    path("painel/novo/", views.IndicadorCreateView.as_view(), name="indicador-novo"),
    path("painel/<int:pk>/editar/", views.IndicadorUpdateView.as_view(), name="indicador-editar"),
    path("painel/<int:pk>/excluir/", views.IndicadorDeleteView.as_view(), name="indicador-excluir"),
    # Requisito 6 — organizações e mural
    path("organizacoes/", views.OrganizacaoListView.as_view(), name="organizacao-lista"),
    path("organizacoes/nova/", views.OrganizacaoCreateView.as_view(), name="organizacao-nova"),
    path("organizacoes/<int:pk>/editar/", views.OrganizacaoUpdateView.as_view(), name="organizacao-editar"),
    path("organizacoes/<int:pk>/excluir/", views.OrganizacaoDeleteView.as_view(), name="organizacao-excluir"),
    path("mural/", views.MuralView.as_view(), name="mural"),
    path("mural/publicar/", views.PublicacaoOrganizacaoCreateView.as_view(), name="publicacao-nova"),
    path("mural/<int:pk>/editar/", views.PublicacaoOrganizacaoUpdateView.as_view(), name="publicacao-editar"),
    path("mural/<int:pk>/excluir/", views.PublicacaoOrganizacaoDeleteView.as_view(), name="publicacao-excluir"),
]
