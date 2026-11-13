"""Formulários (validação de entrada antes de gravar no banco)."""
from django import forms
from django.forms import inlineformset_factory

from core.dominio.documentos import somenteDigitos
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
    UF_CHOICES,
)


class CidadaoForm(forms.ModelForm):
    # Aceita CPF com ou sem pontuação; grava só os 11 números.
    cpf = forms.CharField(label="CPF", max_length=14, help_text="Somente números ou 000.000.000-00")

    class Meta:
        model = Cidadao
        fields = [
            "nome_completo",
            "cpf",
            "email",
            "telefone",
            "endereco",
            "municipio",
            "uf",
            "renda_familiar_declarada",
        ]

    def clean_cpf(self) -> str:
        return somenteDigitos(self.cleaned_data["cpf"])


MembroFamiliarFormSet = inlineformset_factory(
    NucleoFamiliar,
    MembroFamiliar,
    fields=["nome_completo", "parentesco", "data_nascimento"],
    widgets={"data_nascimento": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")},
    extra=2,
    can_delete=True,
)


class OrganizacaoForm(forms.ModelForm):
    class Meta:
        model = Organizacao
        fields = ["nome_completo", "tipo", "cnpj", "email", "telefone", "municipio", "uf", "descricao"]
        labels = {"nome_completo": "nome da organização"}


class ProgramaSocialForm(forms.ModelForm):
    class Meta:
        model = ProgramaSocial
        exclude = []


class FiltroProgramaForm(forms.Form):
    uf = forms.ChoiceField(label="UF", choices=[("", "Todas")] + UF_CHOICES, required=False)
    municipio = forms.CharField(label="Município", required=False)
    esfera = forms.ChoiceField(
        label="Esfera", choices=[("", "Todas")] + list(ProgramaSocial.Esfera.choices), required=False
    )


class SolicitacaoForm(forms.ModelForm):
    class Meta:
        model = Solicitacao
        fields = ["cidadao", "programa", "orgao", "numero_protocolo", "status", "observacao"]


class RedeApoioForm(forms.ModelForm):
    class Meta:
        model = RedeApoio
        fields = ["nome", "descricao", "municipio", "uf", "membros"]
        widgets = {"membros": forms.CheckboxSelectMultiple}


class PostagemApoioForm(forms.ModelForm):
    class Meta:
        model = PostagemApoio
        fields = ["autor", "natureza", "tipo", "titulo", "descricao"]

    def __init__(self, *args, rede: RedeApoio | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if rede is not None:
            self.instance.rede = rede
            self.fields["autor"].queryset = rede.membros.all()


class PublicacaoOrganizacaoForm(forms.ModelForm):
    class Meta:
        model = PublicacaoOrganizacao
        fields = ["organizacao", "tipo", "titulo", "descricao", "data_evento", "local", "link_inscricao"]
        widgets = {
            "data_evento": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M")
        }


class IndicadorOrcamentarioForm(forms.ModelForm):
    class Meta:
        model = IndicadorOrcamentario
        exclude = []
