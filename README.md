# EcoCidadão

Assistente municipal inteligente para orientar cidadãos sobre descarte
correto de resíduos, materiais aceitos e proibidos e utilização de
Ecopontos.

> **Aviso:** EcoCidade é um município fictício. Todos os documentos,
> endereços, horários, limites e comunicados do projeto são simulados e
> não representam dados reais de nenhum município.

## Objetivo

O EcoCidadão é um assistente conversacional para orientar a população de
EcoCidade sobre o descarte correto de resíduos. O projeto busca:

- responder perguntas sobre materiais aceitos, proibidos e locais de
  entrega;
- consultar os Ecopontos e considerar horários, interdições e mudanças
  temporais;
- usar evidências documentais e apresentar as fontes consultadas;
- recusar perguntas fora do escopo e não inventar informações quando a base
  não sustenta uma resposta;
- demonstrar, de forma acadêmica, um pipeline completo de RAG com
  ferramentas, guardrails, avaliação e interface local.

## Problema

As informações de descarte de EcoCidade estão distribuídas em documentos
com datas e finalidades diferentes. Em especial, a lista de Ecopontos, o
regulamento de descarte e o comunicado de interdição do Parque das Acácias
não podem ser tratados como se valessem ao mesmo tempo. O sistema precisa
identificar a data de referência da pergunta, priorizar o comunicado mais
recente e não aplicar uma regra antes da sua vigência.

Além disso, o cidadão pode fazer perguntas incompletas, usar termos
informais, combinar consultas documentais com cálculos ou tentar induzir o
modelo a ignorar as instruções. O projeto trata esses casos com ferramentas,
guardrails, citações e respostas seguras.

## Solução e arquitetura

O fluxo principal é:

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

A base documental é carregada de `2_base_documental/`, validada e dividida
em chunks por duas estratégias. Os chunks são indexados em coleções
independentes do ChromaDB com embeddings gerados localmente. O serviço RAG
recupera os trechos mais relevantes, monta um contexto delimitado e cita as
fontes. O agente decide quando usar cada ferramenta e o limite de seis
chamadas evita ciclos improdutivos. A interface Gradio mantém o histórico
da sessão e exibe as fontes de cada resposta.

## Contexto acadêmico

- Global Solution 2026.2 — FIAP.
- Frente B — Descarte e sustentabilidade.
- Desenvolvimento em trio.
- Execução local no Windows, com PyCharm e terminal.
- Projeto implementado apenas em módulos `.py`.

## Integrantes

- [preencher nome 1]
- [preencher nome 2]
- [preencher nome 3]

## Status atual

**Etapas 1 a 7 implementadas e 151 testes automatizados passando. A
avaliação RAGAS real está pendente porque o Ollama Cloud continua retornando
HTTP 402 por falta de créditos. A entrega final ainda depende do preenchimento
dos dados humanos e da geração do vídeo.**

- Etapa 1: estrutura de pastas, configuração central, dependências,
  ponto de entrada e documentação.
- Etapa 2: três documentos autorais da base, carga com validação de
  metadados, duas estratégias de chunking e indexação local no ChromaDB
  com testes automatizados.
- Etapa 3: serviço RAG com LCEL, recuperação por similaridade, citações,
  recusa sem evidência e tratamento de temporalidade.
- Etapa 4: guardrails de escopo, prompt injection, LGPD, contexto
  insuficiente e validação de saída, integrados ao serviço RAG.
- Etapa 5: ferramentas de consulta documental, Ecopontos, calculadora e
  data atual; agente com tool calling, limite de chamadas e tratamento de
  erros.
- Etapa 6: interface Gradio com histórico por sessão, fontes por resposta,
  status de guardrails e mensagens amigáveis para falhas de conexão e do
  banco vetorial.
- Etapa 7: dataset de avaliação com oito perguntas, runner RAGAS, resultado
  pendente documentado e comparação medida de chunking por retrieval.

A validação com o Ollama Cloud está bloqueada temporariamente por falta
de créditos na conta (HTTP 402). O serviço, o agente, a interface e os
testes com LLM simulado estão funcionando. A avaliação RAGAS real vai gerar
respostas e métricas quando houver créditos; nenhum valor foi inventado.

## Tecnologias utilizadas

- Python 3.14.3 no ambiente validado, com compatibilidade pretendida para
  Python 3.12 ou superior.
- LangChain Core, LangChain Text Splitters e LangChain Ollama; LCEL para a
  composição do pipeline.
- `ChatOllama` com Ollama Cloud.
- Embeddings locais com `sentence-transformers` e o modelo
  `paraphrase-multilingual-MiniLM-L12-v2`.
- ChromaDB com persistência local e duas coleções independentes.
- Gradio 6.32 para a interface local; o código mantém compatibilidade
  com a API de mensagens do Gradio 5.
- RAGAS 0.4.4, `datasets` e `pandas` para a avaliação.
- pydantic-settings com python-dotenv para configuração e `.env`.
- PyYAML para leitura do front matter dos documentos.
- `unittest` para os 151 testes automatizados.

## Estrutura do projeto

```text
GS_2026.02_Ecocidadao/
├── 2_base_documental/          # documentos da base de conhecimento
├── avaliacao_ragas.json        # avaliação real ou pendência documentada
├── README.md                   # este arquivo
├── certificacao.txt            # pendente de definição
├── Chat_log.txt                # pendente de definição
├── demo_video_url.txt          # pendente de gravação
├── app.py                      # ponto de entrada da aplicação
├── requirements.txt            # dependências do projeto
├── .env.example                # modelo de variáveis de ambiente
├── .gitignore
├── src/ecocidadao/
│   ├── config.py               # configurações centralizadas
│   ├── ingestion/              # carga e chunking dos documentos
│   ├── rag/                    # recuperação e pipeline LCEL
│   ├── agent/                  # agente e ferramentas
│   ├── guardrails/             # validações de segurança
│   ├── evaluation/             # avaliação RAGAS
│   └── ui/                     # interface Gradio
├── scripts/                    # comandos de ingestão e avaliação
├── tests/                      # testes automatizados
├── data/
│   ├── ecopontos.json          # dados estruturados dos Ecopontos
│   ├── chunks/                 # chunks gerados (ignorados pelo Git)
│   ├── chroma/                 # índice gerado localmente
│   └── experiments/            # resultados da comparação de chunking
└── docs/                       # notas internas opcionais
```

## Pré-requisitos

- Windows.
- PyCharm.
- Python 3.12 (recomendado) ou superior.
- Acesso ao Ollama Cloud, uma chave de API e créditos disponíveis.

**Atenção:** o ambiente local atual utiliza Python 3.14.3. As dependências
de embeddings e banco vetorial (`sentence-transformers`, `torch` e
`chromadb`) foram instaladas e validadas nesse ambiente, mas o
`requirements.txt` mantém compatibilidade com Python 3.12. A interface
`gradio` 6.32, o `ragas` 0.4.4 e o `datasets` 5.2.0 também foram
instalados e validados. O `scikit-network`, dependência opcional usada
apenas na geração de testset do RAGAS, não tem wheel recente para Python
3.14; por isso o `requirements.txt` fixa a versão pura 0.12.1 nesse
interpretador. As métricas usadas nesta avaliação não dependem dessa
biblioteca. Caso alguma dependência não ofereça suporte, recomenda-se
criar o ambiente virtual com Python 3.11 ou 3.12. Nenhuma configuração
global do computador deve ser alterada.

## Instalação

No terminal do PyCharm, na raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Crie o arquivo de variáveis de ambiente:

```powershell
Copy-Item .env.example .env
```

Depois preencha `OLLAMA_API_KEY` e `OLLAMA_MODEL` no `.env`. O arquivo
`.env` não deve ser versionado.

O `requirements.txt` utiliza faixas de versão compatíveis com Python
3.12. O ambiente local validado usa Python 3.14.3 com as dependências
instaladas em `.venv/`; o marcador de ambiente seleciona a versão de
`scikit-network` adequada a cada interpretador.

## Configuração do Ollama Cloud

Depois de criar o `.env`, preencha:

```dotenv
OLLAMA_API_KEY=sua_chave
OLLAMA_BASE_URL=https://ollama.com
OLLAMA_MODEL=modelo_disponivel_na_sua_conta
```

A chave é lida por `pydantic-settings` como `SecretStr`, não é exibida nos
logs nem na interface e não deve ser versionada. O modelo precisa oferecer
suporte a tool calling para o agente funcionar com todas as ferramentas.
Sem chave, o CLI e a interface retornam uma mensagem de configuração; com a
conta sem créditos, a chamada real retorna HTTP 402 e o projeto registra a
pendência em vez de inventar respostas ou métricas.

## Execução

Com o ambiente virtual ativado e a base vetorial já ingerida, inicie a
interface:

```powershell
python app.py
```

O Gradio abre a interface em `http://127.0.0.1:7860` por padrão. O endereço
e a porta podem ser alterados por `GRADIO_SERVER_NAME` e
`GRADIO_SERVER_PORT`. A interface permite digitar perguntas, manter o
histórico da sessão, limpar a conversa e consultar as fontes documentais de
cada resposta.

Se a conta do Ollama Cloud estiver sem créditos ou o banco vetorial não
estiver disponível, a interface mostra uma mensagem explicativa em vez de
expor detalhes internos. Os logs e a interface não exibem chaves, tokens
ou outros dados sensíveis.

## Ingestão e chunking

Os documentos de `2_base_documental/` são carregados com validação de
front matter YAML, metadados obrigatórios, data ISO e tamanho mínimo de
100 palavras. Em seguida, o script gera os chunks nas duas estratégias:

```powershell
python scripts/ingest.py
```

Saídas em `data/chunks/` (ignoradas pelo Git):

- `chunks_fixo.jsonl`: estratégia A, divisão fixa com 800 caracteres e
  150 de sobreposição.
- `chunks_markdown.jsonl`: estratégia B, divisão por cabeçalhos Markdown,
  com divisão recursiva de 800 caracteres e 100 de sobreposição quando
  necessário.
- `summary.json`: contagem e estatísticas de tamanho por documento e
  estratégia.

Cada chunk possui ID determinístico no formato
`{doc_id}::{estrategia}::{indice}`, metadados do documento e, na
estratégia Markdown, a hierarquia de seções (`section_h1`, `section_h2`,
`section_h3`, `section_path` e `section_level`).

Testes automatizados:

```powershell
python -m unittest discover -s tests -v
```

## Indexação no ChromaDB

Os embeddings são gerados localmente com o modelo multilíngue
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, sem enviar
os documentos para serviços externos. O modelo é baixado no primeiro uso
para `.cache/huggingface/`, pasta ignorada pelo Git. O cliente ChromaDB é
inicializado com telemetria anônima desativada.

```powershell
python scripts/index_chroma.py --recreate
```

O comando cria ou atualiza duas coleções independentes em `data/chroma/`
(pasta ignorada pelo Git):

- `ecocidadao_fixo`: chunks da estratégia de divisão fixa.
- `ecocidadao_markdown`: chunks da estratégia por cabeçalhos Markdown.

Cada coleção preserva os IDs determinísticos dos chunks, o texto e os
metadados originais. Os metadados completos são serializados em JSON
para manter listas e valores nulos que o ChromaDB não aceita diretamente.
Execuções repetidas usam `upsert` e removem chunks obsoletos, evitando
duplicação. Para indexar apenas uma estratégia, use
`--strategy fixo` ou `--strategy markdown`.

O módulo `src/ecocidadao/rag/vector_store.py` expõe funções para criar ou
atualizar índices, carregar uma coleção existente e consultar por
similaridade, retornando texto, metadados, distância e similaridade.

Validação local: `chromadb` 1.5.9, `sentence-transformers` 5.7.0 e
`torch` 2.15.0. As faixas do `requirements.txt` mantêm suporte a Python
3.12.

## Serviço RAG

O serviço em `src/ecocidadao/rag/service.py` recupera trechos da coleção
escolhida, monta um contexto com metadados e citações `[F1]`, `[F2]` etc.
e envia a pergunta ao modelo configurado no Ollama Cloud. A resposta
inclui as fontes efetivamente citadas e o contexto utilizado.

```powershell
python scripts/ask_rag.py "Onde devo descartar medicamentos vencidos?" --collection ecocidadao_markdown --as-of 2026-06-10
```

Parâmetros disponíveis:

- `--collection`: `ecocidadao_fixo` ou `ecocidadao_markdown` (padrão do
  `.env`).
- `--top-k`: quantidade de trechos recuperados.
- `--as-of`: data de referência no formato `AAAA-MM-DD`.

Comportamento implementado:

- citações documentais com título, data de publicação, seção e arquivo;
- distinção entre informação documental, inferência e ausência de
  evidência no prompt;
- recusa determinística, sem chamar o LLM, quando nenhum trecho supera o
  limiar de relevância;
- regras temporais explícitas para não misturar documentos antigos e
  novos, não aplicar mudanças antes da vigência e não usar documento
  publicado depois da data da pergunta como regra vigente;
- ampliação automática da janela de recuperação para perguntas temporais
  (`TEMPORAL_TOP_K = 10`), garantindo que regras históricas e novas
  apareçam juntas no contexto;
- encapsulamento de falhas do modelo em `RagServiceError`, com mensagem
  clara no CLI.

A recente consulta real retornou HTTP 402 do Ollama Cloud por falta de
créditos. O tratamento do erro já está implementado; a resposta real do
modelo permanece pendente de validação.

## Guardrails

O `GuardrailEngine` em `src/ecocidadao/guardrails/engine.py` é aplicado
dentro de `RagService.ask`, antes e depois da chamada ao modelo:

1. validação da pergunta;
2. recuperação dos trechos;
3. sanitização do contexto documental;
4. chamada ao LLM;
5. validação da resposta e fallback seguro.

Comportamentos implementados:

- **Escopo:** perguntas claramente fora de descarte, reciclagem,
  sustentabilidade municipal e Ecopontos são recusadas sem chamar o LLM.
  A classificação usa pontuação ponderada e âncoras de domínio, evitando
  bloqueio simplista por palavra isolada. Perguntas legítimas que apenas
  mencionam regras continuam permitidas.
- **Prompt injection:** comandos para ignorar instruções, mudar o papel
  do assistente, revelar o prompt ou fabricar evidências são bloqueados
  na entrada. Instruções encontradas nos documentos são removidas antes
  de compor o prompt, com o marcador
  `[conteúdo instrucional não confiável removido por segurança]`.
- **Contexto não confiável:** o prompt delimita os trechos entre
  `<contexto_documental_nao_confiavel>` e
  `</contexto_documental_nao_confiavel>` e orienta o modelo a não
  obedecer comandos presentes neles.
- **LGPD:** pedidos de dados pessoais de terceiros são recusados. CPF,
  telefone, e-mail e padrões sensíveis são redigidos na pergunta, no
  contexto e na resposta. Contatos institucionais, como o telefone da
  Secretaria de Meio Ambiente, continuam permitidos.
- **Contexto insuficiente:** quando não há trecho acima do limiar, o
  serviço responde de forma determinística, sem chamar o LLM, e orienta
  o cidadão a procurar a Secretaria Municipal de Meio Ambiente ou o
  Ecoponto mais próximo.
- **Validação de saída:** citações inexistentes são removidas, respostas
  factuais sem citação válida não são apresentadas como fato, saídas fora
  de escopo ou com tentativa de revelar instruções são bloqueadas e dados
  pessoais são redigidos. Em qualquer falha, aplica-se uma resposta
  segura padronizada.
- **Rastreabilidade:** `RagResponse` expõe `guardrail_events` e
  `blocked_by_guardrail` para auditoria e testes.

Os guardrails são heurísticos e complementam, mas não substituem, a
validação humana e a resposta real do modelo. A suíte completa está em
**151 testes automatizados**:

```powershell
python -m unittest discover -s tests -v
```

## Ferramentas e agente

O agente em `src/ecocidadao/agent/agent.py` usa `ChatOllama` com suporte
a tool calling e um loop próprio de execução, o que permite controlar o
limite e os ciclos com precisão.

Ferramentas disponíveis:

- `consultar_base_documental`: consulta o `RagService` e retorna resposta,
  contexto e fontes com citações `[F1]`, `[F2]` etc. Os guardrails do RAG
  são aplicados antes de o resultado chegar ao agente.
- `consultar_ecopontos`: lê `data/ecopontos.json` e consulta endereço,
  horário, materiais aceitos e situação de funcionamento. Considera a
  interdição do Parque das Acácias entre 15/03/2026 e 31/05/2026 e as
  mudanças permanentes a partir de 01/06/2026, incluindo o novo horário e
  a retirada de pilhas e baterias.
- `calcular`: calculadora baseada em AST, sem `eval()` nem execução
  arbitrária. Aceita operadores e funções seguras, valida limites e
  identifica o resultado como estimativa calculada, não como dado
  oficial.
- `data_atual`: retorna a data atual em ISO para interpretar vigências e
  reaberturas.

Comportamentos do agente:

- decide quando chamar cada ferramenta e pode combiná-las;
- limita a execução a no máximo **6 chamadas de ferramentas** por
  pergunta;
- detecta chamadas repetidas pela assinatura da ferramenta e dos
  argumentos, interrompendo ciclos desnecessários;
- converte falhas de ferramentas em mensagens controladas e continua o
  fluxo quando possível;
- informa limitação quando o modelo, a ferramenta ou o contexto não
  permitem responder com segurança;
- aplica guardrails na entrada e na saída e preserva as citações
  documentais, acrescentando as fontes consultadas quando necessário;
- diferencia resposta documental, dado estruturado dos Ecopontos e
  resultado calculado.

Exemplo de uso:

```powershell
python scripts/ask_agent.py "O Parque das Acácias aceita pilhas em 10/06/2026? Se eu levar 3 caixas de 5 kg, quanto é o total?" --as-of 2026-06-10
```

A validação real do agente com o Ollama Cloud continua bloqueada pelo
HTTP 402. Os testes usam LLM simulado e cobrem as ferramentas, o limite
de chamadas, a repetição e os erros controlados.

## Interface Gradio

A interface fica em `src/ecocidadao/ui/` e é iniciada por `app.py`. Ela não
reimplementa a lógica de negócio: usa `ChatSession` para manter o histórico
e `EcoCidadaoAgent` para guardrails, ferramentas e respostas.

- **Histórico:** o `Chatbot` e o estado da sessão preservam as interações
  durante o uso. O agente recebe até quatro turnos anteriores como contexto
  delimitado e explicitamente marcados como não instruções.
- **Proteção do histórico:** turnos anteriores bloqueados por guardrails ou
  com prompt injection detectado são omitidos do contexto. A pergunta atual
  continua passando pelo `GuardrailEngine` antes de qualquer chamada ao
  modelo.
- **Fontes por resposta:** as fontes documentais aparecem na própria
  mensagem do assistente e em um painel lateral com documento, data, seção
  e arquivo. Ferramentas usadas são listadas sem expor argumentos ou
  resultados internos.
- **Status visual:** respostas concluídas, recusas de guardrail, contexto
  insuficiente, limite de ferramentas, repetição e falhas de conexão têm
  títulos e avisos distintos.
- **Falhas compreensíveis:** erros do Ollama Cloud, do ChromaDB, da base
  documental ou de `data/ecopontos.json` são convertidos em mensagens
  orientativas, sem chaves, tokens, traces ou detalhes sensíveis.
- **Sessão:** o botão “Limpar conversa” apaga o histórico e reinicia o
  estado da sessão.

## Contradição temporal e detalhe escondido

A base contém uma contradição proposital entre documentos:

- `lista_ecopontos.md` (fevereiro de 2026) e `regulamento_descarte.md`
  informam que o Parque das Acácias aceita pilhas e baterias;
- `comunicado_interdicao.md` informa que o Parque fica interditado de
  **15/03/2026 a 31/05/2026**;
- a partir de **01/06/2026**, o comunicado retira pilhas e baterias do
  Parque e altera o horário para segunda a sexta, 08h–17h, e sábado,
  08h–12h.

A resposta correta depende da data de referência. Em datas dentro da
interdição, o Parque não deve ser indicado como disponível; após 01/06/2026,
a informação mais recente prevalece. O serviço RAG recebe `--as-of`, inclui
essas regras no contexto e a ferramenta `consultar_ecopontos` aplica a mesma
lógica aos dados estruturados.

O detalhe escondido é o descarte de **medicamentos vencidos**: eles não são
aceitos nos Ecopontos. O destino correto é a Farmácia Municipal EcoSaúde,
Rua das Palmeiras, 77, Centro, de segunda a sexta, 08h–17h. Esse conteúdo
aparece no regulamento e é usado para verificar se o RAG recupera a fonte
correta em vez de responder apenas com a lista geral de Ecopontos.

## Testes automatizados

A suíte usa `unittest`, não depende de chamadas reais ao Ollama Cloud e cobre
ingestão, chunking, embeddings, ChromaDB, RAG, temporalidade, guardrails,
ferramentas, agente, avaliação, CLI e interface:

```powershell
python -m unittest discover -s tests -v
```

No estado atual, os **151 testes passam**. Os testes de integração com o
modelo real não substituem a validação manual quando a conta tiver créditos.
A validação final também inclui `python -m compileall src scripts tests app.py`
e `python -m pip check`.

## Avaliação RAGAS e comparação de chunking

O dataset em `src/ecocidadao/evaluation/dataset.json` contém exatamente
oito perguntas: quatro simples e quatro de armadilha. As perguntas de
armadilha exigem resolver a interdição do Parque das Acácias, a mudança
permanente após 1º/06/2026 ou a prevalência do comunicado mais recente
sobre a lista de fevereiro. Todos os `ground_truth` estão marcados como
`pendente_validacao_humana`; eles são rascunhos técnicos e não foram
declarados validados pelos integrantes ou pelo professor.

Avaliação real:

```powershell
python scripts/evaluate_ragas.py
```

O runner recupera contextos, tenta gerar as respostas com o modelo
configurado e aplica `faithfulness`, `answer_relevancy`,
`context_precision` e `context_recall`. A saída é
`avaliacao_ragas.json`, com pergunta, resposta gerada, contextos,
ground truth e métricas. A execução local atual está registrada como
`pendente` porque o Ollama Cloud retornou **HTTP 402**; as métricas
permanecem `null` e o motivo está documentado no arquivo.

Comparação de chunking:

```powershell
python scripts/compare_chunking.py
```

A saída é `data/experiments/chunking_comparison.json`. A comparação usa
as duas estratégias já implementadas, recria índices temporários no
ChromaDB com os mesmos embeddings locais e mede, por pergunta, Hit@3,
Hit@5, MRR e métricas documentais de precision/recall. Na execução local:

| Estratégia | Chunks | Média de caracteres | Hit@3 | Hit@5 | MRR | Precision documental | Recall documental |
|---|---:|---:|---:|---:|---:|---:|---:|
| E1 fixo | 17 | 607 | 1,0 | 1,0 | 1,0 | 0,725 | 1,0 |
| E2 markdown | 22 | 453,77 | 1,0 | 1,0 | 1,0 | 0,800 | 0,875 |

As métricas documentais de precision/recall são proxies calculados a
partir dos `reference_doc_ids`; não são as métricas RAGAS. As métricas
RAGAS de contexto continuam pendentes de LLM. Por isso o experimento
registra `winner = null` e não declara uma estratégia vencedora.

## Variáveis de ambiente

| Variável | Finalidade |
|---|---|
| `APP_ENV` | Ambiente da aplicação (`dev`, `test`, `prod`). |
| `LOG_LEVEL` | Nível de log. |
| `OLLAMA_API_KEY` | Chave do Ollama Cloud; nunca versionar. |
| `OLLAMA_BASE_URL` | Endereço da API do Ollama Cloud. |
| `OLLAMA_MODEL` | Modelo de linguagem a ser utilizado. |
| `LLM_TEMPERATURE` | Temperatura do modelo. |
| `LLM_MAX_TOKENS` | Limite de tokens da resposta. |
| `LLM_TIMEOUT_S` | Timeout das chamadas ao modelo. |
| `EMBEDDING_MODEL` | Modelo local de embeddings. |
| `EMBEDDING_DEVICE` | Dispositivo de execução (`cpu` ou `cuda`). |
| `HF_HOME` | Cache local dos modelos de Hugging Face. |
| `BASE_DOCS_DIR` | Pasta da base documental. |
| `CHROMA_DIR` | Pasta persistente do ChromaDB. |
| `ECOPONTOS_DATA_PATH` | Dados estruturados dos Ecopontos. |
| `EVALUATION_DATASET_PATH` | Dataset das oito perguntas do RAGAS. |
| `RAGAS_OUTPUT_PATH` | Arquivo de saída da avaliação real. |
| `CHUNKING_EXPERIMENT_PATH` | Arquivo da comparação medida de chunking. |
| `COLLECTION_NAME` | Coleção padrão do ChromaDB. |
| `RETRIEVAL_TOP_K` | Quantidade de trechos recuperados. |
| `RETRIEVAL_FETCH_K` | Candidatos avaliados antes do ranking final. |
| `RETRIEVAL_SCORE_THRESHOLD` | Limiar mínimo de relevância. |
| `MAX_CONTEXT_CHARS` | Limite de contexto enviado ao modelo. |
| `MAX_INPUT_CHARS` | Limite de caracteres da pergunta. |
| `MAX_TOOL_CALLS` | Limite de chamadas de ferramentas (máximo 6). |
| `GRADIO_SERVER_NAME` | Endereço local da interface. |
| `GRADIO_SERVER_PORT` | Porta local da interface. |

## Justificativa para a ausência do notebook

O professor autorizou expressamente a execução local do projeto e a
retirada do arquivo `.ipynb` da entrega, desde que o motivo fosse
documentado. Por esse motivo:

- todo o projeto é implementado em módulos Python (`.py`);
- não há notebook Jupyter na entrega;
- não são utilizadas dependências de Jupyter;
- não é utilizado Google Colab;
- a execução, os testes e a avaliação são feitos localmente no PyCharm;
- este README documenta a instalação, a execução e a organização do
  projeto.

## Limitações

- A base é acadêmica e fictícia, com apenas três documentos e um arquivo de
  Ecopontos; não é uma base oficial de município real.
- A avaliação RAGAS real, as respostas reais do agente e a validação manual
  da interface continuam bloqueadas pelo HTTP 402 do Ollama Cloud.
- Os oito `ground_truth` do dataset são rascunhos técnicos e ainda não foram
  validados por uma pessoa.
- Os guardrails são heurísticos: reduzem risco, mas não substituem revisão
  humana, moderação ou uma política de segurança mais ampla.
- O `scikit-network` não tem wheel recente para Python 3.14; ele é usado
  apenas na geração de testset do RAGAS, não nas métricas executadas.
- O projeto não consulta sites, APIs públicas ou dados em tempo real; toda a
  resposta depende da base local e das ferramentas implementadas.
- O arquivo `.env` real não é entregue; a chave precisa ser configurada pelo
  avaliador.

## Próximas etapas

1. ~~Criação dos três documentos autorais da base documental.~~ Concluído.
2. ~~Ingestão, metadados e comparação de duas estratégias de chunking.~~
   Concluído.
3. ~~Indexação no ChromaDB com embeddings locais.~~ Concluído.
4. ~~Pipeline RAG com LCEL, citações e recusa sem evidência.~~ Concluído;
   falta validar a resposta real do Ollama Cloud.
5. ~~Guardrails de escopo, prompt injection, LGPD e contexto
   insuficiente.~~ Concluído.
6. ~~Agente com ferramentas e limite de seis chamadas.~~ Concluído;
   falta validar com o Ollama Cloud real.
7. ~~Interface Gradio com histórico e fontes.~~ Concluído; falta validar
   com o Ollama Cloud real.
8. ~~Dataset de oito perguntas, runner RAGAS e comparação medida de
   chunking.~~ Concluído; a avaliação RAGAS real continua pendente.
9. Finalização dos entregáveis, vídeo e checklist da entrega.

## Pendências conhecidas

- Adicionar créditos à conta do Ollama Cloud para validar respostas reais.
- Executar `python scripts/evaluate_ragas.py` com créditos e substituir o
  status `pendente` de `avaliacao_ragas.json` por métricas reais.
- Validar os oito `ground_truth` marcados como
  `pendente_validacao_humana`.
- Confirmar a compatibilidade do Python 3.14.3 ou usar Python 3.12.
- Validar guardrails, agente e interface com respostas reais do Ollama
  Cloud quando a conta tiver créditos.
- Concluir `certificacao.txt`, `Chat_log.txt` e `demo_video_url.txt`; os
  arquivos atuais são marcadores de pendência e não contêm dados inventados.
- Preencher os nomes dos integrantes do trio.
