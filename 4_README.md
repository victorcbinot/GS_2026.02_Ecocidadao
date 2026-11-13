# EcoCidadão

Assistente municipal inteligente para orientar cidadãos sobre descarte
correto de resíduos, materiais aceitos e proibidos e utilização de
Ecopontos.

> **Aviso:** EcoCidade é um município fictício. Todos os documentos,
> endereços, horários, limites e comunicados do projeto são simulados e
> não representam dados reais de nenhum município.

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

**Etapas 1 a 6 concluídas. Serviço RAG, guardrails, agente com
ferramentas e interface Gradio implementados; avaliação RAGAS ainda
pendente.**

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

A validação com o Ollama Cloud está bloqueada temporariamente por falta
de créditos na conta (HTTP 402). O serviço e os testes com LLM simulado
estão funcionando; a resposta real do modelo será validada quando houver
créditos.

## Tecnologias utilizadas e previstas

- Python.
- LangChain e LCEL.
- ChatOllama com Ollama Cloud.
- Embeddings locais com `sentence-transformers` e o modelo
  `paraphrase-multilingual-MiniLM-L12-v2`.
- ChromaDB com persistência local e duas coleções independentes.
- Gradio 6.32 para a interface local; o código mantém compatibilidade
  com a API de mensagens do Gradio 5.
- RAGAS.
- python-dotenv e pydantic-settings.
- unittest para os testes atuais; Pytest previsto para etapas futuras.

## Estrutura do projeto

```text
GS_2026.02_Ecocidadao/
├── 2_base_documental/          # documentos da base de conhecimento
├── 3_avaliacao_ragas.json      # será gerado pela avaliação real
├── 4_README.md                 # este arquivo
├── 5_certificacao.txt         # pendente de definição
├── 6_Chat_Log.txt             # pendente de definição
├── 7_demo_video_url.txt       # pendente de gravação
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
`gradio` 6.32 foi instalada e validada neste ambiente; a avaliação
(`ragas` e `datasets`) ainda será instalada e validada. Caso alguma
dependência não ofereça suporte, recomenda-se criar o ambiente virtual
com Python 3.11 ou 3.12. Nenhuma configuração global do computador deve
ser alterada.

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
instaladas em `.venv/`.

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
**136 testes automatizados**:

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
| `CHUNK_STRATEGY` | Estratégia de chunking (`fixo` ou `markdown`). |
| `COLLECTION_NAME` | Coleção do ChromaDB. |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | Parâmetros de chunking. |
| `RETRIEVAL_TOP_K` | Quantidade de trechos recuperados. |
| `RETRIEVAL_FETCH_K` | Candidatos avaliados antes do ranking final. |
| `RETRIEVAL_MMR_LAMBDA` | Equilíbrio entre relevância e diversidade. |
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
8. Avaliação RAGAS com oito perguntas reais.
9. Finalização dos entregáveis, vídeo e checklist da entrega.

## Pendências conhecidas

- Adicionar créditos à conta do Ollama Cloud para validar respostas reais.
- Confirmar a compatibilidade do Python 3.14.3 ou usar Python 3.12.
- Instalar e validar `ragas` e `datasets`.
- Implementar a avaliação RAGAS com oito perguntas reais.
- Validar guardrails, agente e interface com respostas reais do Ollama
  Cloud quando a conta tiver créditos.
- Gerar `3_avaliacao_ragas.json`, `5_certificacao.txt`, `6_Chat_Log.txt`
  e `7_demo_video_url.txt`.
- Preencher os nomes dos integrantes do trio.
- Remover ou substituir o `main.py` de exemplo, se a equipe autorizar.
