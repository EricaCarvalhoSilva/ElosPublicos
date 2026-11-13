# DER — Diagrama Entidade-Relacionamento

Corresponde ao script `database/schema.sql`.

```mermaid
erDiagram
    CIDADAO ||--|| NUCLEO_FAMILIAR : "é responsável por"
    NUCLEO_FAMILIAR ||--o{ MEMBRO_FAMILIAR : "é composto por"
    CIDADAO ||--o{ SOLICITACAO : "faz"
    PROGRAMA_SOCIAL ||--o{ SOLICITACAO : "recebe"
    REDE_APOIO ||--o{ REDE_APOIO_MEMBROS : "tem"
    CIDADAO ||--o{ REDE_APOIO_MEMBROS : "participa"
    REDE_APOIO ||--o{ POSTAGEM_APOIO : "contém"
    CIDADAO ||--o{ POSTAGEM_APOIO : "publica"
    ORGANIZACAO ||--o{ PUBLICACAO_ORGANIZACAO : "publica"

    CIDADAO {
        bigint id PK
        varchar nome_completo
        varchar cpf UK
        varchar email
        varchar telefone
        varchar endereco
        varchar municipio
        varchar uf
        numeric renda_familiar_declarada
        timestamptz criado_em
        timestamptz atualizado_em
    }
    ORGANIZACAO {
        bigint id PK
        varchar nome_completo
        varchar cnpj UK "pode ser nulo"
        varchar tipo
        text descricao
        varchar telefone
        varchar municipio
        varchar uf
    }
    NUCLEO_FAMILIAR {
        bigint id PK
        bigint responsavel_id FK,UK
    }
    MEMBRO_FAMILIAR {
        bigint id PK
        bigint nucleo_id FK
        varchar nome_completo
        varchar parentesco
        date data_nascimento
    }
    PROGRAMA_SOCIAL {
        bigint id PK
        varchar nome
        varchar esfera
        varchar uf
        varchar municipio
        varchar orgao_responsavel
        text criterios_elegibilidade
        text documentacao_necessaria
        numeric renda_per_capita_maxima
        boolean ativo
    }
    SOLICITACAO {
        bigint id PK
        bigint cidadao_id FK
        bigint programa_id FK
        varchar orgao
        varchar numero_protocolo
        varchar status
        text observacao
        timestamptz data_registro
        timestamptz atualizado_em
    }
    REDE_APOIO {
        bigint id PK
        varchar nome
        text descricao
        varchar municipio
        varchar uf
    }
    REDE_APOIO_MEMBROS {
        bigint id PK
        bigint redeapoio_id FK
        bigint cidadao_id FK
    }
    POSTAGEM_APOIO {
        bigint id PK
        bigint rede_id FK
        bigint autor_id FK
        varchar titulo
        text descricao
        varchar natureza
        varchar tipo
        boolean ativa
    }
    PUBLICACAO_ORGANIZACAO {
        bigint id PK
        bigint organizacao_id FK
        varchar tipo
        varchar titulo
        text descricao
        timestamptz data_evento
        varchar local
        varchar link_inscricao
    }
    INDICADOR_ORCAMENTARIO {
        bigint id PK
        varchar municipio
        varchar uf
        varchar acao
        int ano
        numeric valor_previsto
        numeric valor_executado
        varchar fonte
    }
```

`INDICADOR_ORCAMENTARIO` não se relaciona com outras tabelas: é dado público ligado ao município (`municipio` + `uf`).
