from django.contrib import admin

from core.models import (
    Cidadao,
    IndicadorOrcamentario,
    MembroFamiliar,
    NucleoFamiliar,
    Organizacao,
    PostagemApoio,
    ProgramaSocial,
    PublicacaoOrganizacao,
    RedeApoio,
    Solicitacao,
)


class MembroFamiliarInline(admin.TabularInline):
    model = MembroFamiliar
    extra = 1


@admin.register(Cidadao)
class CidadaoAdmin(admin.ModelAdmin):
    list_display = ["nome_completo", "municipio", "uf", "renda_familiar_declarada"]
    search_fields = ["nome_completo", "cpf"]
    list_filter = ["uf"]


@admin.register(NucleoFamiliar)
class NucleoFamiliarAdmin(admin.ModelAdmin):
    inlines = [MembroFamiliarInline]


@admin.register(Organizacao)
class OrganizacaoAdmin(admin.ModelAdmin):
    list_display = ["nome_completo", "tipo", "municipio", "uf"]


@admin.register(ProgramaSocial)
class ProgramaSocialAdmin(admin.ModelAdmin):
    list_display = ["nome", "esfera", "uf", "municipio", "ativo"]
    list_filter = ["esfera", "uf", "ativo"]


@admin.register(Solicitacao)
class SolicitacaoAdmin(admin.ModelAdmin):
    list_display = ["cidadao", "programa", "orgao", "status", "atualizado_em"]
    list_filter = ["status", "orgao"]


admin.site.register(RedeApoio)
admin.site.register(PostagemApoio)
admin.site.register(PublicacaoOrganizacao)
admin.site.register(IndicadorOrcamentario)
