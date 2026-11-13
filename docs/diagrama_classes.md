# Diagrama de Classes — ElosPúblicos

Diagrama em Mermaid (o GitHub desenha automaticamente). Corresponde às classes de `src/core/models.py` e `src/core/dominio/elegibilidade.py`.

```mermaid
classDiagram
    direction TB

    class Usuario {
        <<abstract>>
        +nome_completo: str
        +email: str
        +telefone: str
        +municipio: str
        +uf: str
        +tipoPerfil()* str
        +podePublicarOportunidades()* bool
        +documentoExibicao()* str
        +apresentacao() str
    }
    class Cidadao {
        +cpf: str
        +endereco: str
        +renda_familiar_declarada: Decimal
        +tipoPerfil() str
        +podePublicarOportunidades() bool
        +documentoExibicao() str
        +obterNucleo() NucleoFamiliar
        +perfilFamiliar() PerfilFamiliar
        +rendaPerCapita() Decimal
    }
    class Organizacao {
        +cnpj: str
        +tipo: TipoOrganizacao
        +descricao: str
        +tipoPerfil() str
        +podePublicarOportunidades() bool
        +documentoExibicao() str
    }
    Usuario <|-- Cidadao
    Usuario <|-- Organizacao

    class NucleoFamiliar {
        +quantidadePessoas() int
    }
    class MembroFamiliar {
        +nome_completo: str
        +parentesco: Parentesco
        +data_nascimento: date
    }
    Cidadao "1" -- "1" NucleoFamiliar : responsável
    NucleoFamiliar "1" *-- "0..*" MembroFamiliar : composição

    class ProgramaSocial {
        +nome: str
        +esfera: Esfera
        +uf: str
        +municipio: str
        +renda_per_capita_maxima: Decimal
        +disponiveisPara(uf, municipio)$ QuerySet
        +regras() list~RegraElegibilidade~
        +avaliarElegibilidade(cidadao) ResultadoElegibilidade
    }
    class Solicitacao {
        +orgao: Orgao
        +numero_protocolo: str
        +status: Status
        +estaEmAberto() bool
        +clean()
    }
    Cidadao "1" -- "0..*" Solicitacao
    ProgramaSocial "1" -- "0..*" Solicitacao

    class RedeApoio {
        +nome: str
        +municipio: str
        +uf: str
    }
    RedeApoio "0..*" o-- "0..*" Cidadao : membros

    class Publicacao {
        <<abstract>>
        +titulo: str
        +descricao: str
        +ativa: bool
        +categoriaExibicao()* str
        +autorExibicao()* str
        +validarRegras()*
        +clean()
        +resumo() dict
    }
    class PostagemApoio {
        +natureza: Natureza
        +tipo: TipoApoio
        +categoriaExibicao() str
        +autorExibicao() str
        +validarRegras()
    }
    class PublicacaoOrganizacao {
        +tipo: TipoPublicacao
        +data_evento: datetime
        +local: str
        +categoriaExibicao() str
        +autorExibicao() str
        +validarRegras()
    }
    Publicacao <|-- PostagemApoio
    Publicacao <|-- PublicacaoOrganizacao
    RedeApoio "1" *-- "0..*" PostagemApoio
    Cidadao "1" -- "0..*" PostagemApoio : autor
    Organizacao "1" -- "0..*" PublicacaoOrganizacao

    class IndicadorOrcamentario {
        +municipio: str
        +uf: str
        +acao: str
        +ano: int
        +valor_previsto: Decimal
        +valor_executado: Decimal
        +percentualExecucao() Decimal
        +valorNaoExecutado() Decimal
    }

    class RegraElegibilidade {
        <<abstract>>
        +avaliar(perfil)* ResultadoRegra
        +descrever()* str
    }
    class RegraRendaPerCapita {
        +limite: Decimal
        +avaliar(perfil) ResultadoRegra
        +descrever() str
    }
    class RegraAbrangenciaRegional {
        +esfera: str
        +uf: str
        +municipio: str
        +avaliar(perfil) ResultadoRegra
        +descrever() str
    }
    class AvaliadorElegibilidade {
        +regras: list~RegraElegibilidade~
        +avaliar(perfil) ResultadoElegibilidade
    }
    RegraElegibilidade <|-- RegraRendaPerCapita
    RegraElegibilidade <|-- RegraAbrangenciaRegional
    AvaliadorElegibilidade "1" o-- "1..*" RegraElegibilidade
    ProgramaSocial ..> AvaliadorElegibilidade : usa
```

## Onde estão os pilares de POO

| Pilar | Onde |
|---|---|
| Classe abstrata | `Usuario`, `Publicacao` (models) e `RegraElegibilidade` (domínio): usam `ABCMeta` e `@abstractmethod`, não podem ser instanciadas |
| Herança | `Cidadao` e `Organizacao` ← `Usuario`; `PostagemApoio` e `PublicacaoOrganizacao` ← `Publicacao`; `RegraRendaPerCapita` e `RegraAbrangenciaRegional` ← `RegraElegibilidade`; todas as views herdam das views genéricas do Django |
| Polimorfismo (`@override`) | Métodos sobrescritos com o decorador `@override` (equivalente ao `@Override` do Java). Ex.: o mural chama `resumo()` em postagens e publicações sem saber a classe; o avaliador chama `avaliar()` em cada regra |
| Composição 1:N | `NucleoFamiliar` ◆ `MembroFamiliar` (apagou o núcleo, apagou os membros) e `RedeApoio` ◆ `PostagemApoio` |
| Encapsulamento | Regras de negócio dentro das classes (`clean()`, `validarRegras()`, `estaEmAberto()`), CPF exibido mascarado por `documentoExibicao()` |
