# Ficha para reescrita manual dos ground truths

Esta ficha não contém o texto final. Ela lista apenas os fatos que precisam
aparecer em cada resposta. O texto deve ser escrito por um integrante do grupo,
com linguagem própria, sem usar IA para redigir.

## Regras

- Escrever de 1 a 3 frases por item.
- Usar palavras do grupo, não copiar a redação atual.
- Incluir todos os fatos obrigatórios do item.
- Não acrescentar informação que não esteja nos documentos.
- Manter a data de referência (`as_of`) de cada pergunta.
- Depois da reescrita, o assistente confere apenas a fidelidade factual e
  atualiza o JSON; não reescreve o texto por vocês.

## Itens a reescrever

### 1. `simple_medicamentos` — as_of 2026-06-10

Fatos obrigatórios:

- medicamentos vencidos não podem ser entregues em Ecoponto;
- destino: Farmácia Municipal EcoSaúde;
- endereço: Rua das Palmeiras, 77, Centro;
- atendimento: segunda a sexta, 08:00 às 17:00.

Fonte: `regulamento_descarte.md`, seção 6.

### 2. `simple_vila_verde` — as_of 2026-06-10

Fatos obrigatórios:

- local: Ecoponto Vila Verde;
- materiais: papel, papelão, vidro, plástico, metal e óleo de cozinha usado;
- horário: terça a sábado, 08:00 às 16:00.

Fonte: `lista_ecopontos.md`, tabela “Ecopontos em funcionamento”.

### 3. `simple_oleo` — as_of 2026-06-10

Fatos obrigatórios:

- óleo de cozinha usado;
- somente no Ecoponto Vila Verde;
- garrafa PET lacrada;
- máximo de 2 litros por entrega.

Fontes: `lista_ecopontos.md`, “Observações importantes”; e
`regulamento_descarte.md`, seção 5.

### 4. `simple_entulho` — as_of 2026-06-10

Fatos obrigatórios:

- entulho e resíduos de construção;
- somente no Ecoponto Industrial;
- limite de 2 metros cúbicos por mês;
- limite por domicílio.

Fontes: `lista_ecopontos.md`, “Observações importantes”; e
`regulamento_descarte.md`, seção 5.

### 5. `trap_parque_interdito_pilhas` — as_of 2026-04-20

Fatos obrigatórios:

- em 20/04/2026 o Parque das Acácias não aceita pilhas e baterias;
- motivo: interdição de 15/03/2026 a 31/05/2026, inclusive;
- durante a interdição o Parque não recebe nenhum material;
- alternativa para pilhas e baterias: Ecoponto Industrial.

Fontes: `comunicado_interdicao.md`, seções 1 e 2.

### 6. `trap_parque_pos_reabertura_pilhas` — as_of 2026-06-10

Fatos obrigatórios:

- em 10/06/2026 o Parque das Acácias não aceita pilhas e baterias;
- a mudança vale a partir de 01/06/2026;
- pilhas e baterias passam a ser recebidas exclusivamente no Ecoponto
  Industrial;
- a mudança é permanente.

Fonte: `comunicado_interdicao.md`, seção 3.

### 7. `trap_parque_interdito_eletronicos` — as_of 2026-04-20

Fatos obrigatórios:

- em 20/04/2026 não é possível entregar eletrônicos no Parque das Acácias;
- motivo: interdição de 15/03/2026 a 31/05/2026, inclusive;
- durante a interdição o Parque não recebe nenhum material;
- alternativa para eletrônicos: Ecoponto Industrial.

Fontes: `comunicado_interdicao.md`, seções 1 e 2.

### 8. `trap_parque_horario_pos_reabertura` — as_of 2026-06-10

Fatos obrigatórios:

- em 10/06/2026 o Parque das Acácias funciona de segunda a sexta, 08:00 às
  17:00, e no sábado, 08:00 às 12:00;
- esse horário vale a partir de 01/06/2026;
- ele substitui o horário anterior de segunda a sábado, 07:00 às 19:00.

Fontes: `comunicado_interdicao.md`, seção 3; e `lista_ecopontos.md`, tabela
“Ecopontos em funcionamento”.

## Registro de autoria

Preencher depois da reescrita, com quem escreveu cada item.

| Item | Integrante que escreveu | Data |
|---|---|---|
| `simple_medicamentos` | Victor Correia Binot | 18/11/2026 |
| `simple_vila_verde` | Victor Correia Binot | 18/11/2026 |
| `simple_oleo` | Victor Correia Binot | 18/11/2026 |
| `simple_entulho` | Victor Correia Binot | 18/11/2026 |
| `trap_parque_interdito_pilhas` | Victor Correia Binot | 18/11/2026 |
| `trap_parque_pos_reabertura_pilhas` | Victor Correia Binot | 18/11/2026 |
| `trap_parque_interdito_eletronicos` | Victor Correia Binot | 18/11/2026 |
| `trap_parque_horario_pos_reabertura` | Victor Correia Binot | 18/11/2026 |
