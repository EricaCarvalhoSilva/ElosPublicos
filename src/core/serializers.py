"""Serializadores da API REST (convertem objetos em JSON e vice-versa)."""
import copy

from django.core.exceptions import ValidationError as ErroValidacaoDjango
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from core.dominio.documentos import somenteDigitos
from core.models import (
    Cidadao,
    IndicadorOrcamentario,
    MembroFamiliar,
    Organizacao,
    PostagemApoio,
    ProgramaSocial,
    PublicacaoOrganizacao,
    RedeApoio,
    Solicitacao,
    validarCpf,
)


class RegrasDoModeloMixin:
    """
    Roda as regras de negócio do model (método clean) também pela API, para
    que a web e a API obedeçam às mesmas regras.
    """

    def validate(self, dados: dict) -> dict:
        dados = super().validate(dados)
        campos = {
            nome: valor
            for nome, valor in dados.items()
            if not isinstance(self.fields.get(nome), serializers.ManyRelatedField)
        }
        if self.instance is not None:
            instancia = copy.copy(self.instance)
            for nome, valor in campos.items():
                setattr(instancia, nome, valor)
        else:
            instancia = self.Meta.model(**campos)
        try:
            instancia.clean()
        except ErroValidacaoDjango as erro:
            raise serializers.ValidationError(
                getattr(erro, "message_dict", {"non_field_errors": erro.messages})
            )
        return dados


class CampoSomenteDigitos(serializers.CharField):
    """Aceita CPF/CNPJ com pontuação e entrega só os números."""

    def to_internal_value(self, data) -> str:
        return somenteDigitos(super().to_internal_value(data))


class MembroFamiliarSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembroFamiliar
        fields = ["id", "nome_completo", "parentesco", "data_nascimento"]


class CidadaoSerializer(RegrasDoModeloMixin, serializers.ModelSerializer):
    cpf = CampoSomenteDigitos(
        max_length=14,
        validators=[validarCpf, UniqueValidator(queryset=Cidadao.objects.all())],
        write_only=True,
    )
    cpf_mascarado = serializers.CharField(source="documentoExibicao", read_only=True)
    renda_per_capita = serializers.DecimalField(
        source="rendaPerCapita", max_digits=10, decimal_places=2, read_only=True
    )
    membros = MembroFamiliarSerializer(source="nucleo_familiar.membros", many=True, read_only=True)

    class Meta:
        model = Cidadao
        fields = [
            "id", "nome_completo", "cpf", "cpf_mascarado", "email", "telefone", "endereco",
            "municipio", "uf", "renda_familiar_declarada", "renda_per_capita", "membros",
            "criado_em", "atualizado_em",
        ]


class OrganizacaoSerializer(RegrasDoModeloMixin, serializers.ModelSerializer):
    tipo_perfil = serializers.CharField(source="tipoPerfil", read_only=True)
    cnpj = CampoSomenteDigitos(
        max_length=18,
        required=False,
        allow_null=True,
        allow_blank=True,
        validators=[UniqueValidator(queryset=Organizacao.objects.all())],
    )

    class Meta:
        model = Organizacao
        fields = "__all__"

    def validate_cnpj(self, valor: str | None) -> str | None:
        return somenteDigitos(valor) or None


class ProgramaSocialSerializer(RegrasDoModeloMixin, serializers.ModelSerializer):
    abrangencia = serializers.CharField(read_only=True)

    class Meta:
        model = ProgramaSocial
        fields = "__all__"


class SolicitacaoSerializer(RegrasDoModeloMixin, serializers.ModelSerializer):
    status_exibicao = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Solicitacao
        fields = "__all__"


class RedeApoioSerializer(serializers.ModelSerializer):
    class Meta:
        model = RedeApoio
        fields = "__all__"


class PostagemApoioSerializer(RegrasDoModeloMixin, serializers.ModelSerializer):
    categoria = serializers.CharField(source="categoriaExibicao", read_only=True)

    class Meta:
        model = PostagemApoio
        fields = "__all__"


class PublicacaoOrganizacaoSerializer(RegrasDoModeloMixin, serializers.ModelSerializer):
    categoria = serializers.CharField(source="categoriaExibicao", read_only=True)

    class Meta:
        model = PublicacaoOrganizacao
        fields = "__all__"


class IndicadorOrcamentarioSerializer(serializers.ModelSerializer):
    percentual_execucao = serializers.DecimalField(
        source="percentualExecucao", max_digits=6, decimal_places=1, read_only=True
    )

    class Meta:
        model = IndicadorOrcamentario
        fields = "__all__"
