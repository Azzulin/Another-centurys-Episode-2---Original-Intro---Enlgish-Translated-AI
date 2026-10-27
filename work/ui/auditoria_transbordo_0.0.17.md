# Auditoria de transbordo de memória — 0.0.17 (2026-10-23)

ISO `work/output/ACE2-EN-0.0.17.iso` (SHA-256 `33fad6e5…2300a8d`). Leitura apenas. Os scripts ficaram no
scratchpad da sessão: `pointer_audit.py`, `widget_audit.py`, `final_audit.py` e `census_map.py`.

## 1. Estrutura dos recursos regravados: PASS

Independente do build e do `audit_iso`, comparando com a base:

- 247 contêineres de missão (com e sem diálogo):
  - mesma lista de campos de offset;
  - campo de tamanho igual ao tamanho real;
  - 4.015 seções que não são texto idênticas à base (4.225 palavras de offset mascaradas);
  - 990 tabelas lidas no novo endereço, todas terminando antes da seção seguinte (nenhuma sobreposição);
  - todos os offsets alinhados em 16 e dentro do contêiner.
- 216 pacotes de parceiro (108 VMD + 108 comprimidos): cadeia de pedaços intacta, e todo pedaço que não é texto
  idêntico à base.
- 296 binders internos: nenhuma folha que não seja texto mudou, fora os 40 blocos de glifo/atlas das fontes
  (pacotes de fonte idênticos aos da 0.0.16).

## 2. Memória residente (arena): sem risco

- Capturas do `crash_watch` (16/10, 21/10, 23/10): em missão, a arena nunca ficou com menos de ~2,9 MB livres. O
  menor valor geral (~2,45 MB) é da tela de preparação de saída.
- Na Op 04-01 (23/10), o jogo carrega o **42041**, com ~11,8 MB livres na arena.
- A 0.0.17 acrescenta no máximo +384 bytes a um contêiner em relação à 0.0.16 (6041/42041). O maior crescimento
  contra a base continua +800 (6010). Parceiros e pacotes de HUD não mudaram.

## 3. Texto × capacidade do widget

Capacidades medidas no jogo (censo do `crash_watch`, 274 textos):

| Capacidade | Onde |
|---|---|
| 16 | itens da pausa |
| 20 | títulos da pausa, legenda de marcadores |
| 32 | rótulos, nomes, objetivos, contadores, lista de missões, guias de botões |
| 80 | cartão de memória, linha de ajuda do rodapé (por exemplo "Select the unit operated by the player") |
| 128 | janela de mensagem, condições secretas |

O único transbordo que o vigia flagrou nas capturas é o já conhecido "Solar Facilities Destroyed：1 facilities"
(0.0.15).

Nada da lista abaixo é novo da 0.0.17: são textos que já estavam na 0.0.16. A 4-1, a 6907 e os nomes novos estão
dentro dos limites.

### Confirmado (texto visto no jogo num widget menor)

| Linha | Texto | Letras | Capacidade | Quando aparece |
|---|---|---|---|---|
| `menu3041` #0 (id 1) | "Checking Memory Card (PS2) in Slot 1. / Do not turn off power or remove/insert the card." | 85 | 80 | todo boot |
| `menu3041` #29 (id 48) | "Loading from Memory Card (PS2) in Slot 1. / …" | 89 | 80 | todo carregamento |

São 5 a 9 letras além da capacidade, ou seja, 560 a 1.584 bytes escritos depois do buffer. É o mesmo tamanho do
transbordo que travou a Op 11-1 (7 letras, 784 bytes).

### Quase certo (mesma família de mensagem ou mesmo widget medido)

| Linha | Texto | Letras | Capacidade | Motivo |
|---|---|---|---|---|
| `menu3041` #19 (id 29) | "Saving to Memory Card (PS2) in Slot 1. / …" | 86 | 80 | mesma mensagem "em andamento" de #0 e #29 (japonês 68–71) |
| `menu3041` #18 (id 28) | "Formatting Memory Card (PS2) in Memory Card / Slot 1. …" | 100 | 80 | idem |
| `menu3055` #25 | "Destroy the Infinite Mobile Cannon" | 34 | 32 | lista de missões da Free Mission (18 irmãs medidas em 32); Op 11-2 |
| `menu3055` #32 | "Destroy Submersible Combat Vessel" | 33 | 32 | idem; Op 14-3 |

As mesmas duas frases estão no briefing estratégico (`brief63010` #4, `brief63013` #5). A tela de briefing não
aparece no censo (outro caminho de desenho), então a lista de missões é a ocorrência de risco.

### Provável (linha de uma linha, japonês ≤ 32, inglês > 32, fora das tabelas que o validador cobre, sem medida)

O padrão é o mesmo do objetivo de 35 letras da 0.0.15. A regra `widget` do `validate.py` só cobre `m6###`, `hud*`
e `menu3056`.

- **Guias de botões** (só vistas em 32): `menu3013` #3 (48) e #4 (34); `menu3009` #0 (42) e #5 (34); `menu3065` #1
  (34); `menu3072` #1 (34).
- **Títulos de confirmação** (`㍉…`): `menu3013` #172 (34), #174 (34), #176 (33); `menu3040` #34 (33), #36 (34);
  `menu3065` #39 (38).
- **Listas de nome**: `menu3000` #39 "Dragonar-1 (Cavalier): Space Only" (33); `menu3000` #79 e `menu3025` #79
  "Aestivalis Artillery Frame Proto." (33); `menu3022` #13 e `menu3072` #78 "Another Century's Episode Original"
  (34); `menu3072` #75 "The Super Dimension Fortress Macross" (36); `menu3040` #45 e `menu3072` #37 "L-Gaim - Time
  For L-GAIM - (Ins.)" (33).
- **Opções**: `menu3071` #23, #27, #35 (34); `menu3072` #27 (34), #28 (37); `menu3040` #20 (33).
- **Briefing estratégico** (sem medida; caminho de desenho desconhecido):
  - títulos de operação: Op 08 "Assault on the Interception Limit" (33), Op 11 "Raid on the Giganos Secret
    Factory" (34), Op 15 "Battle of the UCE Air Defense Base" (34), Op 20 "Launch of the New Battleship Macross"
    (36), Op 24 "Air Defense Satellite Capture Operation" (39);
  - objetivo da Op 13: "Minimize Damage to Unidentified Units" (37).
- **Diversos**: `menu3001` #39 (35), `menu3065` #14 (42), #66 e #70 (45), #78 (35), `common` #0 (38), `m6285` #132
  (36).
- **Ajuda do rodapé** em `menu3013` e `menu3009` (33–46 letras): a mesma família de "Select the unit operated by
  the player", medida em **80**. Provavelmente seguras.

### Sem como avaliar sem medida

Painéis de texto longo (enciclopédia `menu3019`, cartas `menu3029`, ajuda de tela `menu3013` #98–#194, opções
`menu3065`, mensagens do cartão sem cartão/sem espaço `menu3041` #2, #4, #6, #11, #20). O japonês desses textos
chega a 300–640 letras, acima de qualquer capacidade conhecida da lista dos menus (42–255): o jogo deve dimensionar
esses widgets de outro jeito. Só o censo do `crash_watch` com essas telas abertas diz a capacidade.

## 4. Recomendação

1. Corrigir já os 6 "confirmado/quase certo":
   - `menu3041` #0, #18, #19, #29 para no máximo 80 letras, por exemplo "Checking Memory Card (PS2) in Slot 1.\nDo
     not remove it or turn off the power." (76);
   - `menu3055` #25 e #32 (e as cópias de briefing) para no máximo 32.
2. Estender a regra `widget` às tabelas `menu*` e `brief*` (linhas de uma linha sem tags, japonês ≤ 32) e encurtar
   o que ela acusar (~45 linhas).
3. No teste da 0.0.17, com `crash_watch.bat`, abrir: enciclopédia, cartas, a ajuda da preparação de saída, Options,
   o tocador de música (`menu3072`), a galeria (`menu3009`), e salvar com o cartão cheio ou sem cartão. O censo
   desses momentos fecha a última coluna.
