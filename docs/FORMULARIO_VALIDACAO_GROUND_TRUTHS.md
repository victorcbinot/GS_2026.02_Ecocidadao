# Formulário de validação humana dos ground truths

Este formulário serve para agilizar a conferência das oito respostas de
referência de `src/ecocidadao/evaluation/dataset.json` contra os documentos de
`base_documental/`.

## Como responder

Para cada item, marque **OK** se a resposta de referência estiver correta ou
**CORRIGIR** e escreva a correção. Não é necessário reescrever o texto se ele
estiver correto.

No final, informe:

- nome do revisor;
- RM;
- data da conferência.

Formulário preenchido por Victor Binot (RM 571499) em 18/11/2026. Os oito
itens foram conferidos e marcados como OK, sem correções.

---

## 1. `simple_medicamentos` — simples — referência: 2026-06-10

**Pergunta:** Onde uma pessoa deve descartar medicamentos vencidos e qual é o
horário de atendimento desse local?

**Ground truth atual:** Medicamentos vencidos não devem ser entregues em
Ecopontos. Eles devem ser levados à Farmácia Municipal EcoSaúde, na Rua das
Palmeiras, 77, Centro, que atende de segunda a sexta-feira, das 08:00 às 17:00.

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

**Ground truth atual:** O Ecoponto Vila Verde aceita papel, papelão, vidro,
plástico, metal e óleo de cozinha usado. Funciona de terça a sábado, das 08:00
às 16:00.

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

**Ground truth atual:** O óleo de cozinha usado deve ser entregue
exclusivamente no Ecoponto Vila Verde, em garrafa PET lacrada, com no máximo 2
litros por entrega.

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

**Ground truth atual:** Entulho e resíduos de construção devem ser entregues
somente no Ecoponto Industrial. O limite é de 2 metros cúbicos por mês por
domicílio.

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

**Ground truth atual:** Não. O Parque das Acácias está interditado de 15 de
março de 2026 a 31 de maio de 2026, inclusive, e não recebe nenhum material
nesse período. Em 20 de abril de 2026, pilhas e baterias devem ser levadas ao
Ecoponto Industrial.

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

**Ground truth atual:** Não. A partir de 1º de junho de 2026, o Parque das
Acácias deixa de aceitar pilhas e baterias. Elas passam a ser recebidas
exclusivamente no Ecoponto Industrial.

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

**Ground truth atual:** Não. Durante a interdição de 15 de março de 2026 a 31
de maio de 2026, o Parque das Acácias não recebe nenhum material. Em 20 de
abril de 2026, eletrônicos devem ser levados ao Ecoponto Industrial.

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

**Ground truth atual:** Em 10 de junho de 2026, o Parque das Acácias funciona
de segunda a sexta-feira, das 08:00 às 17:00, e no sábado, das 08:00 às 12:00.
Esse horário foi definido a partir de 1º de junho de 2026 e substitui o
horário anterior de segunda a sábado, das 07:00 às 19:00.

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

Nome do revisor: Victor Binot

RM: 571499

Data da conferência: 18/11/2026

Declaro que conferi os oito itens acima contra os documentos de
`base_documental/` e que as respostas marcadas como **OK** podem ser usadas
como ground truth na avaliação.

Assinatura: Victor Binot
