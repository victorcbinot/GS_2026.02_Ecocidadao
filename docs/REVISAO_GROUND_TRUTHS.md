# Validação humana das 8 ground truths

## Registro da validação

- Revisor: **Victor Binot**
- RM: **571499**
- Data da conferência: **18/11/2026**
- Formulário respondido: `docs/FORMULARIO_VALIDACAO_GROUND_TRUTHS.md`
- Resultado: **8 de 8 itens confirmados como OK, sem correções**
- Status registrado no dataset: `validado_humanamente`

A validação foi feita por leitura direta de cada pergunta e resposta de
referência de `src/ecocidadao/evaluation/dataset.json` contra os trechos
correspondentes de `base_documental/`.

## Escopo da conferência

Foram verificados:

- existência e data dos documentos citados;
- seção de referência;
- coerência entre pergunta, data de referência (`as_of`), resposta e pontos
  esperados;
- tratamento correto dos conflitos temporais do Parque das Acácias.

Nenhuma resposta de referência precisou ser corrigida.

## Tabela de validação

| ID | Tipo | Data de referência | Fontes conferidas | Resultado | Status |
|---|---|---|---|---|---|
| `simple_medicamentos` | simples | 2026-06-10 | `regulamento_descarte`, seção 6 | OK: medicamentos não vão em Ecopontos; destino é a Farmácia Municipal EcoSaúde, Rua das Palmeiras, 77, Centro, segunda a sexta, 08:00–17:00. | Validado |
| `simple_vila_verde` | simples | 2026-06-10 | `lista_ecopontos`, “Ecopontos em funcionamento” e “Materiais não aceitos” | OK: papel, papelão, vidro, plástico, metal e óleo usado; terça a sábado, 08:00–16:00. | Validado |
| `simple_oleo` | simples | 2026-06-10 | `lista_ecopontos`, “Observações importantes”; `regulamento_descarte`, seção 5 | OK: exclusivamente Vila Verde, garrafa PET lacrada, máximo de 2 litros por entrega. | Validado |
| `simple_entulho` | simples | 2026-06-10 | `lista_ecopontos`, “Observações importantes”; `regulamento_descarte`, seção 5 | OK: somente Ecoponto Industrial, 2 m³ por mês por domicílio. | Validado |
| `trap_parque_interdito_pilhas` | armadilha | 2026-04-20 | `comunicado_interdicao`, seções 1 e 2; `lista_ecopontos` | OK: interdição de 15/03/2026 a 31/05/2026, inclusive; em 20/04 não recebe material; pilhas vão ao Industrial. | Validado |
| `trap_parque_pos_reabertura_pilhas` | armadilha | 2026-06-10 | `comunicado_interdicao`, seções 3 e 4; `lista_ecopontos` | OK: a partir de 01/06/2026 o Parque deixa de aceitar pilhas e baterias; elas passam a ser exclusivas do Industrial. | Validado |
| `trap_parque_interdito_eletronicos` | armadilha | 2026-04-20 | `comunicado_interdicao`, seções 1 e 2; `lista_ecopontos` | OK: durante a interdição o Parque não recebe nada; eletrônicos vão ao Industrial. | Validado |
| `trap_parque_horario_pos_reabertura` | armadilha | 2026-06-10 | `comunicado_interdicao`, seção 3; `lista_ecopontos`, “Ecopontos em funcionamento” | OK: novo horário é segunda a sexta, 08:00–17:00, e sábado, 08:00–12:00, a partir de 01/06/2026, substituindo segunda a sábado, 07:00–19:00. | Validado |

## Distribuição

- 4 perguntas simples: `simple_medicamentos`, `simple_vila_verde`,
  `simple_oleo`, `simple_entulho`.
- 4 perguntas de armadilha:
  - `trap_parque_interdito_pilhas` — período de interdição;
  - `trap_parque_pos_reabertura_pilhas` — mudança permanente após reabertura;
  - `trap_parque_interdito_eletronicos` — período de interdição;
  - `trap_parque_horario_pos_reabertura` — horário substituído por comunicado.

## Declaração

Declaro que conferi os oito itens contra os documentos de `base_documental/` e
que as respostas de referência estão corretas para uso na avaliação.

Victor Binot — RM 571499 — 18/11/2026
