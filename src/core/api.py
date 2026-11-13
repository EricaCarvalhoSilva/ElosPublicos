"""
API REST (Django REST Framework). Cada ViewSet já oferece o CRUD completo:
GET (listar/detalhar), POST (criar), PUT/PATCH (atualizar) e DELETE (excluir).
"""
from rest_framework import permissions, viewsets

from core.models import (
    Cidadao,
    IndicadorOrcamentario,
    Organizacao,
    PostagemApoio,
    ProgramaSocial,
    PublicacaoOrganizacao,
    RedeApoio,
    Solicitacao,
)
from core.serializers import (
    CidadaoSerializer,
    IndicadorOrcamentarioSerializer,
    OrganizacaoSerializer,
    PostagemApoioSerializer,
    ProgramaSocialSerializer,
    PublicacaoOrganizacaoSerializer,
    RedeApoioSerializer,
    SolicitacaoSerializer,
)


class LeituraPublicaViewSet(viewsets.ModelViewSet):
    """Informação pública: qualquer um lê, só usuários logados alteram."""

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CidadaoViewSet(viewsets.ModelViewSet):
    queryset = Cidadao.objects.all()
    serializer_class = CidadaoSerializer


class OrganizacaoViewSet(viewsets.ModelViewSet):
    queryset = Organizacao.objects.all()
    serializer_class = OrganizacaoSerializer


class ProgramaSocialViewSet(LeituraPublicaViewSet):
    queryset = ProgramaSocial.objects.filter(ativo=True)
    serializer_class = ProgramaSocialSerializer


class SolicitacaoViewSet(viewsets.ModelViewSet):
    queryset = Solicitacao.objects.select_related("cidadao", "programa")
    serializer_class = SolicitacaoSerializer


class RedeApoioViewSet(viewsets.ModelViewSet):
    queryset = RedeApoio.objects.all()
    serializer_class = RedeApoioSerializer


class PostagemApoioViewSet(viewsets.ModelViewSet):
    queryset = PostagemApoio.objects.all()
    serializer_class = PostagemApoioSerializer


class PublicacaoOrganizacaoViewSet(LeituraPublicaViewSet):
    queryset = PublicacaoOrganizacao.objects.all()
    serializer_class = PublicacaoOrganizacaoSerializer


class IndicadorOrcamentarioViewSet(LeituraPublicaViewSet):
    queryset = IndicadorOrcamentario.objects.all()
    serializer_class = IndicadorOrcamentarioSerializer
