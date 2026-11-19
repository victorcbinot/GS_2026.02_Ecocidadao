# EcoCidadão

Assistente municipal inteligente para orientar cidadãos sobre descarte correto
de resíduos, materiais aceitos e proibidos e utilização de Ecopontos.

> **Aviso:** EcoCidade é um município fictício. Todos os documentos, endereços,
> horários, limites e comunicados são simulados e não representam dados reais
> de nenhum município.

## Status atual

- Pipeline RAG, agente com ferramentas, guardrails e interface Gradio
  implementados.
- **154 testes automatizados passando**.
- Avaliação RAGAS real registrada em `avaliacao_ragas.json`.
- Comparação de chunking medida em
  `data/experiments/chunking_comparison.json`.
- A configuração local usa `qwen2.5:7b` para o agente e para o juiz RAGAS, com
  embeddings locais.
- A conta da Ollama Cloud continua retornando **HTTP 402** por falta de
  créditos. O alvo `gpt-oss:20b` permanece documentado como alternativa, mas a
  execução reproduzível e as evidências usam o modelo local. Isso está
  identificado em `evidencias/` e `Chat_Log.txt`; nenhum resultado foi
  inventado.
- Os oito ground truths continuam marcados como `pendente_validacao_humana`.
- Nomes, RMs e turma dos três integrantes preenchidos; certificação e vídeo
  continuam pendentes.

## Integrantes

- Felipe de Oliveira Doern — RM 568798
- Miguel Marcelo Alves Ramos de Oliveira — RM 569467
- Victor Correia Binot — RM 571499

Turma: 1CCPI — FIAP.

## Objetivo

O EcoCidadão orienta a população de EcoCidade sobre:

- materiais aceitos, proibidos e locais de entrega;
- horários, interdições e mudanças temporais dos Ecopontos;
- evidências documentais com fontes citadas;
- recusa segura de perguntas fora do escopo ou sem contexto;
- demonstração acadêmica de um pipeline completo de RAG com ferramentas,
  guardrails, avaliação e interface local.

## Problema

As informações estão distribuídas em três documentos com datas e finalidades
diferentes. A lista de Ecopontos, o regulamento de descarte e o comunicado de
interdição do Parque das Acácias não podem ser tratados como se valessem ao
mesmo tempo. O sistema precisa identificar a data de referência, priorizar o
comunicado mais recente e não aplicar uma regra antes da sua vigência.

## Arquitetura

```text
Pergunta do cidadão
  -> guardrails de entrada
  -> agente com tool calling
       -> consultar_base_documental -> RAG -> ChromaDB + embeddings locais
       -> consultar_ecopontos      -> data/ecopontos.json
       -> calcular                 -> calculadora segura com AST
       -> data_atual               -> data de referência
  -> guardrails de saída
  -> resposta + fontes + status de segurança
  -> interface Gradio ou CLI
```

A base documental é carregada de `base_documental/`, validada e dividida em
chunks por duas estratégias. Os chunks são indexados em coleções independentes
do ChromaDB com embeddings locais. O serviço RAG recupera os trechos mais
relevantes, monta um contexto delimitado e cita as fontes. O agente decide
quando usar cada ferramenta e o limite de seis chamadas evita ciclos
improdutivos.

## Modelos e separação de papéis

| Papel | Configuração atual | Execução |
|---|---|---|
| Agente principal | `qwen2.5:7b` | Ollama local (`http://127.0.0.1:11434`) |
| Juiz RAGAS | `qwen2.5:7b` | Ollama local (`http://127.0.0.1:11434`) |
| Embeddings | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Local, CPU |
| ChromaDB | `1.5.9` | Local |

O agente e o juiz têm variáveis independentes (`OLLAMA_*` e `RAGAS_JUDGE_*`).
O juiz local não exige chave. A chave do agente, quando usada no modo Cloud, é
lida como `SecretStr` e não é exibida em logs nem na interface. `LLM_NUM_GPU`
limita as camadas enviadas à GPU; em máquinas com falha de CUDA, `28` funciona
como contingência e `0` força CPU.

> A execução RAGAS preservada em `avaliacao_ragas.json` usou o
> `qwen2.5:7b` local como **gerador das respostas e como juiz**, porque a
> Ollama Cloud estava sem créditos. O JSON registra essa configuração. A
> configuração-alvo com GPT-OSS 20B gerando respostas não pôde ser executada.

## Estrutura do projeto

```text
GS_2026.02_Ecocidadao/
├── base_documental/          # três documentos da base
├── avaliacao_ragas.json      # resultado RAGAS real preservado
├── certificacao.txt          # nomes/RMs/turma preenchidos; certificação pendente
├── Chat_Log.txt              # interações reais de validação local
├── demo_video_url.txt        # URL do vídeo pendente
├── app.py                      # ponto de entrada da interface
├── requirements.txt            # dependências com versões fixadas
├── .env.example                # modelo de variáveis de ambiente
├── evidencias/                 # capturas e logs reais
├── docs/
│   ├── AVALIACAO_RAGAS.md
│   ├── COMPARACAO_CHUNKING.md
│   ├── CONCLUSAO.md
│   └── REVISAO_GROUND_TRUTHS.md
├── src/ecocidadao/
│   ├── config.py
│   ├── ingestion/
│   ├── rag/
│   ├── agent/
│   ├── guardrails/
│   ├── evaluation/
│   └── ui/
├── scripts/
├── tests/
└── data/
    ├── ecopontos.json
    ├── chunks/                 # gerado e ignorado pelo Git
    ├── chroma/                 # gerado e ignorado pelo Git
    └── experiments/
```

## Pré-requisitos

- Windows com PowerShell.
- Python 3.14.3 no ambiente validado; o código mantém compatibilidade
  pretendida com Python 3.12+.
- Ollama local com `qwen2.5:7b` para o agente e para o juiz RAGAS.
- Opcional: chave e créditos da Ollama Cloud para o agente `gpt-oss:20b`.

## Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Preencha o `.env` conforme o modo de execução. O `.env` é ignorado pelo Git.

## Configuração

### Modo local (sem custo de API)

```dotenv
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_API_KEY=
LLM_TIMEOUT_S=180
LLM_NUM_GPU=28

RAGAS_JUDGE_BASE_URL=http://127.0.0.1:11434
RAGAS_JUDGE_MODEL=qwen2.5:7b
RAGAS_JUDGE_API_KEY=
RAGAS_JUDGE_TIMEOUT_S=600
```

### Agente na Ollama Cloud

```dotenv
OLLAMA_BASE_URL=https://ollama.com
OLLAMA_MODEL=gpt-oss:20b
OLLAMA_API_KEY=sua_chave_real
```

O juiz pode continuar local:

```dotenv
RAGAS_JUDGE_BASE_URL=http://127.0.0.1:11434
RAGAS_JUDGE_MODEL=qwen2.5:7b
```

Sem créditos, a chamada ao agente retorna HTTP 402 e a interface mostra uma
mensagem controlada. Não há compra automática de créditos.

## Execução

### 1. Gerar chunks

```powershell
python scripts/ingest.py
```

Saídas em `data/chunks/`:

- `chunks_fixo.jsonl` — 800 caracteres, 150 de sobreposição;
- `chunks_markdown.jsonl` — cabeçalhos Markdown, 800 caracteres, 100 de
  sobreposição;
- `summary.json`.

### 2. Indexar no ChromaDB

```powershell
python scripts/index_chroma.py --recreate
```

Coleções: `ecocidadao_fixo` e `ecocidadao_markdown`.

### 3. Consultar o RAG

```powershell
python scripts/ask_rag.py "Onde devo descartar medicamentos vencidos?" --collection ecocidadao_markdown --as-of 2026-06-10
```

### 4. Consultar o agente

```powershell
python scripts/ask_agent.py "Em 20/04/2026, o Parque das Acácias aceita pilhas? Para onde levar?" --as-of 2026-04-20
```

O agente limita a execução a no máximo **6 chamadas de ferramentas** por
pergunta e detecta chamadas repetidas.

### 5. Abrir a interface

```powershell
python app.py
```

A interface abre em `http://127.0.0.1:7860` por padrão.

### 6. Rodar os testes

```powershell
python -m unittest discover -s tests -v
python -m compileall src scripts tests app.py
python -m pip check
```

## Ingestão e chunking

A ingestão valida front matter YAML, metadados obrigatórios, data ISO e tamanho
mínimo de 100 palavras. Cada chunk tem ID determinístico no formato
`{doc_id}::{estrategia}::{indice}`. A estratégia Markdown preserva
`section_h1`, `section_h2`, `section_h3`, `section_path` e `section_level`.

### Comparação medida

Execução real: `python scripts/compare_chunking.py`.

| Estratégia | Chunks | Média de caracteres | Hit@3 | Hit@5 | MRR | Precision documental | Recall documental |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fixo | 17 | 607,00 | 1,0000 | 1,0000 | 1,0000 | 0,7250 | 1,0000 |
| Markdown | 22 | 453,77 | 1,0000 | 1,0000 | 1,0000 | 0,8000 | 0,8750 |

**Decisão recomendada: Markdown.** Empata em Hit@3, Hit@5 e MRR, tem precisão
documental maior, chunks menores e preserva a hierarquia de seções. A ressalva
é o recall documental menor em duas armadilhas de pilhas; perguntas temporais
usam janela ampliada (`TEMPORAL_TOP_K=10`) para mitigar. O JSON mantém
`winner=null` porque não houve RAGAS por estratégia, mas registra
`recommended_strategy=markdown`; a recomendação é uma decisão de engenharia
baseada nos dados de retrieval. Detalhes em `docs/COMPARACAO_CHUNKING.md`.

## Avaliação RAGAS

O dataset em `src/ecocidadao/evaluation/dataset.json` tem exatamente oito
perguntas: quatro simples e quatro de armadilha. A revisão técnica está em
`docs/REVISAO_GROUND_TRUTHS.md`; todos os ground truths continuam
`pendente_validacao_humana`.

Resultados reais preservados em `avaliacao_ragas.json`:

| Métrica | Resultado |
|---|---:|
| Faithfulness | 0,570833 |
| Answer relevancy | 0,180817 |
| Context precision | 0,520833 |
| Context recall | 0,937500 |

Leitura resumida:

- a recuperação cobre bem os documentos na maioria das perguntas;
- a precisão do contexto é mediana, com chunks irrelevantes no topo;
- as respostas são prolixas e pouco aderentes, derrubando
  `answer_relevancy`;
- duas perguntas de armadilha ficaram sem contexto exposto e receberam
  `context_recall=1,0`, um resultado anômalo que não deve ser lido como
  cobertura real;
- o `qwen2.5:7b` local foi gerador e juiz nessa execução; a configuração-alvo
  separa GPT-OSS 20B (gerador) e Qwen 2.5 7B (juiz).

Explicação completa, tabela por pergunta e melhorias propostas:
`docs/AVALIACAO_RAGAS.md`.

Para executar novamente quando houver créditos:

```powershell
python scripts/evaluate_ragas.py
```

A saída padrão agora é `avaliacao_ragas.json`.

## Guardrails

O `GuardrailEngine` é aplicado antes e depois da chamada ao modelo:

- **Escopo:** recusa perguntas fora de descarte, reciclagem, sustentabilidade
  municipal e Ecopontos sem chamar o LLM.
- **Prompt injection:** bloqueia comandos para ignorar instruções, mudar papel
  ou revelar o prompt; instruções encontradas nos documentos são removidas.
- **LGPD:** recusa dados pessoais de terceiros e redige CPF, telefone, e-mail e
  padrões sensíveis na pergunta, no contexto e na resposta.
- **Contexto insuficiente:** resposta determinística, sem LLM, com orientação
  ao cidadão.
- **Validação de saída:** remove citações inexistentes, bloqueia resposta
  factual sem citação válida, saída fora de escopo e tentativa de revelar
  instruções; aplica fallback seguro.
- **Rastreabilidade:** `RagResponse` expõe `guardrail_events` e
  `blocked_by_guardrail`.

## Ferramentas e agente

- `consultar_base_documental`: RAG com citações `[F1]`, `[F2]` etc.
- `consultar_ecopontos`: endereço, horário, materiais e situação do Ecoponto.
- `calcular`: calculadora segura com AST, sem `eval()`.
- `data_atual`: data ISO de referência.

O agente combina ferramentas, trata erros controlados, preserva citações e
limita a **6 chamadas** por pergunta. A suíte cobre limite, repetição, erros e
combinação de ferramentas.

## Contradição temporal e detalhe escondido

- `lista_ecopontos.md` (01/02/2026) informa que o Parque das Acácias aceita
  pilhas e baterias.
- `comunicado_interdicao.md` (10/03/2026) interdita o Parque de 15/03/2026 a
  31/05/2026, inclusive.
- A partir de 01/06/2026, o Parque reabre com horário reduzido e deixa de
  aceitar pilhas e baterias; elas passam a ser exclusivas do Ecoponto
  Industrial.
- Medicamentos vencidos não são aceitos em Ecopontos; o destino é a Farmácia
  Municipal EcoSaúde, Rua das Palmeiras, 77, Centro, segunda a sexta,
  08:00–17:00.

## Evidências

A pasta `evidencias/` contém registros reais:

- `04b_interface_gradio_consulta.png` — agente usando `consultar_ecopontos`.
- `04c_interface_gradio_rag_fontes.png` — consulta RAG com fontes e citação.
- `04d_interface_gradio_guardrail.png` — recusa de escopo pelo guardrail.
- `01_rag_consulta.txt`, `02_agente_ferramentas.txt`,
  `02b_agente_ferramentas_combinadas.txt`,
  `03_guardrail_escopo.txt`, `03b_guardrail_injection.txt`,
  `03c_guardrail_lgpd.txt` e `06_comparacao_chunking.txt` — logs reais.
- `05_testes.txt` — saída da suíte completa (154 testes).
- `07_configuracao_modelos.txt` — separação dos modelos, embeddings locais e
  limite de 6 ferramentas.

As capturas de interface foram feitas com o modelo local `qwen2.5:7b` porque
a Ollama Cloud retornou HTTP 402. Não há prints fictícios. Detalhes e comandos
em `evidencias/00_LEIA-ME.md`.

## Custo estimado por pergunta

| Modo | Custo direto de API | Observação |
|---|---:|---|
| Tudo local (agente, juiz e embeddings) | R$ 0,00 | Sem chamadas de nuvem. |
| Agente Cloud + juiz/embeddings locais | Não medido | A conta retornou HTTP 402; nenhum crédito foi consumido. |
| Agente Cloud com créditos | Depende da tarifa vigente | Estimar com `(tokens de entrada + saída) × tarifa`; o projeto não coleta tokens. |

Não foi inventado valor de tarifa. O custo local é zero em termos de API; custo
de energia e hardware não foi medido.

## Limitações

- Base acadêmica fictícia, com apenas três documentos.
- Ollama Cloud sem créditos; agente `gpt-oss:20b` não responde no momento.
- RAGAS executado com `qwen2.5:7b` como gerador e juiz, não com GPT-OSS 20B.
- `answer_relevancy` baixa e respostas prolixas.
- Duas armadilhas ficaram sem contexto exposto na execução RAGAS.
- Ground truths pendentes de validação humana.
- Guardrails heurísticos não substituem revisão humana.
- Evidências de interface usam contingência local, não o agente Cloud.
- Certificação e vídeo pendentes.

## Entregáveis

- `avaliacao_ragas.json` — resultado real preservado.
- `certificacao.txt` — nomes, RMs e turma (1CCPI) preenchidos; certificação e
  vídeo pendentes.
- `Chat_Log.txt` — interações reais de validação local.
- `demo_video_url.txt` — URL pendente, sem valor fictício.
- `docs/AVALIACAO_RAGAS.md` — análise das métricas.
- `docs/COMPARACAO_CHUNKING.md` — comparação e decisão.
- `docs/CONCLUSAO.md` — conclusão curta com números reais.
- `docs/REVISAO_GROUND_TRUTHS.md` — revisão das oito respostas.
- `evidencias/` — capturas e logs reais.

## Justificativa para a ausência do notebook

O professor autorizou a execução local e a retirada do `.ipynb`, desde que o
motivo fosse documentado. Todo o projeto está em módulos `.py`; não há Jupyter,
Google Colab ou dependências de notebook.

Registro: print da autorização do Professor no Teams em
`evidencias/autorizacao_notebook_teams.png`.

## Próximas etapas

1. Adicionar créditos à Ollama Cloud e validar o agente `gpt-oss:20b`.
2. Reexecutar o RAGAS separando GPT-OSS 20B (gerador) e Qwen 2.5 7B (juiz).
3. Corrigir a montagem de contextos do RAGAS para não depender apenas das
   fontes citadas.
4. Validar os oito ground truths com uma pessoa.
5. Reduzir respostas prolixas e melhorar `answer_relevancy`.
6. Gravar o vídeo, preencher o link em `demo_video_url.txt` e finalizar a
   certificação.
