# ElosPúblicos

**Acadêmicas:** Helen Alves da Cruz e Erica Cristiana Carvalho Silva | Análise e Desenvolvimento de Sistemas, turma ADSIS4S-N-A

Plataforma de acesso a direitos sociais e articulação comunitária — projeto da AEP, alinhado à **ODS 1: Erradicação da Pobreza**, com base na leitura estrutural da pobreza apresentada pela Senhorita Bira (canal *O Algoritmo da Imagem*).

## Sobre o projeto

O ElosPúblicos parte da ideia de que a pobreza não é resultado de falha individual, mas de barreiras estruturais — entre elas, a dificuldade de acesso à informação sobre direitos já existentes. O sistema centraliza informações sobre programas sociais, permite o acompanhamento de solicitações de assistência, conecta pessoas a redes comunitárias de apoio mútuo e expõe indicadores públicos de execução de políticas de combate à pobreza.

## Lista de Requisitos

- O sistema deve permitir o cadastro de cidadãos, com nome completo, CPF, endereço, telefone, renda familiar declarada e composição do núcleo familiar.
- O sistema deve permitir a consulta de programas sociais disponíveis por região (federal, estadual e municipal), exibindo critérios de elegibilidade e documentação necessária.
- O sistema deve permitir a criação de redes de apoio mútuo comunitárias, nas quais usuários podem publicar ofertas ou pedidos de doações, trocas de serviços e caronas solidárias.
- O sistema deve permitir o acompanhamento, pelo cidadão, do status de solicitações registradas junto a órgãos de assistência social (ex: CRAS, CadÚnico).
- O sistema deve permitir a visualização de indicadores públicos de execução orçamentária relacionados a políticas de combate à pobreza no município do usuário, em formato de painel simplificado.
- O sistema deve permitir que organizações da sociedade civil (ONGs e coletivos) publiquem editais de auxílio, oficinas de capacitação profissional e eventos comunitários.

## Cronograma de Execução

| Data | Atividade | Responsável |
|---|---|---|
| Semana 1 (01–07) | Levantamento de requisitos e definição do escopo funcional | Helen e Erica — Análise/PO |
| Semana 2 (08–14) | Modelagem do banco de dados (DER) e definição da arquitetura | Erica — Banco de Dados |
| Semana 3–4 (15–28) | Prototipação de telas (cadastro, consulta de programas sociais) | Helen — UX/Frontend |
| Semana 5–6 (29–12) | Desenvolvimento do back-end: cadastro de cidadãos e consulta de programas | Erica — Backend |
| Semana 7 (13–19) | Desenvolvimento do módulo de rede de apoio mútuo | Helen — Backend/Frontend |
| Semana 8 (20–26) | Testes internos, ajustes e escrita da documentação (README, /docs) | Erica — QA/Documentação |
| Semana 9 (27–03) | Estruturação final do GitHub e revisão geral para entrega | Helen e Erica — Geral |

> Datas simuladas para fins didáticos.

## Justificativa Técnica (resumo)

- **Linguagem/Framework:** Python + Django — ORM maduro e painel administrativo pronto para o cadastro de dados sensíveis (renda, composição familiar) e controle de permissões entre cidadãos e organizações.
- **Banco de Dados:** PostgreSQL — relações bem definidas entre cidadão, núcleo familiar, solicitações e redes de apoio; suporte a buscas geográficas (PostGIS) para consultas por região.
- **Padrão Arquitetural:** MVC em camadas, com API REST — permite reaproveitar o back-end em uma futura versão mobile e isola a manutenção de cada módulo.

*(Justificativa completa no PDF da 1ª Entrega, em `/docs`.)*

## Estrutura do repositório

```
/src        → código-fonte da aplicação (back-end Django e front-end)
/docs       → documentação complementar (diagramas, decisões de arquitetura, wireframes, PDF da entrega)
/database   → scripts de criação do banco (DER, migrations, seed de dados de teste)
```

---

## 2ª Entrega — Implementação

### Como avaliar (resumo rápido)

| | |
|---|---|
| **Usuário** | `admin` |
| **Senha** | `admin123` |
| **Endereço** | http://localhost:8000 (ou o link da porta 8000 no Codespaces) |

O usuário e os dados de demonstração (programas sociais, cidadãos, redes, organizações e indicadores) são criados automaticamente pelo comando `python manage.py popular_dados`, que o Docker já executa sozinho.

**Sem instalar nada (pelo navegador):** neste repositório, clique em **Code → Codespaces → Create codespace on main**. No terminal, rode `docker compose up --build`. Quando terminar, abra a porta **8000** na aba **Ports** (ícone de globo).

**Roteiro sugerido de teste:** Cidadãos (cadastrar, ver ficha, editar, excluir) → ficha do cidadão com a checagem de elegibilidade → Solicitações → Redes de apoio → Mural → Painel "Onde está o dinheiro".

Testes automáticos: `docker compose exec web python manage.py test core`

### Como executar

Há três formas. A primeira (Docker) funciona igual em Windows, Linux e macOS e já sobe o PostgreSQL junto. A segunda (Codespaces) roda direto no navegador, sem instalar nada.

#### Opção 1: Docker (recomendada)

Pré-requisito: [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e aberto.

```bash
docker compose up --build
```

Abra http://localhost:8000. Na primeira execução o sistema cria as tabelas, popula dados de demonstração e cria o usuário **admin / admin123**.

Para parar: `Ctrl+C`. Para apagar o banco e começar do zero: `docker compose down -v`.

#### Opção 2: pelo navegador, sem instalar nada (GitHub Codespaces)

Pré-requisito: estar logado em uma conta do GitHub. O Codespace é criado na conta de quem abre; quem testa não altera este repositório.

1. Nesta página do repositório, clique no botão verde **Code**, depois na aba **Codespaces** e em **Create codespace on main**. Vai abrir um editor (VS Code) no navegador.
2. No terminal, na parte de baixo da tela, rode:

   ```bash
   docker compose up --build
   ```

3. Espere aparecer `Starting development server at http://0.0.0.0:8000/`.
4. Abra a aba **Ports**, ao lado de **Terminal**, e clique no ícone de globo da porta **8000**. Use a porta 8000; a 5432 é o banco de dados e não abre no navegador.
5. Entre com **admin / admin123**.

Para rodar os testes, abra outro terminal (botão **+**) e rode `docker compose exec web python manage.py test core`.

#### Opção 3: instalação manual

Pré-requisitos: Python 3.12 ou mais recente e PostgreSQL 14 ou mais recente.

1. Crie o banco e o usuário no PostgreSQL (pelo `psql` ou pgAdmin):

   ```sql
   CREATE USER elos WITH PASSWORD 'elos123';
   CREATE DATABASE elospublicos OWNER elos;
   ```

2. Crie o ambiente virtual e instale as dependências:

   **Windows (PowerShell)**
   ```powershell
   cd src
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

   **Linux / macOS**
   ```bash
   cd src
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Crie as tabelas, os dados de exemplo e rode o servidor:

   ```bash
   python manage.py makemigrations core
   python manage.py migrate
   python manage.py popular_dados
   python manage.py runserver
   ```

Se o seu PostgreSQL usa outro usuário, senha ou porta, defina as variáveis `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` e `POSTGRES_PORT` antes de rodar (no PowerShell: `$env:POSTGRES_PASSWORD="minhasenha"`; no Linux/macOS: `export POSTGRES_PASSWORD=minhasenha`).

### Testes automatizados

```bash
cd src
python manage.py test core
```

Os testes cobrem o CRUD completo de cidadãos (telas e API), as classes abstratas, a herança, o polimorfismo, a composição do núcleo familiar e as regras de negócio.

### Rastreabilidade: requisito → implementação

| Requisito | Onde está no sistema | Classes / arquivos |
|---|---|---|
| 1. Cadastro de cidadãos com composição do núcleo familiar | `/cidadaos/` (CRUD completo) e `/cidadaos/<id>/familia/` | `Cidadao`, `NucleoFamiliar`, `MembroFamiliar` |
| 2. Consulta de programas por região, com critérios e documentos | `/programas/` (filtro por UF, município e esfera) e checagem de elegibilidade | `ProgramaSocial`, `RegraElegibilidade` e subclasses |
| 3. Redes de apoio mútuo (doações, trocas, caronas) | `/redes/` e publicação de ofertas e pedidos | `RedeApoio`, `PostagemApoio` |
| 4. Acompanhamento do status de solicitações (CRAS, CadÚnico) | `/solicitacoes/` e ficha do cidadão | `Solicitacao` |
| 5. Painel de execução orçamentária do município | `/painel/` | `IndicadorOrcamentario` |
| 6. Organizações publicam editais, oficinas e eventos | `/organizacoes/` e `/mural/` | `Organizacao`, `PublicacaoOrganizacao` |

### Pilares de POO

| Pilar | Onde |
|---|---|
| Classe abstrata | `Usuario` e `Publicacao` (`core/models.py`) e `RegraElegibilidade` (`core/dominio/elegibilidade.py`), com `ABCMeta` e `@abstractmethod` |
| Herança | `Cidadao`/`Organizacao` herdam de `Usuario`; `PostagemApoio`/`PublicacaoOrganizacao` herdam de `Publicacao`; regras de elegibilidade herdam de `RegraElegibilidade` |
| Polimorfismo | Métodos sobrescritos marcados com `@override` (o equivalente Python do `@Override` do Java, `typing.override`, Python 3.12+) |
| Composição 1:N | `NucleoFamiliar` ◆ `MembroFamiliar` |

Convenções de código: classes em PascalCase, métodos e variáveis em camelCase, e campos persistidos em snake_case, porque viram colunas no banco (`database/schema.sql`). O código é tipado com *type hints*.

Diagramas: [`docs/diagrama_classes.md`](docs/diagrama_classes.md) e [`docs/der.md`](docs/der.md).

### Banco de dados

- Conexão ativa com PostgreSQL configurada em `src/elospublicos/settings.py`.
- Script de criação das tabelas: [`database/schema.sql`](database/schema.sql), compatível com as classes em `src/core/models.py`.
- Dados de demonstração: `python manage.py popular_dados`.

### API REST

Disponível em `/api/` (navegável no navegador após login). Cada recurso aceita GET, POST, PUT, PATCH e DELETE:

`/api/cidadaos/`, `/api/organizacoes/`, `/api/programas/`, `/api/solicitacoes/`, `/api/redes/`, `/api/postagens/`, `/api/publicacoes/`, `/api/indicadores/`

### Telas públicas e restritas

Programas sociais, mural e painel de indicadores são públicos. Cadastros, solicitações e redes de apoio exigem login, porque envolvem dados pessoais (LGPD). O CPF aparece sempre mascarado nas telas.
