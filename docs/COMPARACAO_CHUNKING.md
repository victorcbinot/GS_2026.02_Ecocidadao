# Comparação de chunking — fixo versus Markdown

## Dados reais utilizados

- Script: `python scripts/compare_chunking.py`
- Saída: `data/experiments/chunking_comparison.json`
- Documentos: 3 (`lista_ecopontos.md`, `regulamento_descarte.md`,
  `comunicado_interdicao.md`)
- Perguntas: 8 (4 simples e 4 armadilhas)
- `top_k`: 5
- Embeddings: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
  local, CPU
- Índices: ChromaDB temporário, recriado para cada estratégia
- Ground truths: `pendente_validacao_humana`

Configurações comparadas:

| Estratégia | Tamanho | Sobreposição |
|---|---:|---:|
| Fixo | 800 caracteres | 150 |
| Markdown | 800 caracteres | 100 |

## Resultados medidos

| Estratégia | Chunks | Média de caracteres | Mediana | Hit@3 | Hit@5 | MRR | Precision documental | Recall documental |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Fixo | 17 | 607,00 | 569,0 | 1,0000 | 1,0000 | 1,0000 | 0,7250 | 1,0000 |
| Markdown | 22 | 453,77 | 469,5 | 1,0000 | 1,0000 | 1,0000 | 0,8000 | 0,8750 |

As métricas de precision/recall documental são proxies calculados a partir de
`reference_doc_ids`; não são as métricas RAGAS. O JSON continua com
`winner=null` porque não há execução RAGAS por estratégia, mas registra
`recommended_strategy=markdown` e a justificativa em `recommendation_reason`.
A recomendação é uma decisão de engenharia baseada nos dados de retrieval
disponíveis, não um “vencedor” estatístico definitivo.

## Onde as estratégias diferem

- **Hit@3, Hit@5 e MRR são idênticos.** As duas estratégias colocam pelo menos
  um documento relevante no top 5 e o primeiro documento relevante na primeira
  posição em todas as perguntas. Isso mostra que o corpus é pequeno e o
  retrieval é fácil nesse recorte.
- **Markdown tem precisão documental maior:** 0,8000 contra 0,7250. Em média,
  uma proporção maior dos cinco chunks recuperados pertence a documentos
  realmente necessários.
- **Fixo tem recall documental maior:** 1,0000 contra 0,8750. A diferença
  aparece em duas armadilhas:
  - `trap_parque_interdito_pilhas`;
  - `trap_parque_pos_reabertura_pilhas`.
  Nos dois casos, o Markdown recuperou o `comunicado_interdicao`, mas não
  recuperou a `lista_ecopontos` no top 5. O comunicado contém a alternativa
  (Ecoponto Industrial), portanto a resposta ainda pode ser correta, mas a
  comparação entre a regra antiga e a nova fica menos explícita.
- **Markdown gera chunks menores e mais numerosos:** 22 chunks e média de
  453,77 caracteres, contra 17 chunks e média de 607 no fixo. Chunks menores
  reduzem ruído no prompt, desde que a seção seja autoexplicativa.
- **Markdown preserva a hierarquia de seções.** Os metadados `section_h1`,
  `section_h2`, `section_h3` e `section_path` permitem citar “3. Reabertura e
  mudanças permanentes” em vez de apenas o documento inteiro. Isso é
  especialmente importante para o conflito temporal do Parque das Acácias.

## Decisão recomendada

**Adotar a estratégia Markdown como padrão.**

Justificativa com evidências:

1. Empata nas métricas de ranking (Hit@3, Hit@5 e MRR = 1,0).
2. Tem precision documental maior (0,8000 contra 0,7250), o que reduz o
   volume de chunks irrelevantes enviados ao modelo.
3. Preserva a estrutura das seções, essencial para citar corretamente as
   regras temporais.
4. É a estratégia usada na execução RAGAS preservada em
   `avaliacao_ragas.json`, que obteve `context_recall=0,9375`.
5. Gera chunks menores (média 453,77 caracteres), deixando o contexto mais
   focado.

Ressalvas que acompanham a decisão:

- O recall documental caiu de 1,0 para 0,875 nas duas armadilhas de pilhas.
  Para mitigar, perguntas temporais já usam janela ampliada de recuperação
  (`TEMPORAL_TOP_K=10`), o que deve trazer a lista antiga para o contexto.
- O `top_k=5` da comparação é menor que o `top_k=6` da avaliação e que a janela
  temporal de 10 usada em perguntas com data. A decisão não deve ser lida como
  “Markdown é melhor em qualquer configuração”.
- O corpus tem apenas três documentos. Em bases maiores, o recall do Markdown
  precisa ser reavaliado com mais perguntas e, idealmente, com RAGAS por
  estratégia.

## Alternativa

O chunking fixo é um fallback defensável quando o requisito principal for
recall documental máximo e não houver custo relevante de contexto. Neste
projeto, a estrutura Markdown e a precisão maior pesaram mais, porque as
perguntas de armadilha dependem de seção e vigência, não apenas de presença do
documento.
