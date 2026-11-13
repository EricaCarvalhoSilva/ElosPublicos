"""
Testes automatizados. Rodar com:  python manage.py test core
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from core.dominio.documentos import cpfValido
from core.dominio.elegibilidade import (
    PerfilFamiliar,
    RegraElegibilidade,
    RegraRendaPerCapita,
)
from core.management.commands.popular_dados import gerarCpf
from core.models import (
    Cidadao,
    MembroFamiliar,
    Organizacao,
    PostagemApoio,
    ProgramaSocial,
    Publicacao,
    PublicacaoOrganizacao,
    RedeApoio,
    Solicitacao,
    Usuario,
)

CPF_VALIDO = gerarCpf("123456789")


def criarCidadao(**extras) -> Cidadao:
    dados = dict(
        nome_completo="Maria Teste", cpf=CPF_VALIDO, telefone="44999990000",
        endereco="Rua A, 1", municipio="Maringá", uf="PR",
        renda_familiar_declarada=Decimal("800.00"),
    )
    dados.update(extras)
    return Cidadao.objects.create(**dados)


class DominioTests(SimpleTestCase):
    def test_regraAbstrataNaoPodeSerInstanciada(self):
        with self.assertRaises(TypeError):
            RegraElegibilidade()

    def test_rendaPerCapita(self):
        perfil = PerfilFamiliar(Decimal("800"), 4, "PR", "Maringá")
        self.assertEqual(perfil.rendaPerCapita, Decimal("200.00"))
        self.assertTrue(RegraRendaPerCapita(Decimal("218")).avaliar(perfil).atendida)
        self.assertFalse(RegraRendaPerCapita(Decimal("150")).avaliar(perfil).atendida)

    def test_validacaoCpf(self):
        self.assertTrue(cpfValido(CPF_VALIDO))
        self.assertFalse(cpfValido("11111111111"))


class PilaresPooTests(TestCase):
    def test_classesAbstratasDoModelo(self):
        with self.assertRaises(TypeError):
            Usuario()
        with self.assertRaises(TypeError):
            Publicacao()

    def test_heranca(self):
        self.assertTrue(issubclass(Cidadao, Usuario))
        self.assertTrue(issubclass(Organizacao, Usuario))
        self.assertTrue(issubclass(PostagemApoio, Publicacao))
        self.assertTrue(issubclass(PublicacaoOrganizacao, Publicacao))

    def test_polimorfismo(self):
        cidadao = criarCidadao()
        organizacao = Organizacao.objects.create(
            nome_completo="ONG Teste", tipo="ONG", telefone="1", municipio="Maringá", uf="PR"
        )
        usuarios: list[Usuario] = [cidadao, organizacao]
        respostas = [u.podePublicarOportunidades() for u in usuarios]
        self.assertEqual(respostas, [False, True])
        self.assertEqual(cidadao.tipoPerfil(), "Cidadão")
        self.assertEqual(organizacao.tipoPerfil(), "ONG")

    def test_composicaoNucleoFamiliar(self):
        cidadao = criarCidadao()
        nucleo = cidadao.obterNucleo()
        MembroFamiliar.objects.create(nucleo=nucleo, nome_completo="Filho", parentesco="FILHO")
        MembroFamiliar.objects.create(nucleo=nucleo, nome_completo="Filha", parentesco="FILHO")
        self.assertEqual(cidadao.quantidadePessoas(), 3)
        self.assertEqual(cidadao.rendaPerCapita(), Decimal("266.67"))
        cidadao.delete()
        self.assertEqual(MembroFamiliar.objects.count(), 0)


class RegrasDeNegocioTests(TestCase):
    def setUp(self):
        self.cidadao = criarCidadao()
        self.programa = ProgramaSocial.objects.create(
            nome="Programa X", esfera="FEDERAL", orgao_responsavel="CRAS", descricao="d",
            criterios_elegibilidade="c", documentacao_necessaria="doc",
            renda_per_capita_maxima=Decimal("1000"),
        )

    def test_naoPermiteDuasSolicitacoesAbertas(self):
        Solicitacao.objects.create(cidadao=self.cidadao, programa=self.programa, orgao="CRAS")
        segunda = Solicitacao(cidadao=self.cidadao, programa=self.programa, orgao="CRAS")
        with self.assertRaises(ValidationError):
            segunda.full_clean()

    def test_programaMunicipalExigeMunicipio(self):
        programa = ProgramaSocial(
            nome="Y", esfera="MUNICIPAL", uf="PR", orgao_responsavel="o", descricao="d",
            criterios_elegibilidade="c", documentacao_necessaria="d",
        )
        with self.assertRaises(ValidationError):
            programa.full_clean()

    def test_consultaPorRegiao(self):
        ProgramaSocial.objects.create(
            nome="Só SP", esfera="ESTADUAL", uf="SP", orgao_responsavel="o", descricao="d",
            criterios_elegibilidade="c", documentacao_necessaria="d",
        )
        nomes = set(ProgramaSocial.disponiveisPara("PR", "Maringá").values_list("nome", flat=True))
        self.assertEqual(nomes, {"Programa X"})

    def test_soMembroPublicaNaRede(self):
        rede = RedeApoio.objects.create(nome="Rede", municipio="Maringá", uf="PR")
        postagem = PostagemApoio(
            rede=rede, autor=self.cidadao, natureza="OFERTA", tipo="CARONA",
            titulo="Carona", descricao="d",
        )
        with self.assertRaises(ValidationError):
            postagem.full_clean()
        rede.membros.add(self.cidadao)
        postagem.full_clean()


class CrudCidadaoTests(TestCase):
    """CRUD completo da entidade principal pelas telas web."""

    def setUp(self):
        self.usuario = get_user_model().objects.create_user("atendente", password="senha12345")
        self.client.force_login(self.usuario)

    def dadosFormulario(self, **extras) -> dict:
        dados = {
            "nome_completo": "José da Silva", "cpf": CPF_VALIDO, "email": "",
            "telefone": "44 99999-1111", "endereco": "Rua B, 2", "municipio": "Maringá",
            "uf": "PR", "renda_familiar_declarada": "1200.00",
        }
        dados.update(extras)
        return dados

    def test_criarLerAtualizarExcluir(self):
        # Create (aceita CPF com pontuação)
        cpfFormatado = f"{CPF_VALIDO[:3]}.{CPF_VALIDO[3:6]}.{CPF_VALIDO[6:9]}-{CPF_VALIDO[9:]}"
        resposta = self.client.post(reverse("core:cidadao-novo"), self.dadosFormulario(cpf=cpfFormatado))
        self.assertEqual(resposta.status_code, 302)
        cidadao = Cidadao.objects.get()
        self.assertEqual(cidadao.cpf, CPF_VALIDO)
        # Read
        self.assertContains(self.client.get(reverse("core:cidadao-lista")), "José da Silva")
        self.assertContains(self.client.get(cidadao.get_absolute_url()), "José da Silva")
        # Update
        self.client.post(
            reverse("core:cidadao-editar", args=[cidadao.pk]),
            self.dadosFormulario(nome_completo="José da Silva Souza"),
        )
        cidadao.refresh_from_db()
        self.assertEqual(cidadao.nome_completo, "José da Silva Souza")
        # Delete
        self.client.post(reverse("core:cidadao-excluir", args=[cidadao.pk]))
        self.assertFalse(Cidadao.objects.exists())

    def test_cpfInvalidoNaoGrava(self):
        resposta = self.client.post(reverse("core:cidadao-novo"), self.dadosFormulario(cpf="11111111111"))
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Cidadao.objects.exists())

    def test_cnpjFormatadoNaOrganizacao(self):
        resposta = self.client.post(reverse("core:organizacao-nova"), {
            "nome_completo": "Associação Teste", "tipo": "ASSOCIACAO", "cnpj": "11.222.333/0001-81",
            "email": "", "telefone": "44 3025-1234", "municipio": "Maringá", "uf": "PR", "descricao": "",
        })
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Organizacao.objects.get().cnpj, "11222333000181")

    def test_paginasAbrem(self):
        for nome in ["core:inicio", "core:programa-lista", "core:mural", "core:painel",
                     "core:solicitacao-lista", "core:rede-lista", "core:organizacao-lista"]:
            self.assertEqual(self.client.get(reverse(nome)).status_code, 200, nome)


class ApiTests(TestCase):
    def setUp(self):
        self.api = APIClient()
        self.api.force_authenticate(get_user_model().objects.create_user("api", password="senha12345"))

    def test_crudCidadaoPelaApi(self):
        resposta = self.api.post("/api/cidadaos/", {
            "nome_completo": "Ana API", "cpf": CPF_VALIDO, "telefone": "1", "endereco": "Rua C",
            "municipio": "Maringá", "uf": "PR", "renda_familiar_declarada": "500.00",
        }, format="json")
        self.assertEqual(resposta.status_code, 201, resposta.content)
        id_ = resposta.data["id"]
        self.assertEqual(self.api.get(f"/api/cidadaos/{id_}/").status_code, 200)
        self.assertEqual(self.api.patch(f"/api/cidadaos/{id_}/", {"telefone": "2"}, format="json").status_code, 200)
        self.assertEqual(self.api.delete(f"/api/cidadaos/{id_}/").status_code, 204)

    def test_semLoginNaoVeCidadaos(self):
        self.assertIn(APIClient().get("/api/cidadaos/").status_code, (401, 403))
