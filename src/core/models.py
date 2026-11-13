"""
Modelos do ElosPúblicos (camada Model do MVC).

Pilares de POO aplicados aqui:

- Classe abstrata: `Usuario` e `Publicacao` são abstratas de verdade. Usam a
  metaclasse `ModeloAbstratoMeta`, que junta o ABCMeta do Python com a
  metaclasse do Django; por isso têm métodos marcados com @abstractmethod
  e não podem ser instanciadas nem viram tabela no banco.
- Herança: `Cidadao` e `Organizacao` herdam de `Usuario`;
  `PostagemApoio` e `PublicacaoOrganizacao` herdam de `Publicacao`.
- Polimorfismo: as subclasses sobrescrevem (@override) os métodos abstratos
  e cada uma responde de um jeito (ex.: `podePublicarOportunidades()`).
- Composição 1:N: um `NucleoFamiliar` é composto por vários
  `MembroFamiliar`. Se o núcleo é apagado, os membros vão junto (CASCADE).

Convenção de nomes: classes em PascalCase, métodos em camelCase e campos
persistidos em snake_case (porque viram colunas SQL em /database/schema.sql).
"""
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse

from core.compat import override
from core.dominio.documentos import cpfValido, mascararCpf, somenteDigitos
from core.dominio.elegibilidade import (
    AvaliadorElegibilidade,
    PerfilFamiliar,
    RegraAbrangenciaRegional,
    RegraElegibilidade,
    RegraRendaPerCapita,
    ResultadoElegibilidade,
)

UF_CHOICES = [
    (uf, uf)
    for uf in (
        "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO"
    ).split()
]


def validarCpf(valor: str) -> None:
    if not cpfValido(valor):
        raise ValidationError("CPF inválido. Confira os números digitados.")


class ModeloAbstratoMeta(ABCMeta, type(models.Model)):
    """Permite usar @abstractmethod em modelos abstratos do Django."""


# ---------------------------------------------------------------------------
# Usuários: classe abstrata + herança + polimorfismo
# ---------------------------------------------------------------------------
class Usuario(models.Model, metaclass=ModeloAbstratoMeta):
    """Base abstrata para quem usa a plataforma (não vira tabela)."""

    nome_completo = models.CharField("nome completo", max_length=150)
    email = models.EmailField("e-mail", blank=True)
    telefone = models.CharField("telefone", max_length=20)
    municipio = models.CharField("município", max_length=100)
    uf = models.CharField("UF", max_length=2, choices=UF_CHOICES)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["nome_completo"]

    @abstractmethod
    def tipoPerfil(self) -> str:
        """Nome do tipo de perfil, para exibição."""

    @abstractmethod
    def podePublicarOportunidades(self) -> bool:
        """Regra de negócio: só organizações publicam editais, oficinas e eventos."""

    @abstractmethod
    def documentoExibicao(self) -> str:
        """Documento de identificação no formato seguro para exibir."""

    def apresentacao(self) -> str:
        return f"{self.nome_completo} ({self.tipoPerfil()}) | {self.municipio}/{self.uf}"

    def __str__(self) -> str:
        return self.nome_completo


class Cidadao(Usuario):
    """Entidade principal do sistema (Requisito 1)."""

    cpf = models.CharField("CPF", max_length=11, unique=True, validators=[validarCpf])
    endereco = models.CharField("endereço", max_length=255)
    renda_familiar_declarada = models.DecimalField(
        "renda familiar declarada (R$/mês)",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta(Usuario.Meta):
        db_table = "cidadao"
        verbose_name = "cidadão"
        verbose_name_plural = "cidadãos"

    @override
    def tipoPerfil(self) -> str:
        return "Cidadão"

    @override
    def podePublicarOportunidades(self) -> bool:
        return False

    @override
    def documentoExibicao(self) -> str:
        return mascararCpf(self.cpf)

    @override
    def clean(self) -> None:
        super().clean()
        self.cpf = somenteDigitos(self.cpf)

    @override
    def save(self, *args, **kwargs) -> None:
        self.cpf = somenteDigitos(self.cpf)
        super().save(*args, **kwargs)
        # Todo cidadão tem um núcleo familiar, mesmo que more sozinho.
        self.obterNucleo()

    def obterNucleo(self) -> "NucleoFamiliar":
        """Devolve o núcleo familiar, criando se ainda não existir."""
        nucleo, _ = NucleoFamiliar.objects.get_or_create(responsavel=self)
        return nucleo

    def quantidadePessoas(self) -> int:
        return self.obterNucleo().quantidadePessoas()

    def perfilFamiliar(self) -> PerfilFamiliar:
        return PerfilFamiliar(
            rendaFamiliar=self.renda_familiar_declarada,
            quantidadePessoas=self.quantidadePessoas(),
            uf=self.uf,
            municipio=self.municipio,
        )

    def rendaPerCapita(self) -> Decimal:
        return self.perfilFamiliar().rendaPerCapita

    def get_absolute_url(self) -> str:
        return reverse("core:cidadao-detalhe", args=[self.pk])


class Organizacao(Usuario):
    """ONGs e coletivos que publicam oportunidades (Requisito 6)."""

    class TipoOrganizacao(models.TextChoices):
        ONG = "ONG", "ONG"
        COLETIVO = "COLETIVO", "Coletivo"
        ASSOCIACAO = "ASSOCIACAO", "Associação de moradores"

    cnpj = models.CharField("CNPJ", max_length=14, unique=True, null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TipoOrganizacao.choices)
    descricao = models.TextField("sobre a organização", blank=True)

    class Meta(Usuario.Meta):
        db_table = "organizacao"
        verbose_name = "organização"
        verbose_name_plural = "organizações"

    @override
    def tipoPerfil(self) -> str:
        return self.get_tipo_display()

    @override
    def podePublicarOportunidades(self) -> bool:
        return True

    @override
    def documentoExibicao(self) -> str:
        if not self.cnpj:
            return "Sem CNPJ (coletivo informal)"
        c = self.cnpj
        return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}"

    @override
    def clean(self) -> None:
        super().clean()
        if self.cnpj:
            self.cnpj = somenteDigitos(self.cnpj)
            if len(self.cnpj) != 14:
                raise ValidationError({"cnpj": "O CNPJ precisa ter 14 números."})
        else:
            self.cnpj = None

    def get_absolute_url(self) -> str:
        return reverse("core:organizacao-lista")


# ---------------------------------------------------------------------------
# Composição 1:N — Núcleo familiar é composto por membros
# ---------------------------------------------------------------------------
class NucleoFamiliar(models.Model):
    responsavel = models.OneToOneField(
        Cidadao, on_delete=models.CASCADE, related_name="nucleo_familiar"
    )

    class Meta:
        db_table = "nucleo_familiar"
        verbose_name = "núcleo familiar"
        verbose_name_plural = "núcleos familiares"

    def quantidadePessoas(self) -> int:
        """Responsável + membros cadastrados."""
        return 1 + self.membros.count()

    def __str__(self) -> str:
        return f"Família de {self.responsavel.nome_completo}"


class MembroFamiliar(models.Model):
    class Parentesco(models.TextChoices):
        CONJUGE = "CONJUGE", "Cônjuge ou companheiro(a)"
        FILHO = "FILHO", "Filho(a) ou enteado(a)"
        PAI_MAE = "PAI_MAE", "Pai ou mãe"
        IRMAO = "IRMAO", "Irmão(ã)"
        NETO = "NETO", "Neto(a)"
        OUTRO = "OUTRO", "Outro"

    nucleo = models.ForeignKey(NucleoFamiliar, on_delete=models.CASCADE, related_name="membros")
    nome_completo = models.CharField("nome completo", max_length=150)
    parentesco = models.CharField(max_length=10, choices=Parentesco.choices)
    data_nascimento = models.DateField("data de nascimento", null=True, blank=True)

    class Meta:
        db_table = "membro_familiar"
        verbose_name = "membro familiar"
        verbose_name_plural = "membros familiares"

    def __str__(self) -> str:
        return f"{self.nome_completo} ({self.get_parentesco_display()})"


# ---------------------------------------------------------------------------
# Programas sociais e solicitações (Requisitos 2 e 4)
# ---------------------------------------------------------------------------
class ProgramaSocial(models.Model):
    class Esfera(models.TextChoices):
        FEDERAL = "FEDERAL", "Federal"
        ESTADUAL = "ESTADUAL", "Estadual"
        MUNICIPAL = "MUNICIPAL", "Municipal"

    nome = models.CharField(max_length=150)
    esfera = models.CharField(max_length=10, choices=Esfera.choices)
    uf = models.CharField("UF", max_length=2, choices=UF_CHOICES, blank=True)
    municipio = models.CharField("município", max_length=100, blank=True)
    orgao_responsavel = models.CharField("onde solicitar", max_length=150)
    descricao = models.TextField("o que é")
    criterios_elegibilidade = models.TextField("quem tem direito")
    documentacao_necessaria = models.TextField("documentos necessários")
    renda_per_capita_maxima = models.DecimalField(
        "renda máxima por pessoa (R$)",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Deixe em branco se o programa não tiver limite de renda.",
    )
    link_oficial = models.URLField("página oficial", blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "programa_social"
        ordering = ["esfera", "nome"]
        verbose_name = "programa social"
        verbose_name_plural = "programas sociais"

    @override
    def clean(self) -> None:
        super().clean()
        if self.esfera in (self.Esfera.ESTADUAL, self.Esfera.MUNICIPAL) and not self.uf:
            raise ValidationError({"uf": "Programas estaduais e municipais precisam da UF."})
        if self.esfera == self.Esfera.MUNICIPAL and not self.municipio:
            raise ValidationError({"municipio": "Programas municipais precisam do município."})
        if self.esfera == self.Esfera.FEDERAL:
            self.uf, self.municipio = "", ""

    @classmethod
    def disponiveisPara(cls, uf: str, municipio: str) -> models.QuerySet:
        """Programas que valem para quem mora em municipio/uf."""
        return cls.objects.filter(ativo=True).filter(
            Q(esfera=cls.Esfera.FEDERAL)
            | Q(esfera=cls.Esfera.ESTADUAL, uf=uf)
            | Q(esfera=cls.Esfera.MUNICIPAL, uf=uf, municipio__iexact=municipio)
        )

    def regras(self) -> list[RegraElegibilidade]:
        regras: list[RegraElegibilidade] = [
            RegraAbrangenciaRegional(self.esfera, self.uf, self.municipio)
        ]
        if self.renda_per_capita_maxima is not None:
            regras.append(RegraRendaPerCapita(self.renda_per_capita_maxima))
        return regras

    def avaliarElegibilidade(self, cidadao: Cidadao) -> ResultadoElegibilidade:
        return AvaliadorElegibilidade(self.regras()).avaliar(cidadao.perfilFamiliar())

    def abrangencia(self) -> str:
        if self.esfera == self.Esfera.FEDERAL:
            return "Todo o Brasil"
        if self.esfera == self.Esfera.ESTADUAL:
            return f"Estado {self.uf}"
        return f"{self.municipio}/{self.uf}"

    def get_absolute_url(self) -> str:
        return reverse("core:programa-detalhe", args=[self.pk])

    def __str__(self) -> str:
        return f"{self.nome} ({self.get_esfera_display()})"


class Solicitacao(models.Model):
    class Orgao(models.TextChoices):
        CRAS = "CRAS", "CRAS"
        CREAS = "CREAS", "CREAS"
        CADUNICO = "CADUNICO", "CadÚnico"
        INSS = "INSS", "INSS"
        OUTRO = "OUTRO", "Outro órgão"

    class Status(models.TextChoices):
        REGISTRADA = "REGISTRADA", "Registrada"
        EM_ANALISE = "EM_ANALISE", "Em análise"
        PENDENTE_DOCUMENTOS = "PENDENTE_DOCUMENTOS", "Faltam documentos"
        DEFERIDA = "DEFERIDA", "Aprovada"
        INDEFERIDA = "INDEFERIDA", "Negada"

    STATUS_ABERTOS = (Status.REGISTRADA, Status.EM_ANALISE, Status.PENDENTE_DOCUMENTOS)

    cidadao = models.ForeignKey(Cidadao, on_delete=models.CASCADE, related_name="solicitacoes")
    programa = models.ForeignKey(
        ProgramaSocial, on_delete=models.PROTECT, related_name="solicitacoes"
    )
    orgao = models.CharField("órgão", max_length=10, choices=Orgao.choices)
    numero_protocolo = models.CharField("número de protocolo", max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REGISTRADA)
    observacao = models.TextField("observações", blank=True)
    data_registro = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "solicitacao"
        ordering = ["-atualizado_em"]
        verbose_name = "solicitação"
        verbose_name_plural = "solicitações"

    def estaEmAberto(self) -> bool:
        return self.status in self.STATUS_ABERTOS

    @override
    def clean(self) -> None:
        """Regra de negócio: não pode haver duas solicitações abertas do mesmo programa."""
        super().clean()
        if self.cidadao_id and self.programa_id and self.estaEmAberto():
            duplicada = (
                Solicitacao.objects.filter(
                    cidadao_id=self.cidadao_id,
                    programa_id=self.programa_id,
                    status__in=self.STATUS_ABERTOS,
                )
                .exclude(pk=self.pk)
                .exists()
            )
            if duplicada:
                raise ValidationError(
                    "Este cidadão já tem uma solicitação em aberto para este programa."
                )

    def __str__(self) -> str:
        return f"{self.programa.nome}: {self.get_status_display()}"


# ---------------------------------------------------------------------------
# Redes de apoio mútuo e publicações (Requisitos 3 e 6)
# ---------------------------------------------------------------------------
class RedeApoio(models.Model):
    nome = models.CharField(max_length=120)
    descricao = models.TextField("descrição", blank=True)
    municipio = models.CharField("município", max_length=100)
    uf = models.CharField("UF", max_length=2, choices=UF_CHOICES)
    membros = models.ManyToManyField(
        Cidadao, related_name="redes_apoio", blank=True, db_table="rede_apoio_membros"
    )
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rede_apoio"
        ordering = ["nome"]
        verbose_name = "rede de apoio"
        verbose_name_plural = "redes de apoio"

    def get_absolute_url(self) -> str:
        return reverse("core:rede-detalhe", args=[self.pk])

    def __str__(self) -> str:
        return f"{self.nome} ({self.municipio}/{self.uf})"


class Publicacao(models.Model, metaclass=ModeloAbstratoMeta):
    """Base abstrata de tudo que aparece no mural da comunidade."""

    titulo = models.CharField("título", max_length=150)
    descricao = models.TextField("descrição")
    ativa = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["-criado_em"]

    @abstractmethod
    def categoriaExibicao(self) -> str:
        """Categoria em linguagem simples (ex.: 'Oferta de carona')."""

    @abstractmethod
    def autorExibicao(self) -> str:
        """Quem publicou."""

    @abstractmethod
    def validarRegras(self) -> None:
        """Regras de negócio próprias de cada tipo de publicação."""

    @override
    def clean(self) -> None:
        # Template Method: a base chama a regra, cada subclasse implementa a sua.
        super().clean()
        self.validarRegras()

    def resumo(self) -> dict:
        return {
            "titulo": self.titulo,
            "categoria": self.categoriaExibicao(),
            "autor": self.autorExibicao(),
            "descricao": self.descricao,
            "data": self.criado_em,
            "tipo": type(self).__name__,
        }

    def __str__(self) -> str:
        return self.titulo


class PostagemApoio(Publicacao):
    class Natureza(models.TextChoices):
        OFERTA = "OFERTA", "Oferta"
        PEDIDO = "PEDIDO", "Pedido"

    class TipoApoio(models.TextChoices):
        DOACAO = "DOACAO", "doação"
        TROCA_SERVICO = "TROCA_SERVICO", "troca de serviço"
        CARONA = "CARONA", "carona solidária"

    rede = models.ForeignKey(RedeApoio, on_delete=models.CASCADE, related_name="postagens")
    autor = models.ForeignKey(Cidadao, on_delete=models.CASCADE, related_name="postagens")
    natureza = models.CharField(max_length=10, choices=Natureza.choices)
    tipo = models.CharField(max_length=20, choices=TipoApoio.choices)

    class Meta(Publicacao.Meta):
        db_table = "postagem_apoio"
        verbose_name = "postagem de apoio"
        verbose_name_plural = "postagens de apoio"

    @override
    def categoriaExibicao(self) -> str:
        return f"{self.get_natureza_display()} de {self.get_tipo_display()}"

    @override
    def autorExibicao(self) -> str:
        return self.autor.nome_completo

    @override
    def validarRegras(self) -> None:
        if self.autor_id and self.rede_id:
            if not self.rede.membros.filter(pk=self.autor_id).exists():
                raise ValidationError("Só quem participa da rede pode publicar nela.")


class PublicacaoOrganizacao(Publicacao):
    class TipoPublicacao(models.TextChoices):
        EDITAL = "EDITAL", "Edital de auxílio"
        OFICINA = "OFICINA", "Oficina de capacitação"
        EVENTO = "EVENTO", "Evento comunitário"

    organizacao = models.ForeignKey(
        Organizacao, on_delete=models.CASCADE, related_name="publicacoes"
    )
    tipo = models.CharField(max_length=10, choices=TipoPublicacao.choices)
    data_evento = models.DateTimeField("data e hora", null=True, blank=True)
    local = models.CharField(max_length=200, blank=True)
    link_inscricao = models.URLField("link de inscrição", blank=True)

    class Meta(Publicacao.Meta):
        db_table = "publicacao_organizacao"
        verbose_name = "publicação de organização"
        verbose_name_plural = "publicações de organizações"

    @override
    def categoriaExibicao(self) -> str:
        return self.get_tipo_display()

    @override
    def autorExibicao(self) -> str:
        return self.organizacao.nome_completo

    @override
    def validarRegras(self) -> None:
        if self.organizacao_id and not self.organizacao.podePublicarOportunidades():
            raise ValidationError("Este perfil não pode publicar oportunidades.")
        if self.tipo in (self.TipoPublicacao.OFICINA, self.TipoPublicacao.EVENTO):
            if not self.data_evento:
                raise ValidationError({"data_evento": "Oficinas e eventos precisam de data."})


# ---------------------------------------------------------------------------
# Indicadores de execução orçamentária (Requisito 5)
# ---------------------------------------------------------------------------
class IndicadorOrcamentario(models.Model):
    municipio = models.CharField("município", max_length=100)
    uf = models.CharField("UF", max_length=2, choices=UF_CHOICES)
    acao = models.CharField("ação ou política", max_length=150)
    ano = models.PositiveIntegerField()
    valor_previsto = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    valor_executado = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    fonte = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "indicador_orcamentario"
        ordering = ["-ano", "acao"]
        constraints = [
            models.UniqueConstraint(
                fields=["municipio", "uf", "acao", "ano"], name="indicador_unico_por_ano"
            )
        ]
        verbose_name = "indicador orçamentário"
        verbose_name_plural = "indicadores orçamentários"

    def percentualExecucao(self) -> Decimal:
        if not self.valor_previsto:
            return Decimal("0")
        return (self.valor_executado / self.valor_previsto * 100).quantize(Decimal("0.1"))

    def valorNaoExecutado(self) -> Decimal:
        return max(self.valor_previsto - self.valor_executado, Decimal("0"))

    def __str__(self) -> str:
        return f"{self.acao}: {self.municipio}/{self.uf} ({self.ano})"
