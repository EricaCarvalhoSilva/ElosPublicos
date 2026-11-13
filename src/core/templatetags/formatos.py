from decimal import Decimal, InvalidOperation

from django import template

from core.dominio.elegibilidade import formatarReais

register = template.Library()


@register.filter
def reais(valor) -> str:
    """Uso no template: {{ valor|reais }} → R$ 1.234,56"""
    try:
        return formatarReais(Decimal(valor))
    except (InvalidOperation, TypeError, ValueError):
        return "—"


@register.filter
def limitarPercentual(valor) -> str:
    """Largura de barra entre 0 e 100, com ponto decimal (para CSS)."""
    try:
        numero = max(Decimal("0"), min(Decimal(valor), Decimal("100")))
    except (InvalidOperation, TypeError, ValueError):
        numero = Decimal("0")
    return f"{numero:.1f}"
