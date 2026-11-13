"""
Regras de elegibilidade a programas sociais (camada de domínio).

Este módulo é Python puro, sem dependência do Django, para deixar as regras
de negócio isoladas e testáveis. Ele demonstra:

- Classe abstrata: `RegraElegibilidade` (ABC com métodos abstratos).
- Herança: `RegraRendaPerCapita` e `RegraAbrangenciaRegional` herdam dela.
- Polimorfismo: o `AvaliadorElegibilidade` chama `avaliar()` em cada regra
  sem saber qual é a classe concreta; cada uma responde do seu jeito.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from core.compat import override


def formatarReais(valor: Decimal) -> str:
    """Formata um valor no padrão brasileiro (R$ 1.234,56)."""
    valor = Decimal(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    inteiro, centavos = f"{valor:.2f}".split(".")
    inteiroComPontos = f"{int(inteiro):,}".replace(",", ".")
    return f"R$ {inteiroComPontos},{centavos}"


@dataclass(frozen=True)
class PerfilFamiliar:
    """Dados mínimos de uma família usados para checar elegibilidade."""

    rendaFamiliar: Decimal
    quantidadePessoas: int
    uf: str
    municipio: str

    @property
    def rendaPerCapita(self) -> Decimal:
        pessoas = max(self.quantidadePessoas, 1)
        return (Decimal(self.rendaFamiliar) / pessoas).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )


@dataclass(frozen=True)
class ResultadoRegra:
    atendida: bool
    motivo: str


@dataclass
class ResultadoElegibilidade:
    resultados: list[ResultadoRegra] = field(default_factory=list)

    @property
    def elegivel(self) -> bool:
        return all(r.atendida for r in self.resultados)

    @property
    def pendencias(self) -> list[str]:
        return [r.motivo for r in self.resultados if not r.atendida]


class RegraElegibilidade(ABC):
    """Contrato que toda regra de elegibilidade precisa cumprir."""

    @abstractmethod
    def avaliar(self, perfil: PerfilFamiliar) -> ResultadoRegra:
        """Diz se o perfil atende à regra e explica o motivo."""

    @abstractmethod
    def descrever(self) -> str:
        """Texto curto, em linguagem simples, para mostrar ao cidadão."""


class RegraRendaPerCapita(RegraElegibilidade):
    def __init__(self, limite: Decimal) -> None:
        self.limite = Decimal(limite)

    @override
    def avaliar(self, perfil: PerfilFamiliar) -> ResultadoRegra:
        rendaPerCapita = perfil.rendaPerCapita
        if rendaPerCapita <= self.limite:
            return ResultadoRegra(
                True,
                f"Renda por pessoa ({formatarReais(rendaPerCapita)}) dentro do limite "
                f"de {formatarReais(self.limite)}.",
            )
        return ResultadoRegra(
            False,
            f"Renda por pessoa ({formatarReais(rendaPerCapita)}) acima do limite "
            f"de {formatarReais(self.limite)}.",
        )

    @override
    def descrever(self) -> str:
        return f"Renda por pessoa da família de até {formatarReais(self.limite)}."


class RegraAbrangenciaRegional(RegraElegibilidade):
    """Programas estaduais e municipais só valem para quem mora no local."""

    def __init__(self, esfera: str, uf: str = "", municipio: str = "") -> None:
        self.esfera = esfera
        self.uf = (uf or "").upper()
        self.municipio = (municipio or "").strip().lower()

    @override
    def avaliar(self, perfil: PerfilFamiliar) -> ResultadoRegra:
        if self.esfera == "FEDERAL":
            return ResultadoRegra(True, "Programa federal: vale em todo o Brasil.")
        if perfil.uf.upper() != self.uf:
            return ResultadoRegra(False, f"Programa disponível apenas no estado {self.uf}.")
        if self.esfera == "MUNICIPAL" and perfil.municipio.strip().lower() != self.municipio:
            return ResultadoRegra(False, "Programa disponível apenas para moradores do município.")
        return ResultadoRegra(True, "Você mora na região atendida pelo programa.")

    @override
    def descrever(self) -> str:
        if self.esfera == "FEDERAL":
            return "Disponível em todo o país."
        if self.esfera == "ESTADUAL":
            return f"Disponível para moradores do estado {self.uf}."
        return f"Disponível para moradores de {self.municipio.title()}/{self.uf}."


class AvaliadorElegibilidade:
    """Combina várias regras e devolve um resultado único."""

    def __init__(self, regras: list[RegraElegibilidade]) -> None:
        self.regras = regras

    def avaliar(self, perfil: PerfilFamiliar) -> ResultadoElegibilidade:
        return ResultadoElegibilidade([regra.avaliar(perfil) for regra in self.regras])
