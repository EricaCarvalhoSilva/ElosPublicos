"""
Popula o banco com dados de demonstração.

Uso:  python manage.py popular_dados

Os programas federais usam as regras gerais divulgadas pelo governo, com
valores de referência que mudam com o salário mínimo: confira no gov.br
antes de usar de verdade. Programas estaduais/municipais, pessoas,
organizações e indicadores são fictícios.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.compat import override
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
)


def gerarCpf(base: str) -> str:
    """Completa 9 dígitos com os verificadores, gerando um CPF válido de teste."""
    digitos = [int(d) for d in base]
    for tamanho in (9, 10):
        soma = sum(d * (tamanho + 1 - i) for i, d in enumerate(digitos[:tamanho]))
        digitos.append((soma * 10) % 11 % 10)
    return "".join(map(str, digitos))


class Command(BaseCommand):
    help = "Popula o banco com dados de demonstração do ElosPúblicos."

    @override
    def handle(self, *args, **options) -> None:
        self._criarUsuarioDemo()
        if ProgramaSocial.objects.exists():
            self.stdout.write(self.style.WARNING("O banco já tem dados. Nada foi alterado."))
            return
        with transaction.atomic():
            programas = self._criarProgramas()
            cidadaos = self._criarCidadaos()
            self._criarSolicitacoes(cidadaos, programas)
            self._criarRedes(cidadaos)
            self._criarOrganizacoes()
            self._criarIndicadores()
        self.stdout.write(self.style.SUCCESS("Dados de demonstração criados."))

    def _criarUsuarioDemo(self) -> None:
        Usuario = get_user_model()
        if not Usuario.objects.filter(username="admin").exists():
            Usuario.objects.create_superuser("admin", "admin@exemplo.com", "admin123")
            self.stdout.write("Usuário de demonstração: admin / admin123")

    def _criarProgramas(self) -> dict[str, ProgramaSocial]:
        dados = [
            dict(
                nome="Bolsa Família",
                esfera="FEDERAL",
                orgao_responsavel="CRAS (inscrição no CadÚnico)",
                descricao="Transferência de renda mensal para famílias em situação de pobreza.",
                criterios_elegibilidade="Família inscrita no CadÚnico com renda por pessoa dentro do limite do programa.",
                documentacao_necessaria="CPF ou título de eleitor do responsável familiar.\nDocumento de todas as pessoas da casa.\nComprovante de endereço, se tiver.",
                renda_per_capita_maxima=Decimal("218.00"),
                link_oficial="https://www.gov.br/mds/pt-br/acoes-e-programas/bolsa-familia",
            ),
            dict(
                nome="Benefício de Prestação Continuada (BPC)",
                esfera="FEDERAL",
                orgao_responsavel="INSS, com inscrição prévia no CadÚnico",
                descricao="Um salário mínimo por mês para idosos a partir de 65 anos e pessoas com deficiência de baixa renda.",
                criterios_elegibilidade="Idoso com 65 anos ou mais, ou pessoa com deficiência, com renda por pessoa de até 1/4 do salário mínimo.",
                documentacao_necessaria="Documento com foto e CPF de todas as pessoas da casa.\nLaudos médicos, no caso de deficiência.",
                renda_per_capita_maxima=Decimal("379.50"),
                link_oficial="https://www.gov.br/inss/pt-br/direitos-e-deveres/beneficios-assistenciais",
            ),
            dict(
                nome="Tarifa Social de Energia Elétrica",
                esfera="FEDERAL",
                orgao_responsavel="Distribuidora de energia, com cadastro no CadÚnico",
                descricao="Desconto na conta de luz para famílias de baixa renda.",
                criterios_elegibilidade="Família no CadÚnico com renda por pessoa de até meio salário mínimo, ou com integrante que recebe BPC.",
                documentacao_necessaria="Número do NIS.\nConta de luz em nome de alguém da família.",
                renda_per_capita_maxima=Decimal("759.00"),
            ),
            dict(
                nome="Renda Cidadã Estadual (exemplo fictício)",
                esfera="ESTADUAL",
                uf="PR",
                orgao_responsavel="Secretaria estadual de assistência social",
                descricao="Programa fictício para demonstrar a consulta por estado.",
                criterios_elegibilidade="Famílias residentes no estado com renda por pessoa de até R$ 300,00.",
                documentacao_necessaria="RG e CPF.\nComprovante de residência no estado.",
                renda_per_capita_maxima=Decimal("300.00"),
            ),
            dict(
                nome="Cesta Básica Municipal (exemplo fictício)",
                esfera="MUNICIPAL",
                uf="PR",
                municipio="Maringá",
                orgao_responsavel="CRAS do bairro",
                descricao="Programa fictício para demonstrar a consulta por município.",
                criterios_elegibilidade="Moradores do município com renda por pessoa de até R$ 400,00.",
                documentacao_necessaria="RG, CPF e comprovante de endereço no município.",
                renda_per_capita_maxima=Decimal("400.00"),
            ),
        ]
        return {d["nome"]: ProgramaSocial.objects.create(**d) for d in dados}

    def _criarCidadaos(self) -> list[Cidadao]:
        pessoas = [
            ("Maria Aparecida dos Santos", "123456789", "Rua das Acácias, 120 - Jardim Alvorada", Decimal("850.00")),
            ("João Batista Ferreira", "987654321", "Av. Colombo, 4500 - Zona 7", Decimal("2400.00")),
            ("Ana Clara Oliveira", "456123789", "Rua Pioneiro João Pinto, 33 - Parque das Grevíleas", Decimal("600.00")),
        ]
        cidadaos = []
        for nome, baseCpf, endereco, renda in pessoas:
            cidadao = Cidadao.objects.create(
                nome_completo=nome,
                cpf=gerarCpf(baseCpf),
                telefone="(44) 99999-0000",
                endereco=endereco,
                municipio="Maringá",
                uf="PR",
                renda_familiar_declarada=renda,
            )
            cidadaos.append(cidadao)

        nucleoMaria = cidadaos[0].obterNucleo()
        MembroFamiliar.objects.create(nucleo=nucleoMaria, nome_completo="Pedro dos Santos", parentesco="FILHO", data_nascimento=date(2014, 5, 2))
        MembroFamiliar.objects.create(nucleo=nucleoMaria, nome_completo="Luiza dos Santos", parentesco="FILHO", data_nascimento=date(2017, 9, 21))
        MembroFamiliar.objects.create(nucleo=nucleoMaria, nome_completo="Antônio Carlos dos Santos", parentesco="CONJUGE")
        nucleoAna = cidadaos[2].obterNucleo()
        MembroFamiliar.objects.create(nucleo=nucleoAna, nome_completo="Benedita Oliveira", parentesco="PAI_MAE", data_nascimento=date(1955, 1, 10))
        return cidadaos

    def _criarSolicitacoes(self, cidadaos: list[Cidadao], programas: dict[str, ProgramaSocial]) -> None:
        Solicitacao.objects.create(
            cidadao=cidadaos[0], programa=programas["Bolsa Família"], orgao="CRAS",
            numero_protocolo="CRAS-2026-00412", status="EM_ANALISE",
            observacao="Entrevista do CadÚnico feita. Aguardando análise.",
        )
        Solicitacao.objects.create(
            cidadao=cidadaos[2], programa=programas["Tarifa Social de Energia Elétrica"], orgao="CADUNICO",
            status="PENDENTE_DOCUMENTOS", observacao="Falta a conta de luz em nome de alguém da família.",
        )

    def _criarRedes(self, cidadaos: list[Cidadao]) -> None:
        rede = RedeApoio.objects.create(
            nome="Vizinhança Solidária Jardim Alvorada",
            descricao="Doações, trocas de serviço e caronas entre moradores do bairro.",
            municipio="Maringá",
            uf="PR",
        )
        rede.membros.set(cidadaos)
        PostagemApoio.objects.create(
            rede=rede, autor=cidadaos[1], natureza="OFERTA", tipo="CARONA",
            titulo="Carona para o centro às terças",
            descricao="Saio às 7h do Jardim Alvorada e passo pelo terminal. Cabem 3 pessoas.",
        )
        PostagemApoio.objects.create(
            rede=rede, autor=cidadaos[0], natureza="PEDIDO", tipo="DOACAO",
            titulo="Material escolar para duas crianças",
            descricao="Preciso de cadernos e mochila para meus filhos (3º e 6º ano).",
        )
        PostagemApoio.objects.create(
            rede=rede, autor=cidadaos[2], natureza="OFERTA", tipo="TROCA_SERVICO",
            titulo="Faço bainha e pequenos consertos de roupa",
            descricao="Em troca, procuro ajuda para consertar um chuveiro.",
        )

    def _criarOrganizacoes(self) -> None:
        coletivo = Organizacao.objects.create(
            nome_completo="Coletivo Mãos que Tecem", tipo="COLETIVO", cnpj=None, telefone="(44) 98888-0000",
            municipio="Maringá", uf="PR", descricao="Coletivo de costureiras que oferece formação gratuita.",
        )
        ong = Organizacao.objects.create(
            nome_completo="Instituto Raízes do Bairro", tipo="ONG", cnpj="12345678000190",
            telefone="(44) 3333-0000", municipio="Maringá", uf="PR",
            descricao="Apoio a famílias em situação de vulnerabilidade.",
        )
        agora = timezone.now()
        PublicacaoOrganizacao.objects.create(
            organizacao=coletivo, tipo="OFICINA", titulo="Oficina gratuita de corte e costura",
            descricao="Oito encontros, com material incluso e certificado.",
            data_evento=agora + timedelta(days=10), local="Salão da Associação de Moradores",
        )
        PublicacaoOrganizacao.objects.create(
            organizacao=ong, tipo="EDITAL", titulo="Edital de auxílio para pequenos reparos em casa",
            descricao="Apoio de até R$ 1.500,00 para reformas urgentes, como telhado e instalação elétrica.",
        )
        PublicacaoOrganizacao.objects.create(
            organizacao=ong, tipo="EVENTO", titulo="Mutirão de orientação sobre o CadÚnico",
            descricao="Equipe tira dúvidas e ajuda a organizar os documentos para a entrevista.",
            data_evento=agora + timedelta(days=4), local="Praça central do bairro",
        )

    def _criarIndicadores(self) -> None:
        linhas = [
            ("Proteção Social Básica (CRAS)", 2025, "4800000.00", "4150000.00"),
            ("Benefícios eventuais (auxílio natalidade, funeral, cestas)", 2025, "1200000.00", "610000.00"),
            ("Segurança alimentar e restaurante popular", 2025, "2300000.00", "1980000.00"),
            ("Proteção Social Básica (CRAS)", 2026, "5100000.00", "2900000.00"),
            ("Benefícios eventuais (auxílio natalidade, funeral, cestas)", 2026, "1300000.00", "420000.00"),
        ]
        for acao, ano, previsto, executado in linhas:
            IndicadorOrcamentario.objects.create(
                municipio="Maringá", uf="PR", acao=acao, ano=ano,
                valor_previsto=Decimal(previsto), valor_executado=Decimal(executado),
                fonte="Dados fictícios para demonstração",
            )
