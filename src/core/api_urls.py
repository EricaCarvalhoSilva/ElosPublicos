from rest_framework.routers import DefaultRouter

from core import api

roteador = DefaultRouter()
roteador.register("cidadaos", api.CidadaoViewSet)
roteador.register("organizacoes", api.OrganizacaoViewSet)
roteador.register("programas", api.ProgramaSocialViewSet)
roteador.register("solicitacoes", api.SolicitacaoViewSet)
roteador.register("redes", api.RedeApoioViewSet)
roteador.register("postagens", api.PostagemApoioViewSet)
roteador.register("publicacoes", api.PublicacaoOrganizacaoViewSet)
roteador.register("indicadores", api.IndicadorOrcamentarioViewSet)

urlpatterns = roteador.urls
