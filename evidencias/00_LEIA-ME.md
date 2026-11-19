# Evidências reais do EcoCidadão

## Ressalva de ambiente

As capturas de interface foram feitas em 19/11/2026 com o modelo local
`qwen2.5:7b`, porque a Ollama Cloud retornou HTTP 402 por falta de créditos
para o `gpt-oss:20b`. O `.env` passou a usar o agente principal e o juiz RAGAS
em `qwen2.5:7b` local. Em máquinas com falha de CUDA, `LLM_NUM_GPU=28` limita
as camadas na GPU; `0` força CPU.

As evidências abaixo são reais. Nenhum print, resposta, fonte ou ferramenta
foi inventado. A contingência local está declarada em cada caso.

## Interface Gradio

- `04b_interface_gradio_consulta.png` — pergunta sobre pilhas no Parque das
  Acácias em 20/04/2026, respondida pelo agente com a ferramenta
  `consultar_ecopontos` e sem fonte documental.
- `04c_interface_gradio_rag_fontes.png` — pergunta sobre medicamentos vencidos,
  respondida com `consultar_base_documental` e painel de fonte documental `[F1]`.
- `04d_interface_gradio_guardrail.png` — pergunta fora do escopo ("Como faço um
  bolo de chocolate?") recusada antes de consultar o modelo ou a base, com
  evento `input_scope_blocked`.

Comando usado para subir a interface com contingência local:

```powershell
$env:OLLAMA_BASE_URL='http://127.0.0.1:11434'
$env:OLLAMA_MODEL='qwen2.5:7b'
$env:OLLAMA_API_KEY=''
$env:GRADIO_SERVER_PORT='7861'
python app.py
```

As capturas foram feitas em 19/11/2026, em resolução de 1511x896 a 1556x915
conforme a janela do navegador. Os arquivos PNG são capturas diretas da página
renderizada.

## Logs de CLI

- `01_rag_consulta.txt` — consulta RAG com citação `[F1]`; modelo local.
- `02_agente_ferramentas.txt` — agente usando `consultar_ecopontos`.
- `02b_agente_ferramentas_combinadas.txt` — agente usando
  `consultar_ecopontos` e `calcular` na mesma pergunta.
- `03_guardrail_escopo.txt` — recusa de pergunta fora do escopo.
- `03b_guardrail_injection.txt` — bloqueio de prompt injection.
- `03c_guardrail_lgpd.txt` — bloqueio de pedido de dados pessoais.
- `05_testes.txt` — saída da suíte completa de testes (155 testes).
- `06_comparacao_chunking.txt` — comparação real fixo versus Markdown.
- `07_configuracao_modelos.txt` — confirmação dos modelos do agente e do juiz,
  endpoints locais, embeddings locais e limite de 6 ferramentas. A chave não é
  exibida.

## O que não foi possível capturar

- Resposta real do agente `gpt-oss:20b` na Ollama Cloud: a conta retorna
  HTTP 402.
- Avaliação RAGAS com GPT-OSS 20B gerando respostas: mesma limitação.
- Vídeo de demonstração: ainda não gravado; ver `demo_video_url.txt`.

## Como validar que não são prints fictícios

- Os logs foram gerados pelos comandos descritos no README e contêm as saídas
  reais do terminal.
- As capturas Gradio foram obtidas de uma instância real em
  `http://127.0.0.1:7861`, com o app iniciado por `python app.py`.
- As respostas e fontes seguem o mesmo pipeline, a mesma base documental e os
  mesmos guardrails descritos em `Chat_Log.txt`. As capturas atuais substituem
  as versões anteriores.
