# Formulário de validação humana dos ground truths

Este formulário registra a reescrita e a conferência das oito respostas de
referência de `src/ecocidadao/evaluation/dataset.json` contra os documentos de
`base_documental/`.

## Como responder

Para cada item, marque **OK** se a resposta reescrita estiver correta ou
**CORRIGIR** e escreva a correção.

No final, informe:

- nome do revisor;
- RM;
- data da conferência.

Formulário preenchido por Victor Correia Binot (RM 571499) em 18/11/2026. Os
oito itens foram reescritos com palavras próprias, conferidos e marcados como
OK.

---

## 1. `simple_medicamentos` — simples — referência: 2026-06-10

**Pergunta:** Onde uma pessoa deve descartar medicamentos vencidos e qual é o
horário de atendimento desse local?

**Ground truth reescrito:** Medicamentos vencidos não devem ser descartados
nos Ecopontos. Eles devem ser entregues na Farmácia Municipal EcoSaúde,
localizada na Rua das Palmeiras, 77, no Centro, de segunda a sexta-feira, das
08h às 17h.

**Fonte para conferir:** `regulamento_descarte.md`, seção 6.

> Medicamentos vencidos, em desuso ou com embalagem danificada não devem ser
> entregues em nenhum Ecoponto. A destinação correta é a Farmácia Municipal
> EcoSaúde, na Rua das Palmeiras, 77, Centro, de segunda a sexta-feira, das
> 08:00 às 17:00.

**Resposta:** [x] OK  [ ] CORRIGIR

Correção, se houver: ______________________________________________________

---

## 2. `simple_vila_verde` — simples — referência: 2026-06-10

**Pergunta:** Quais materiais são aceitos no Ecoponto Vila Verde e qual é o
horário de funcionamento?

**Ground truth reescrito:** O Ecoponto Vila Verde recebe papel, papelão,
vidro, plástico, metal e óleo de cozinha usado. O local funciona de terça-feira
a sábado, das 08h às 16h.

**Fonte para conferir:** `lista_ecopontos.md`, tabela “Ecopontos em
funcionamento”.

> Vila Verde | Rua dos Ipês, 45, Vila Verde | terça a sábado, 08:00 às 16:00 |
> papel, papelão, vidro, plástico, metal e óleo de cozinha usado

**Resposta:** [x] OK  [ ] CORRIGIR

Correção, se houver: ______________________________________________________

---

## 3. `simple_oleo` — simples — referência: 2026-06-10

**Pergunta:** Onde entregar óleo de cozinha usado e qual é o limite máximo por
entrega?

**Ground truth reescrito:** O óleo de cozinha usado deve ser entregue no
Ecoponto Vila Verde, dentro de uma garrafa PET bem fechada. Cada entrega pode
ter no máximo 2 litros de óleo.

**Fontes para conferir:** `lista_ecopontos.md`, “Observações importantes”; e
`regulamento_descarte.md`, seção 5.

> Óleo de cozinha usado deve ser entregue em garrafa PET lacrada, com no máximo
> 2 litros por entrega, exclusivamente no Ecoponto Vila Verde.

> Óleo de cozinha é limitado a 2 litros por entrega.

**Resposta:** [x] OK  [ ] CORRIGIR

Correção, se houver: ______________________________________________________

---

## 4. `simple_entulho` — simples — referência: 2026-06-10

**Pergunta:** Onde entregar entulho e resíduos de construção e qual é o limite
mensal por domicílio?

**Ground truth reescrito:** O descarte de entulho e resíduos de construção deve
ser feito exclusivamente no Ecoponto Industrial. O limite permitido é de 2
metros cúbicos por mês para cada domicílio.

**Fontes para conferir:** `lista_ecopontos.md`, “Observações importantes”; e
`regulamento_descarte.md`, seção 5.

> Resíduos de construção são limitados a 2 metros cúbicos por mês e somente no
> Ecoponto Industrial.

> Para resíduos de construção, o limite é de 2 metros cúbicos por mês por
> domicílio.

**Resposta:** [x] OK  [ ] CORRIGIR

Correção, se houver: ______________________________________________________

---

## 5. `trap_parque_interdito_pilhas` — armadilha — referência: 2026-04-20

**Pergunta:** Em 20 de abril de 2026, o Parque das Acácias aceita pilhas e
baterias? Se não, para onde esse material deve ser levado nessa data?

**Ground truth reescrito:** Em 20/04/2026, o Ecoponto Parque das Acácias está
interditado e não recebe nenhum tipo de material. A interdição ocorre de
15/03/2026 até 31/05/2026, inclusive. Durante esse período, pilhas e baterias
devem ser entregues no Ecoponto Industrial.

**Fontes para conferir:** `comunicado_interdicao.md`, seções 1 e 2.

> A interdição começa em 15 de março de 2026 e termina em 31 de maio de 2026,
> inclusive. Durante esse período, o Ecoponto Parque das Acácias não receberá
> nenhum material.

> Pilhas e baterias | Ecoponto Industrial

**Resposta:** [x] OK  [ ] CORRIGIR

Correção, se houver: ______________________________________________________

---

## 6. `trap_parque_pos_reabertura_pilhas` — armadilha — referência: 2026-06-10

**Pergunta:** Em 10 de junho de 2026, o Parque das Acácias aceita pilhas e
baterias? Se não, onde descartá-las?

**Ground truth reescrito:** Em 10/06/2026, o Ecoponto Parque das Acácias já
está reaberto, mas não recebe pilhas e baterias. Desde 01/06/2026, esses
materiais são aceitos exclusivamente no Ecoponto Industrial, e essa mudança é
permanente.

**Fonte para conferir:** `comunicado_interdicao.md`, seção 3.

> o ponto deixa de aceitar pilhas e baterias;
> pilhas e baterias passam a ser recebidas exclusivamente no Ecoponto
> Industrial;
> Essas alterações são permanentes e não se limitam ao período de obras.

**Resposta:** [x] OK  [ ] CORRIGIR

Correção, se houver: ______________________________________________________

---

## 7. `trap_parque_interdito_eletronicos` — armadilha — referência: 2026-04-20

**Pergunta:** Em 20 de abril de 2026, é possível entregar eletrônicos no
Parque das Acácias? Qual é a alternativa?

**Ground truth reescrito:** Em 20/04/2026, não é possível entregar eletrônicos
no Ecoponto Parque das Acácias, pois o local está interditado de 15/03/2026 a
31/05/2026, inclusive, sem receber nenhum material durante esse período. A
alternativa para o descarte de eletrônicos é o Ecoponto Industrial.

**Fonte para conferir:** `comunicado_interdicao.md`, seções 1 e 2.

> Durante esse período, o Ecoponto Parque das Acácias não receberá nenhum
> material.

> Eletrônicos | Ecoponto Industrial

**Resposta:** [x] OK  [ ] CORRIGIR

Correção, se houver: ______________________________________________________

---

## 8. `trap_parque_horario_pos_reabertura` — armadilha — referência: 2026-06-10

**Pergunta:** Qual é o horário de funcionamento do Parque das Acácias em 10 de
junho de 2026?

**Ground truth reescrito:** Em 10/06/2026, o Ecoponto Parque das Acácias
funciona de segunda a sexta-feira, das 08h às 17h, e aos sábados, das 08h às
12h. Esse horário começou a valer em 01/06/2026 e substituiu o horário
anterior, que era de segunda a sábado, das 07h às 19h.

**Fontes para conferir:** `comunicado_interdicao.md`, seção 3; e
`lista_ecopontos.md`, tabela “Ecopontos em funcionamento”.

> novo horário: segunda a sexta-feira, das 08:00 às 17:00; sábado, das 08:00
> às 12:00;

> Parque das Acácias | Avenida das Acácias, 850, Jardim das Acácias | segunda a
> sábado, 07:00 às 19:00

**Resposta:** [x] OK  [ ] CORRIGIR

Correção, se houver: ______________________________________________________

---

## Registro final

Nome do autor e revisor: Victor Correia Binot

RM: 571499

Data da reescrita e conferência: 18/11/2026

Declaro que reescrevi os oito itens acima com palavras próprias e conferi
contra os documentos de `base_documental/`, e que as respostas marcadas como
**OK** podem ser usadas como ground truth na avaliação.

Assinatura: Victor Correia Binot
