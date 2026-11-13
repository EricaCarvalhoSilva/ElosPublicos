"""Validação de documentos brasileiros (Python puro, sem Django)."""
import re


def somenteDigitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def cpfValido(cpf: str) -> bool:
    """Confere os dois dígitos verificadores do CPF."""
    digitos = somenteDigitos(cpf)
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    for posicao in (9, 10):
        soma = sum(int(digitos[i]) * (posicao + 1 - i) for i in range(posicao))
        verificador = (soma * 10) % 11 % 10
        if verificador != int(digitos[posicao]):
            return False
    return True


def mascararCpf(cpf: str) -> str:
    """Mostra só o miolo do CPF (proteção de dados pessoais / LGPD)."""
    d = somenteDigitos(cpf)
    if len(d) != 11:
        return "CPF não informado"
    return f"***.{d[3:6]}.{d[6:9]}-**"
