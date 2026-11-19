# Conclusão

O EcoCidadão entrega pipeline RAG, agente com quatro ferramentas, guardrails,
interface Gradio e 155 testes passando. Na avaliação real preservada em
`avaliacao_ragas.json`: faithfulness 0,570833, answer relevancy 0,180817,
context precision 0,520833 e context recall 0,937500. A recuperação é o ponto
forte; a geração é prolixa e pouco aderente. No chunking, o fixo teve 17 chunks
e precision 0,7250; o Markdown teve 22 chunks, precision 0,8000 e é recomendado
por preservar seções. As limitações são o HTTP 402 da Ollama Cloud, o RAGAS com
Qwen local como gerador e juiz e duas armadilhas sem contexto. Os ground truths
foram reescritos e validados por Victor Binot (RM 571499) em 18/11/2026. As melhorias são
separar gerador e juiz, corrigir os contextos do RAGAS, encurtar respostas e
ajustar recuperação/reranking. Certificação e vídeo ainda dependem de dados
humanos; a execução local, sem notebook, está justificada no README.
