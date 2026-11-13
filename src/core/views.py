"""
Views (camada de controle). Usamos as views genéricas baseadas em classes do
Django: cada CRUD herda de CreateView/ListView/UpdateView/DeleteView e
sobrescreve só o que precisa (mais um exemplo de herança e polimorfismo).
"""
from __future__ import annotations

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import ProtectedError, Q, Sum
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from core.compat import override
from core.forms import (
    CidadaoForm,
    FiltroProgramaForm,
    IndicadorOrcamentarioForm,
    MembroFamiliarFormSet,
    OrganizacaoForm,
    PostagemApoioForm,
    ProgramaSocialForm,
    PublicacaoOrganizacaoForm,
    RedeApoioForm,
    SolicitacaoForm,
)
from core.models import (
    Cidadao,
    IndicadorOrcamentario,
    Organizacao,
    PostagemApoio,
    ProgramaSocial,
    PublicacaoOrganizacao,
    RedeApoio,
    Solicitacao,
    UF_CHOICES,
)


# ---------------------------------------------------------------------------
# Mixins reaproveitados por todos os CRUDs
# ---------------------------------------------------------------------------
class FormularioMixin(LoginRequiredMixin, SuccessMessageMixin):
    """Usa o mesmo template de formulário para qualquer entidade."""

    template_name = "core/form.html"
    titulo = ""
    textoBotao = "Salvar"

    @override
    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["titulo"] = self.titulo
        contexto["texto_botao"] = self.textoBotao
        contexto["url_voltar"] = self.request.META.get("HTTP_REFERER", reverse("core:inicio"))
        return contexto


class ExclusaoMixin(LoginRequiredMixin, SuccessMessageMixin):
    template_name = "core/confirmar_exclusao.html"
    aviso = ""

    @override
    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["aviso"] = self.aviso
        return contexto


class InicioView(TemplateView):
    template_name = "core/inicio.html"

    @override
    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["total_programas"] = ProgramaSocial.objects.filter(ativo=True).count()
        contexto["total_redes"] = RedeApoio.objects.count()
        contexto["total_publicacoes"] = (
            PostagemApoio.objects.filter(ativa=True).count()
            + PublicacaoOrganizacao.objects.filter(ativa=True).count()
        )
        return contexto


# ---------------------------------------------------------------------------
# Requisito 1 — Cidadão (entidade principal, CRUD completo)
# ---------------------------------------------------------------------------
class CidadaoListView(LoginRequiredMixin, ListView):
    model = Cidadao
    template_name = "core/cidadao_lista.html"
    paginate_by = 20

    @override
    def get_queryset(self):
        consulta = super().get_queryset()
        busca = self.request.GET.get("q", "").strip()
        if busca:
            digitos = "".join(c for c in busca if c.isdigit())
            filtro = Q(nome_completo__icontains=busca) | Q(municipio__icontains=busca)
            if digitos:
                filtro |= Q(cpf__contains=digitos)
            consulta = consulta.filter(filtro)
        return consulta


class CidadaoDetailView(LoginRequiredMixin, DetailView):
    model = Cidadao
    template_name = "core/cidadao_detalhe.html"

    @override
    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        cidadao: Cidadao = self.object
        programas = ProgramaSocial.disponiveisPara(cidadao.uf, cidadao.municipio)
        contexto["avaliacoes"] = [(p, p.avaliarElegibilidade(cidadao)) for p in programas]
        contexto["membros"] = cidadao.obterNucleo().membros.all()
        contexto["solicitacoes"] = cidadao.solicitacoes.select_related("programa")
        return contexto


class CidadaoCreateView(FormularioMixin, CreateView):
    model = Cidadao
    form_class = CidadaoForm
    titulo = "Cadastrar cidadão"
    textoBotao = "Cadastrar"
    success_message = "Cidadão cadastrado. Agora inclua quem mora com ele(a)."

    @override
    def get_success_url(self) -> str:
        return reverse("core:cidadao-membros", args=[self.object.pk])


class CidadaoUpdateView(FormularioMixin, UpdateView):
    model = Cidadao
    form_class = CidadaoForm
    titulo = "Editar cadastro"
    success_message = "Cadastro atualizado."


class CidadaoDeleteView(ExclusaoMixin, DeleteView):
    model = Cidadao
    success_url = reverse_lazy("core:cidadao-lista")
    success_message = "Cadastro excluído."
    aviso = "O núcleo familiar, as solicitações e as postagens dessa pessoa também serão apagados."


class MembrosFamiliaresView(LoginRequiredMixin, View):
    """Edita a composição do núcleo familiar (composição 1:N)."""

    template_name = "core/form.html"

    def _renderizar(self, request: HttpRequest, cidadao: Cidadao, formset) -> HttpResponse:
        return render(
            request,
            self.template_name,
            {
                "titulo": f"Quem mora com {cidadao.nome_completo}",
                "subtitulo": "Inclua todas as pessoas que vivem na mesma casa e dividem a renda.",
                "formset": formset,
                "texto_botao": "Salvar composição familiar",
                "url_voltar": cidadao.get_absolute_url(),
            },
        )

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        cidadao = get_object_or_404(Cidadao, pk=pk)
        formset = MembroFamiliarFormSet(instance=cidadao.obterNucleo())
        return self._renderizar(request, cidadao, formset)

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        cidadao = get_object_or_404(Cidadao, pk=pk)
        formset = MembroFamiliarFormSet(request.POST, instance=cidadao.obterNucleo())
        if formset.is_valid():
            formset.save()
            messages.success(request, "Composição familiar atualizada.")
            return redirect(cidadao.get_absolute_url())
        return self._renderizar(request, cidadao, formset)


# ---------------------------------------------------------------------------
# Requisito 2 — Programas sociais por região
# ---------------------------------------------------------------------------
class ProgramaListView(ListView):
    model = ProgramaSocial
    template_name = "core/programa_lista.html"

    @override
    def get_queryset(self):
        self.filtro = FiltroProgramaForm(self.request.GET or None)
        consulta = ProgramaSocial.objects.filter(ativo=True)
        if self.filtro.is_valid():
            uf = self.filtro.cleaned_data["uf"]
            municipio = self.filtro.cleaned_data["municipio"]
            esfera = self.filtro.cleaned_data["esfera"]
            if uf:
                consulta = ProgramaSocial.disponiveisPara(uf, municipio)
            if esfera:
                consulta = consulta.filter(esfera=esfera)
        return consulta

    @override
    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["filtro"] = self.filtro
        return contexto


class ProgramaDetailView(DetailView):
    model = ProgramaSocial
    template_name = "core/programa_detalhe.html"

    @override
    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            contexto["cidadaos"] = Cidadao.objects.all()
            cidadaoId = self.request.GET.get("cidadao")
            if cidadaoId and cidadaoId.isdigit():
                cidadao = Cidadao.objects.filter(pk=int(cidadaoId)).first()
                if cidadao:
                    contexto["cidadao_avaliado"] = cidadao
                    contexto["resultado"] = self.object.avaliarElegibilidade(cidadao)
        return contexto


class ProgramaCreateView(FormularioMixin, CreateView):
    model = ProgramaSocial
    form_class = ProgramaSocialForm
    titulo = "Cadastrar programa social"
    success_message = "Programa cadastrado."


class ProgramaUpdateView(FormularioMixin, UpdateView):
    model = ProgramaSocial
    form_class = ProgramaSocialForm
    titulo = "Editar programa social"
    success_message = "Programa atualizado."


class ProgramaDeleteView(ExclusaoMixin, DeleteView):
    model = ProgramaSocial
    success_url = reverse_lazy("core:programa-lista")
    success_message = "Programa excluído."

    @override
    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                "Este programa tem solicitações registradas. Desative-o em vez de excluir.",
            )
            return HttpResponseRedirect(self.object.get_absolute_url())


# ---------------------------------------------------------------------------
# Requisito 4 — Acompanhamento de solicitações
# ---------------------------------------------------------------------------
class SolicitacaoListView(LoginRequiredMixin, ListView):
    model = Solicitacao
    template_name = "core/solicitacao_lista.html"
    paginate_by = 30

    @override
    def get_queryset(self):
        consulta = Solicitacao.objects.select_related("cidadao", "programa")
        cidadaoId = self.request.GET.get("cidadao", "")
        status = self.request.GET.get("status", "")
        if cidadaoId.isdigit():
            consulta = consulta.filter(cidadao_id=int(cidadaoId))
        if status:
            consulta = consulta.filter(status=status)
        return consulta

    @override
    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["cidadaos"] = Cidadao.objects.all()
        contexto["status_opcoes"] = Solicitacao.Status.choices
        return contexto


class SolicitacaoCreateView(FormularioMixin, CreateView):
    model = Solicitacao
    form_class = SolicitacaoForm
    titulo = "Registrar solicitação"
    success_message = "Solicitação registrada."
    success_url = reverse_lazy("core:solicitacao-lista")

    @override
    def get_initial(self):
        inicial = super().get_initial()
        for campo in ("cidadao", "programa"):
            valor = self.request.GET.get(campo)
            if valor and valor.isdigit():
                inicial[campo] = int(valor)
        return inicial


class SolicitacaoUpdateView(FormularioMixin, UpdateView):
    model = Solicitacao
    form_class = SolicitacaoForm
    titulo = "Atualizar solicitação"
    success_message = "Solicitação atualizada."
    success_url = reverse_lazy("core:solicitacao-lista")


class SolicitacaoDeleteView(ExclusaoMixin, DeleteView):
    model = Solicitacao
    success_url = reverse_lazy("core:solicitacao-lista")
    success_message = "Solicitação excluída."


# ---------------------------------------------------------------------------
# Requisito 3 — Redes de apoio mútuo
# ---------------------------------------------------------------------------
class RedeListView(LoginRequiredMixin, ListView):
    model = RedeApoio
    template_name = "core/rede_lista.html"


class RedeDetailView(LoginRequiredMixin, DetailView):
    model = RedeApoio
    template_name = "core/rede_detalhe.html"

    @override
    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["postagens"] = self.object.postagens.filter(ativa=True).select_related("autor")
        return contexto


class RedeCreateView(FormularioMixin, CreateView):
    model = RedeApoio
    form_class = RedeApoioForm
    titulo = "Criar rede de apoio"
    success_message = "Rede criada."


class RedeUpdateView(FormularioMixin, UpdateView):
    model = RedeApoio
    form_class = RedeApoioForm
    titulo = "Editar rede de apoio"
    success_message = "Rede atualizada."


class RedeDeleteView(ExclusaoMixin, DeleteView):
    model = RedeApoio
    success_url = reverse_lazy("core:rede-lista")
    success_message = "Rede excluída."
    aviso = "Todas as postagens da rede também serão apagadas."


class PostagemCreateView(FormularioMixin, CreateView):
    model = PostagemApoio
    form_class = PostagemApoioForm
    titulo = "Publicar oferta ou pedido"
    textoBotao = "Publicar"
    success_message = "Publicado na rede."

    @override
    def dispatch(self, request, *args, **kwargs):
        self.rede = get_object_or_404(RedeApoio, pk=kwargs["rede_pk"])
        return super().dispatch(request, *args, **kwargs)

    @override
    def get_form_kwargs(self):
        argumentos = super().get_form_kwargs()
        argumentos["rede"] = self.rede
        return argumentos

    @override
    def get_success_url(self) -> str:
        return self.rede.get_absolute_url()


class PostagemUpdateView(FormularioMixin, UpdateView):
    model = PostagemApoio
    form_class = PostagemApoioForm
    titulo = "Editar postagem"
    success_message = "Postagem atualizada."

    @override
    def get_form_kwargs(self):
        argumentos = super().get_form_kwargs()
        argumentos["rede"] = self.object.rede
        return argumentos

    @override
    def get_success_url(self) -> str:
        return self.object.rede.get_absolute_url()


class PostagemDeleteView(ExclusaoMixin, DeleteView):
    model = PostagemApoio
    success_message = "Postagem removida."

    @override
    def get_success_url(self) -> str:
        return self.object.rede.get_absolute_url()


# ---------------------------------------------------------------------------
# Requisito 6 — Organizações e suas publicações
# ---------------------------------------------------------------------------
class OrganizacaoListView(LoginRequiredMixin, ListView):
    model = Organizacao
    template_name = "core/organizacao_lista.html"


class OrganizacaoCreateView(FormularioMixin, CreateView):
    model = Organizacao
    form_class = OrganizacaoForm
    titulo = "Cadastrar organização"
    success_message = "Organização cadastrada."


class OrganizacaoUpdateView(FormularioMixin, UpdateView):
    model = Organizacao
    form_class = OrganizacaoForm
    titulo = "Editar organização"
    success_message = "Organização atualizada."


class OrganizacaoDeleteView(ExclusaoMixin, DeleteView):
    model = Organizacao
    success_url = reverse_lazy("core:organizacao-lista")
    success_message = "Organização excluída."
    aviso = "Os editais, oficinas e eventos dela também serão apagados."


class PublicacaoOrganizacaoCreateView(FormularioMixin, CreateView):
    model = PublicacaoOrganizacao
    form_class = PublicacaoOrganizacaoForm
    titulo = "Publicar edital, oficina ou evento"
    textoBotao = "Publicar"
    success_message = "Publicado no mural."
    success_url = reverse_lazy("core:mural")


class PublicacaoOrganizacaoUpdateView(FormularioMixin, UpdateView):
    model = PublicacaoOrganizacao
    form_class = PublicacaoOrganizacaoForm
    titulo = "Editar publicação"
    success_message = "Publicação atualizada."
    success_url = reverse_lazy("core:mural")


class PublicacaoOrganizacaoDeleteView(ExclusaoMixin, DeleteView):
    model = PublicacaoOrganizacao
    success_url = reverse_lazy("core:mural")
    success_message = "Publicação removida."


class MuralView(TemplateView):
    """
    Mural da comunidade. Junta postagens de cidadãos e publicações de
    organizações numa lista só e chama `resumo()` em cada uma: o mesmo método
    responde diferente conforme a classe concreta (polimorfismo).
    """

    template_name = "core/mural.html"

    @override
    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        publicacoes = list(
            PostagemApoio.objects.filter(ativa=True).select_related("autor", "rede")[:50]
        ) + list(PublicacaoOrganizacao.objects.filter(ativa=True).select_related("organizacao")[:50])
        publicacoes.sort(key=lambda p: p.criado_em, reverse=True)
        contexto["itens"] = [(p, p.resumo()) for p in publicacoes]
        return contexto


# ---------------------------------------------------------------------------
# Requisito 5 — Painel de execução orçamentária
# ---------------------------------------------------------------------------
class PainelIndicadoresView(ListView):
    model = IndicadorOrcamentario
    template_name = "core/painel_indicadores.html"

    @override
    def get_queryset(self):
        consulta = super().get_queryset()
        uf = self.request.GET.get("uf", "")
        municipio = self.request.GET.get("municipio", "").strip()
        ano = self.request.GET.get("ano", "")
        if uf:
            consulta = consulta.filter(uf=uf)
        if municipio:
            consulta = consulta.filter(municipio__iexact=municipio)
        if ano.isdigit():
            consulta = consulta.filter(ano=int(ano))
        return consulta

    @override
    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        totais = self.object_list.aggregate(previsto=Sum("valor_previsto"), executado=Sum("valor_executado"))
        previsto = totais["previsto"] or Decimal("0")
        executado = totais["executado"] or Decimal("0")
        contexto["total_previsto"] = previsto
        contexto["total_executado"] = executado
        contexto["percentual_total"] = (
            (executado / previsto * 100).quantize(Decimal("0.1")) if previsto else Decimal("0")
        )
        contexto["ufs"] = UF_CHOICES
        contexto["anos"] = (
            IndicadorOrcamentario.objects.order_by("-ano").values_list("ano", flat=True).distinct()
        )
        return contexto


class IndicadorCreateView(FormularioMixin, CreateView):
    model = IndicadorOrcamentario
    form_class = IndicadorOrcamentarioForm
    titulo = "Cadastrar indicador"
    success_message = "Indicador cadastrado."
    success_url = reverse_lazy("core:painel")


class IndicadorUpdateView(FormularioMixin, UpdateView):
    model = IndicadorOrcamentario
    form_class = IndicadorOrcamentarioForm
    titulo = "Editar indicador"
    success_message = "Indicador atualizado."
    success_url = reverse_lazy("core:painel")


class IndicadorDeleteView(ExclusaoMixin, DeleteView):
    model = IndicadorOrcamentario
    success_url = reverse_lazy("core:painel")
    success_message = "Indicador excluído."
