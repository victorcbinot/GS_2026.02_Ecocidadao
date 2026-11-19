# Avaliação RAGAS — resultados reais e interpretação

## Origem dos dados

Os resultados abaixo vêm exclusivamente de `avaliacao_ragas.json`, gerado em
`2026-11-18T01:41:48Z`. O arquivo foi preservado; nenhum valor foi recalculado
ou inventado. As tabelas abaixo usam até seis casas decimais; os valores
originais permanecem no JSON.

Configuração registrada nessa execução:

| Item | Valor |
|---|---|
| Coleção | `ecocidadao_markdown` |
| Estratégia de chunking | Markdown |
| `top_k` | 6 |
| Modelo que gerou as respostas | `qwen2.5:7b` local |
| Endpoint do gerador | `http://127.0.0.1:11434` |
| Juiz RAGAS | `qwen2.5:7b` local |
| Embeddings | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (CPU) |
| RAGAS | 0.4.4 |
| Dataset | 8 perguntas (4 simples e 4 armadilhas) |

> **Ressalva importante:** a execução registrada usou o `qwen2.5:7b` local
> como gerador das respostas e como juiz. A configuração atual do sistema
> separa o agente principal (`gpt-oss:20b` na Ollama Cloud) do juiz RAGAS
> (`qwen2.5:7b` local), mas a conta Cloud retorna HTTP 402 por falta de
> créditos. Por isso não foi possível repetir a geração com o GPT-OSS 20B.
> O resultado é real para a configuração registrada no JSON, não para uma
> execução com GPT-OSS 20B.

## O que cada métrica mede

| Métrica | Pergunta que responde | Resultado geral |
|---|---|---:|
| `faithfulness` | As afirmações da resposta são sustentadas pelo contexto recuperado? | 0,570833 |
| `answer_relevancy` | A resposta realmente responde à pergunta feita? | 0,180817 |
| `context_precision` | Os trechos recuperados são relevantes e aparecem antes dos irrelevantes? | 0,520833 |
| `context_recall` | O contexto recuperado cobre a informação necessária do ground truth? | 0,937500 |

## Resultados por pergunta

| ID | Categoria | Faithfulness | Answer relevancy | Context precision | Context recall | Observação |
|---|---|---:|---:|---:|---:|---|
| `simple_medicamentos` | simples | 0,750000 | 0,000000 | 1,000000 | 1,000000 | Resposta correta, mas prolixa e com ressalva desnecessária; relevância foi a zero. |
| `simple_vila_verde` | simples | 0,750000 | 0,776081 | 0,666667 | 1,000000 | Melhor resposta do conjunto; ainda inclui observações genéricas. |
| `simple_oleo` | simples | 0,833333 | 0,000000 | 0,500000 | 1,000000 | Conteúdo correto, porém resposta longa e com recomendação não solicitada. |
| `simple_entulho` | simples | 0,400000 | 0,000000 | 0,500000 | 1,000000 | Repetiu o limite e acrescentou informação não sustentada sobre “limite diário”. |
| `trap_parque_interdito_pilhas` | armadilha | 1,000000 | 0,325475 | 0,500000 | 1,000000 | Contexto correto; resposta descritiva, sem responder de forma direta e curta. |
| `trap_parque_pos_reabertura_pilhas` | armadilha | 0,000000 | 0,000000 | 0,000000 | 1,000000 | Nenhum contexto foi exposto na resposta e o sistema usou a recusa padrão. |
| `trap_parque_interdito_eletronicos` | armadilha | 0,000000 | 0,000000 | 0,000000 | 1,000000 | Mesmo comportamento: recusa padrão sem contexto apresentado. |
| `trap_parque_horario_pos_reabertura` | armadilha | 0,833333 | 0,344982 | 1,000000 | 0,500000 | Recuperou o comunicado, mas não a lista antiga; resposta não fechou o horário novo de forma completa. |

## Interpretação

1. **A recuperação de contexto é o ponto forte.** `context_recall` ficou em
   0,9375 e sete das oito perguntas chegaram a 1,0. O retriever encontrou os
   documentos certos na maior parte dos casos, inclusive nos conflitos
   temporais.
2. **A precisão do contexto é mediana.** `context_precision` de 0,5208 indica
   que vários trechos irrelevantes ocupam as primeiras posições. Exemplo:
   perguntas simples recuperam o comunicado de interdição, que não é
   necessário para responder sobre medicamentos ou Vila Verde.
3. **A fidelidade é limitada.** `faithfulness` de 0,5708 cai principalmente
   em `simple_entulho` (0,4) e nas duas respostas de recusa (0,0). Isso indica
   afirmações não sustentadas pelo contexto e respostas genéricas que não
   podem ser verificadas apenas pelos trechos.
4. **A relevância das respostas é o pior indicador.** `answer_relevancy` de
   0,1808 é muito baixa, com cinco notas zero. As respostas são corretas em
   vários casos, mas longas, defensivas e cheias de ressalvas. O modelo local
   frequentemente acrescenta “não encontrei informações” depois de já ter
   respondido, o que prejudica a métrica e a experiência do usuário.
5. **Há uma anomalia nas duas perguntas com contexto vazio.**
   `trap_parque_pos_reabertura_pilhas` e
   `trap_parque_interdito_eletronicos` ficaram com `contexts=[]` no JSON, mas
   receberam `context_recall=1,0`. Isso é inconsistente: sem contexto não há
   como afirmar cobertura total. O valor não deve ser interpretado como
   evidência de boa recuperação nessas duas perguntas; é um artefato da
   execução e um ponto a corrigir antes da próxima avaliação.
6. **A resposta para o horário pós-reabertura não usou a lista antiga.**
   `context_recall=0,5` mostra que faltou um dos documentos de referência. O
   comunicado sozinho permite responder ao horário novo, mas a comparação com
   o horário anterior ficou incompleta.

## Problemas principais

- Prompt do RAG permissivo demais: o modelo acrescenta recomendações,
  ressalvas e frases de limitação mesmo quando o contexto já responde.
- `top_k=6` sem reranking traz chunks redundantes e documentos vizinhos
  pouco úteis, reduzindo `context_precision`.
- O runner usa `response.sources` (fontes efetivamente citadas) para montar os
  contextos do RAGAS. Quando a resposta é uma recusa padrão, as fontes podem
  ficar vazias; isso produz o caso anômalo de `contexts=[]` com
  `context_recall=1,0`.
- O mesmo modelo local foi gerador e juiz, o que pode introduzir viés de
  autoavaliação. A configuração pretendida separa GPT-OSS 20B (gerador) e
  Qwen 2.5 7B (juiz).
- Os ground truths foram validados por Victor Binot (RM 571499) em 18/11/2026;
  o registro está em `docs/REVISAO_GROUND_TRUTHS.md`.

## Melhorias concretas, em ordem de prioridade

1. **Corrigir a montagem dos contextos do RAGAS:** usar sempre os trechos
   recuperados (`contexts`/`context_metadata`) e não apenas as fontes citadas
   na resposta. Tratar `contexts=[]` explicitamente como falha de cobertura.
2. **Encurtar e direcionar as respostas:** incluir no prompt “responda em até
   três frases, comece pela conclusão, cite apenas as fontes usadas e não
   acrescente ressalvas se o contexto já responde”.
3. **Pós-processar a saída:** remover blocos genéricos de encerramento e
   frases de limitação quando já houver resposta factual com citação válida.
4. **Ajustar a recuperação:** reduzir `top_k` para perguntas simples, manter
   janela ampliada em perguntas temporais, deduplicar chunks do mesmo
   documento e testar um reranker local.
5. **Reexecutar com a configuração-alvo:** GPT-OSS 20B para gerar respostas e
   Qwen 2.5 7B como juiz, quando a conta Cloud tiver créditos. Registrar no
   JSON que os modelos são distintos.
6. **Manter o registro da validação humana** atualizado em
   `docs/REVISAO_GROUND_TRUTHS.md` sempre que o dataset mudar.
7. **Ampliar o conjunto de avaliação** para reduzir a variância de médias
   calculadas sobre apenas oito perguntas.

## Conclusão da avaliação

O pipeline recupera evidências relevantes com frequência alta, mas ainda
responde de forma prolixa e pouco aderente ao formato ideal. A próxima
prioridade não é trocar o retriever, e sim controlar a geração e corrigir a
forma como os contextos são registrados para o RAGAS. As métricas de 0,5708
(faithfulness), 0,1808 (answer relevancy), 0,5208 (context precision) e
0,9375 (context recall) são reais, mas devem ser lidas com as ressalvas de
modelo gerador local e ground truths validados por Victor Binot em 18/11/2026.
