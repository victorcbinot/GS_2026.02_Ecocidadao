# Conclusão

O EcoCidadão entrega pipeline RAG, agente com quatro ferramentas, guardrails,
interface Gradio e 152 testes passando. Na avaliação real preservada em
`avaliacao_ragas.json`: faithfulness 0,570833, answer relevancy 0,180817,
context precision 0,520833 e context recall 0,937500. A recuperação é o ponto
forte; a geração é prolixa e pouco aderente. No chunking, o fixo teve 17 chunks
e precision 0,7250; o Markdown teve 22 chunks, precision 0,8000 e é recomendado
por preservar seções. As limitações são o HTTP 402 da Ollama Cloud, o RAGAS com
Qwen local como gerador e juiz, duas armadilhas sem contexto e ground truths
sem validação humana. As melhorias são separar gerador e juiz, corrigir os
contextos do RAGAS, encurtar respostas, ajustar recuperação/reranking e validar
o dataset. Certificação, turma/instituição e vídeo dependem de dados humanos.
