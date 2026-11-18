# Revisão das 8 ground truths

## Escopo da revisão

As oito respostas de referência de `src/ecocidadao/evaluation/dataset.json`
foram conferidas manualmente contra os três documentos de
`base_documental/`. A revisão verificou:

- existência e data dos documentos citados;
- seção de referência;
- coerência entre pergunta, data de referência (`as_of`), resposta e pontos
  esperados;
- tratamento correto dos conflitos temporais do Parque das Acácias.

Nenhuma linha do dataset foi alterada nesta revisão. As respostas estavam
factualmente coerentes com os documentos. **Todos os oito registros continuam
marcados como `pendente_validacao_humana`, pois a validação por uma pessoa do
grupo ou pelo professor ainda não ocorreu.**

## Tabela de revisão

| ID | Tipo | Data de referência | Fontes conferidas | Resultado da revisão | Status |
|---|---|---|---|---|---|
| `simple_medicamentos` | simples | 2026-06-10 | `regulamento_descarte`, seção 6 | Correto: medicamentos não vão em Ecopontos; destino é a Farmácia Municipal EcoSaúde, Rua das Palmeiras, 77, Centro, segunda a sexta, 08:00–17:00. | Pendente de validação humana |
| `simple_vila_verde` | simples | 2026-06-10 | `lista_ecopontos`, “Ecopontos em funcionamento” e “Materiais não aceitos” | Correto: papel, papelão, vidro, plástico, metal e óleo usado; terça a sábado, 08:00–16:00. | Pendente de validação humana |
| `simple_oleo` | simples | 2026-06-10 | `lista_ecopontos`, “Observações importantes”; `regulamento_descarte`, seção 5 | Correto: exclusivamente Vila Verde, garrafa PET lacrada, máximo de 2 litros por entrega. | Pendente de validação humana |
| `simple_entulho` | simples | 2026-06-10 | `lista_ecopontos`, “Observações importantes”; `regulamento_descarte`, seção 5 | Correto: somente Ecoponto Industrial, 2 m³ por mês por domicílio. | Pendente de validação humana |
| `trap_parque_interdito_pilhas` | armadilha | 2026-04-20 | `comunicado_interdicao`, seções 1 e 2; `lista_ecopontos` | Correto: interdição de 15/03/2026 a 31/05/2026, inclusive; em 20/04 não recebe material; pilhas vão ao Industrial. | Pendente de validação humana |
| `trap_parque_pos_reabertura_pilhas` | armadilha | 2026-06-10 | `comunicado_interdicao`, seções 3 e 4; `lista_ecopontos` | Correto: a partir de 01/06/2026 o Parque deixa de aceitar pilhas e baterias; elas passam a ser exclusivas do Industrial. | Pendente de validação humana |
| `trap_parque_interdito_eletronicos` | armadilha | 2026-04-20 | `comunicado_interdicao`, seções 1 e 2; `lista_ecopontos` | Correto: durante a interdição o Parque não recebe nada; eletrônicos vão ao Industrial. | Pendente de validação humana |
| `trap_parque_horario_pos_reabertura` | armadilha | 2026-06-10 | `comunicado_interdicao`, seção 3; `lista_ecopontos`, “Ecopontos em funcionamento” | Correto: novo horário é segunda a sexta, 08:00–17:00, e sábado, 08:00–12:00, a partir de 01/06/2026, substituindo segunda a sábado, 07:00–19:00. | Pendente de validação humana |

## Distribuição

- 4 perguntas simples: `simple_medicamentos`, `simple_vila_verde`,
  `simple_oleo`, `simple_entulho`.
- 4 perguntas de armadilha:
  - `trap_parque_interdito_pilhas` — período de interdição;
  - `trap_parque_pos_reabertura_pilhas` — mudança permanente após reabertura;
  - `trap_parque_interdito_eletronicos` — período de interdição;
  - `trap_parque_horario_pos_reabertura` — horário substituído por comunicado.

## O que falta para deixar de ser pendente

- Nome e RM do revisor humano.
- Data da validação.
- Confirmação de que as três fontes documentais são as oficiais do trabalho.
- Aceite formal de que a resposta de referência pode ser usada como nota.
