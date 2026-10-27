# Estudo e pipeline: tradução de Another Century's Episode 2 (ACE2)

> **Estado (2026-10-08):**
> - A 0.0.1 foi testada no PCSX2 (fontes, falas e cenas OK).
> - As builds 0.0.2 a 0.0.7 foram geradas e auditadas, **mas ainda não foram testadas no jogo**.
> - A 0.0.7 tem as Operações 01 a 21 e o HUD completos.
> - Op 22 revisada, à espera de 2 consertos estruturais do agente. Ops 23–28 e os 57 lotes fora das operações
>   (missões extras, tutorial, flashbacks, menus) estão com o agente.
> - **Estado atual e próximos passos: seção 8.**
> - O código está em `tools/ace2/`. Use sempre `.venv\Scripts\python.exe` (Pillow, numpy e pycdlib instalados).

**Alvo da tradução:** inglês, em ASCII de 1 byte (CP932), como no ACE1 e no ACE3.

**Discos**

| Uso | Imagem | Executável | `DATA.BIN` |
|---|---|---|---|
| **Base** de todo build | `Another Century's Episode 2 - Special Vocal Version (Japan).iso` | `SLPS_258.29` | 1.315.378.208 bytes, 5.867 recursos |
| Só a abertura | `Another Century's Episode 2 (Japan).iso` (2006) | `SLPS_256.23` | — |
| Referência do que **não** fazer | `... (English Patched).iso` (projeto anterior) | — | — |

Da ISO original de 2006 usamos apenas o `MOVIE001.PSS`, a abertura com "Glorious". Ele tem exatamente o mesmo tamanho
do arquivo da SVV (275.251.204 bytes), então a troca é de arquivo inteiro.

## 1. Por que recomeçar (resumo da auditoria do patch anterior)

O patch anterior (`D:\Projeto Crise de Meia Idade 2`) só alterou o `DATA.BIN` e o `MOVIE001.PSS`. O
`tools/ace2/audit_iso.py` aponta nele os seguintes problemas:

- **Fontes nunca foram completadas.** O texto foi escrito em maiúsculas *fullwidth* (2 bytes por letra), sem
  apóstrofo nem vírgula.
- **Gravação in-place, com o tamanho japonês.** O texto não coube, e o resultado foi:
  - 160 tabelas que não se leem mais;
  - nas tabelas de briefing, ponteiros para fora do recurso;
  - o recurso 63000 movido para cima do 64954 (uma textura).
- **2.097 linhas com códigos de controle alterados** (`<ab()>`, `<ed()>`, `<op()>`, `%d％`→`%d%%`), que são fortes
  candidatos aos travamentos.
- **Diálogos escritos à mão em scripts e aplicados em linhas e missões erradas.** O extrator antigo numerava os
  recursos pela posição no índice, e não pelo ID (os IDs do `DATA.BIN` têm buracos), por isso os textos dele estão
  deslocados.

Por isso os JSONs de `D:\Projeto Crise de Meia Idade 2\extracted_text` **não** são usados. A extração foi refeita do
zero (seção 4).

## 2. Formatos

Os parsers do ACE1 (que vieram do ACE3, MIT) funcionam no ACE2 sem mudança. Só o índice do `DATA.BIN` é diferente.

| Item | Formato no ACE2 |
|---|---|
| `DATA.BIN` | `BND\0 fff70000`, cabeçalho de 36 bytes: +12 tamanho total, +16 contagem, +24 `0x30800` (mantido). Entradas `(id, offset, size)` de 12 bytes. IDs crescentes **com buracos**, payloads alinhados em 2048, sem nomes. |
| BND interno | `BND\0`, pares `(id, offset)`, payloads alinhados em 32 (igual ao ACE1) |
| LZSS | O do ACE3 (`00 01 00 00` + tamanho BE). Há falsos positivos de assinatura, tratados por `try_unpack`. |
| Tabela de texto | magic `0x10000`, ranges, ponteiros, pool CP932 (igual ao ACE1) |
| Contêiner de missão | `00 01 00 00`; +8..+12: registros `(id, offset)` de 16 bytes das subtabelas (nomes inimigos); +20: tabela de diálogo |
| Fonte | Mapa `00 00 01 00` (altura em +8, registros de 24 bytes) + atlas TIM2 de 4 bpp (PSMT4, linear ou PSMCT32 swizzled) |

O executável abre o `DATA.BIN` **pelo nome** (`\DATA.BIN;1`). Por isso o `DATA.BIN` pode crescer: os arquivos seguintes
são deslocados para a cauda vazia do disco (~20 MB livres), e os registros ISO9660 e UDF são reescritos.

### 2.1 Onde está o texto

O mapa completo é gerado por `export_text.py` em `work/translation/inventory.json`.

| Conteúdo | Recursos | Linhas (únicas por tabela) |
|---|---|---|
| Diálogo das missões | `6005–6998` e gêmeos `42xxx` (os pares têm as **mesmas** linhas de texto) | 6.583 em 106 tabelas |
| Nomes inimigos (mira do HUD) | subtabelas de 1 linha dentro dos contêineres de missão | 89 |
| Briefings | `63000–63300` | 1.588 em 168 tabelas |
| Menus, enciclopédia, logs | pacotes `62050–62057` (inner `3000–3077`), cópias em `5000`, `120` | 2.171 em 44 tabelas |
| HUD de gameplay | pacotes `38000–38006` (inner `3013`, `3020`, `3021`) | 256 |
| Janelas do sistema | `8031` (+ cópias em `8033`, `60000`) | 8 |

Ainda não mapeados: texto desenhado em texturas (título, menus), legendas de filme e as CSVs `102–106`, que parecem
ser listas de desenvolvimento.

### 2.2 Códigos de controle

São preservados na mesma ordem (`validate.py`):

- tags: `<sp()> <ab()> <op()> <ed()> <on()> <off()> <im()> <fz()> <tr()> <of()> <cs()> <ac()>`;
- cores: `#c[RRGGBB]…#c`;
- variáveis: `%d`, `%s`, `%%`;
- ícones de botão e de unidade, que são glifos da fonte: `○ × △ □ ㊤ ㊦ ㊧ ㊨ ① … ⑳ ㍉ ㌢ ㌔ ㍍`.

O `％` fullwidth depois de `%d` é **literal**. Trocá-lo por `%%` muda a semântica do `printf` (erro do patch anterior).

## 3. Fontes

Há 4 fontes distintas em 13 pacotes, e todas as cópias recebem o patch.

| Fonte | Onde | Atlas | Altura | Estilo | ASCII nativo | TTF escolhida pela calibração |
|---|---|---|---|---|---|---|
| 2500/2000 | gameplay `38000/1/4/5/6` | 1024×512 | 19 | **Mincho (serifa)** | `% 0-9 M k` | Times (0,230; Georgia 0,237; Century 0,250; góticas ≥ 0,42) |
| 2500/2000 | gameplay `38002/3` | 512×512 | 21 | Mincho | parcial | Times |
| 2500/2000 | menus `62050–62054`, `62057` | 1024×512 | 19 | Mincho | parcial | Georgia |
| 2501/2001 | gameplay `38000–38006` (HUD) | 256×256 | 16 | Gótica | **alfabeto completo** | Yu Gothic Regular |

O `tools/ace2/fonts.py` foi adaptado do ACE1. As diferenças são:

- **Cobertura pela luminância.** A suavização está no cinza da paleta (32…~180); todas as cores têm alpha 128.
- **Contorno de 1 px.** Todo glifo nativo tem um contorno escuro em 4 direções, e os gerados recebem o mesmo.
- **Calibração por comparação de pixels.** A TTF é escolhida comparando várias letras nativas com 9 candidatas; o
  tamanho é dado pela altura do `H`.
- **Busca de espaço precisa.** O atlas de gameplay está quase cheio. A célula nova pode se sobrepor à parte
  transparente de outra, mas tinta nunca cai em célula alheia.
- **Guarda decidida pelos dados.** As fontes 2500 nativas já têm tinta encostada em células vizinhas (457 casos), então
  o jogo amostra por ponto e a guarda é 0. A 2501 não tem, e recebe 1 px.
- **Glifos novos sem margem extra.** O contorno separa as letras; largura = avanço, como nos nativos.

O que não muda: nenhum glifo, registro ou pixel original é alterado (verificado byte a byte no fim). Na fonte de
21 px, o `@` não coube e é reportado como `skipped`. Provas visuais em `work/proof/font_*.png`.

## 4. Ferramentas (`tools/ace2/`)

| Script | Função |
|---|---|
| `ace2lib.py` | Formatos: ISO9660, índice do `DATA.BIN`, BND interno, LZSS, tabela de texto, missão |
| `disc.py` | Gravador de disco: crescimento do `DATA.BIN`, deslocamento, ISO9660 + UDF, troca de arquivo inteiro, verificação |
| `textdb.py` | Descobre **todas** as tabelas do disco (sem lista fixa), agrupa cópias e grava de volta. Nada é espremido: nos contêineres de missão, cada tabela é reconstruída com o tamanho que precisar no lugar da japonesa, e as seções seguintes andam (`ace2lib.mission_relayout`; até a 0.0.10 a tabela era anexada no fim, ver 8.6 item 0). |
| `export_text.py` | Exporta o japonês para `work/translation/en/<tabela>.json` (chave = texto japonês; preserva o `en` existente) |
| `validate.py` | Regras por linha: tokens, CP932, sem fullwidth, sem japonês, quebras de linha, janela de mensagem (127 bytes visíveis), widget de 32 letras; `check_counters` (contador do HUD: rótulo + 1 + valor ≤ 32) |
| `merge_fill.py` | Mescla `_fill/<tabela>.json` (`{índice: inglês}`), valida e mede a largura em px com a fonte completada |
| `batches.py` | Lotes de 80 linhas para o tradutor externo em `work/translation/agent/`: `make` (operações; `--extras` = texto fora delas), `hand` (registra a entrega e congela o grupo), `status` |
| `check_fixes.py` | Testa propostas de correção do revisor (`{lote: {ref: inglês}}`) com as regras do validador, sem gravar nada |
| `validate_return.py` | Valida a entrega do tradutor (`validation/<LOTE>.md`, APROVADO/REJEITADO) e, com `--apply`, grava em `_fill/` |
| `agent_docs.py` | Gera `agent/GLOSSARIO.md` (nomes e termos que existem no texto, por série, com gênero e papel) |
| `review_returns.py` | Revisão de sentido: JP/EN lado a lado com sinais de suspeita (`review/<LOTE>.md`) |
| `rewrap.py` | Requebra linhas para caber numa largura (só layout; nunca troca palavras) |
| `fonts.py`, `font_proof.py` | Completa as fontes e gera provas visuais |
| `exe.py` | Os únicos patches do executável `SLPS_258.29` (fronteira pilha/heap +256 KB; janela de mensagem 60 → 128 letras); sozinho, lista os patches conferidos contra o disco base |
| `build.py` | `--version X` (ensaio) / `--write` → `work/output/ACE2-EN-X.iso` + relatório JSON; `--svv-opening` mantém a abertura da SVV |
| `audit_iso.py` | Auditoria independente de uma ISO pronta (é o que reprova o patch anterior); confere também o executável e a memória das missões; `--svv-opening` para a build feita assim |
| `swap_movie.py` | Troca o `MOVIE001.PSS` de uma imagem pelo de outra, no mesmo lugar (só biblioteca padrão; é a ferramenta dos jogadores para o "Glorious") |
| `make_patch.py` | Patch de release: xdelta da SVV intacta → build com a abertura da SVV recolocada, conferência e `work/release/ACE2-EN-X-SHA256.txt` |
| `test_identity.py` | Toda reconstrução sem edição reproduz os bytes (índice, 528 binders, 754 LZSS, as tabelas, inclusive as 460 dos pacotes de parceiro, e os 201 contêineres pelo relayout) |
| `test_disc.py` | Disco idêntico sem edições (SHA igual) + disco com crescimento e troca do filme |
| `test_textdb.py` | Estresse: tradução sintética 1,5x nos 1.394 locais de texto, sem bytes mortos nos contêineres; cabe no disco |

**Fluxo:** `export_text.py` → tradução em `_fill/` → `merge_fill.py` → `build.py --write` → `audit_iso.py` → PCSX2.

**Fluxo com o tradutor externo (igual ao ACE1):** `glossary.py --write` → `agent_docs.py` → `batches.py make` → o agente grava só `agent/returns/<LOTE>.json` →
`validate_return.py <LOTE>` → `review_returns.py <LOTE>` + correções em `agent/reviewer_fixes.json` →
`validate_return.py <LOTE> --apply` → `fix_names.py` → `merge_fill.py` → `build.py` → `audit_iso.py`.

## 5. Build 0.0.1 (prova de conceito)

Conteúdo:

- fontes completadas nos 13 pacotes;
- `common` (janelas do sistema);
- `brief63000` (briefing da Operação 01);
- `m6011` (Operação 01-1: tutorial e simulação Tack × Marina);
- o nome "Gun Ark";
- abertura com "Glorious".

Os briefings foram deixados **de propósito** com 3 linhas de até ~470 px, para medir a caixa real. O maior japonês da
tabela tem 316 px. As falas de missão foram ajustadas para caber em ~364 px, que é a linha japonesa mais larga.

**O que verificar no PCSX2** (boot limpo; *save states* guardam a fonte antiga):

1. A abertura toca "Glorious".
2. O briefing da Operação 01 está em inglês. Onde a caixa corta as linhas largas?
3. Na missão 01-1, as falas de rádio e de cena aparecem com minúsculas, sem `?` nem letras faltando. Há travamento
   em alguma cena?
4. A mira mostra "Gun Ark" no adversário da simulação.
5. A janela de reiniciar missão (menu de pausa) está em inglês.

## 6. Riscos e pontos abertos

- **Tamanho real das caixas** (diálogo, briefing, menus). Ainda só usamos a linha japonesa mais larga como estimativa.
- **Contêiner de missão maior.** O jogo carrega o contêiner inteiro; se usar um buffer fixo, o crescimento (+~3 KB por
  missão) pode estourar. O ACE3 fez o mesmo sem problema. É a primeira coisa a observar no teste.
- **Fonte de 21 px (`38002/3`).** Ainda não se sabe que tela a usa.
- **HUD (2501).** As letras nativas têm espaçamento largo, que é o original.
- **Patentes (decidido na 0.0.2, pela Gundam Wiki):** 少尉 = Ensign, 中尉 = Lieutenant (Lt.), 大尉 = Captain (Capt.),
  少佐 = Major, 准将 = Commodore. A grafia é aplicada por `fix_names.py` e está em `work/glossary/terms.json`.

## 7. Operações, nomes e larguras (desde a 0.0.2)

- **Uma operação é sempre traduzida inteira.**
  - O `operations.py` gera `work/translation/operations.json` com todas as camadas de cada uma das 28 operações:
    estratégico, **táticos por fase**, missões, debriefing e relatórios.
  - A numeração foi conferida pelos cabeçalhos; todas as 168 tabelas de briefing ficaram atribuídas.
  - Os lotes de tradução partem desse mapa: `batches.py make` gera `work/translation/agent/batches/opNN_KK.json`
    (80 linhas, na ordem de jogo). Ver `agent/PLANO.md` e o fluxo na seção 4.
- **Linhas por janela:** fala de missão até 2, briefing até 3 (o máximo do japonês em todo o jogo; a Op 01, testada,
  também não passa disso). Texto que não é fala mantém as linhas do japonês.
- **Nomes:**
  - `hud3021` tem os rótulos curtos de quem fala nas missões; `menu3014` tem os nomes completos de quem fala nos
    briefings; `unit_names` tem a mira.
  - Nos briefings, `<op(N,1)>` é um índice de retrato, não o ID da 3014. Os 19 índices estão identificados em
    `work/glossary/portraits.json` (43, 46 e 55 com confiança média).
  - Nas missões não há rótulo de quem fala no texto. `<op()>` abre uma janela nova; uma linha sem `<op()>` continua
    a fala anterior.
  - O `glossary.py` funde `decisions.json` > ACE3 > `research/*.json` e gera os preenchimentos.
  - O `fix_names.py` aplica `name_fixes.json` a todo o texto já traduzido, com ensaio por padrão.
- **"？？？？？？"** (menu3010, id 10) é original: marca fases bloqueadas. "WARNING" é textura.
- **Larguras:** `work/ui/limits.json` (briefing 430 px medido; falas 380 px provisório). Os demais tipos usam a maior
  linha japonesa da tabela.

## 8. Estado atual e próximos passos (atualizado em 2026-10-08, fim do dia)

Esta seção é a passagem de bastão entre sessões. Comece por ela e pelo topo do `docs/CHANGELOG.md`. Numa máquina
nova, monte o ambiente antes com `docs/RETOMADA.md`.

### 8.1 Onde estamos

| Item | Estado |
|---|---|
| Builds | 0.0.1 e 0.0.9 testadas no PCSX2. **0.0.9** = todo o texto das tabelas; no teste (09/10) rótulos de menu sumiram e o jogo travou ao pausar na missão. **0.0.10** = correção desses rótulos e do menu de pausa; no teste (10/10) travou na Op 12-1 por falta de memória. **0.0.11** = contêineres sem tabela morta (8.6 item 0). **0.0.13** = janela de mensagem 60 → 128 letras; no teste (10/10) as cutscenes não travaram e o gameplay ficou estável. **0.0.14** = falas dos parceiros em inglês (8.6 item 0c); no teste (16/10) travou na Op 11-1. **0.0.15** = 27 linhas em até 32 letras + regra `widget` no validador; travou no mesmo ponto (16/10). A captura mostrou que o contador do HUD junta rótulo + "：" + valor num widget de 32 (39 letras). **0.0.16** = contadores e `menu3056` dentro de 32 + `check_counters`; no teste (23/10) a Op 04-01 estava inteira em japonês. **0.0.17** = Op 04-01 (6041/42041) e 6907 descobertas e traduzidas, nomes de alvo de todos os contêineres (lista A pelo contador de +28, contêineres sem diálogo), ainda não testada. |
| Parceiros (`xp`) | **6.138/6.138** linhas (2.657 frases únicas) traduzidas pelo Claude, validadas e aplicadas na 0.0.14. |
| Campanha (Ops 01–28) | **6.822/6.822** linhas traduzidas, validadas, revisadas linha a linha e aplicadas. Correções do revisor: Op 02 30; Ops 03–08 56; Ops 09–22 350; Ops 23–24 67; Op 25 204; Ops 26–28 94. |
| Fora das operações | **Aplicados** os 57 lotes: `xa` 457 linhas (76 correções), `xb` 628 e `xd` 142 (107), `xc` 122 + menus 3000–3018 (92), enciclopédia/menus 3019–3029 (121, enciclopédia e cartas retraduzidas), menus 3032–3057 (110), 3061–3077 (121). Menus 2.171/2.171. |
| HUD, nomes, `common` | Completos (HUD 256/256, `unit_names` 120/120 desde a 0.0.17, rótulos de quem fala 118/118, nomes completos 83/83). Falta a segunda tabela dos contêineres (`+24`, nomes de objeto/alvo): 8.6 item 0d. |
| Fora das tabelas | Levantamento feito em 08/10 (8.8): poucas texturas com japonês, o título do save no executável, filmes não conferidos. Nada disso tem lote ainda. |
| Quarentena | `agent/_quarentena_google_0.0.3/` (aplicação do agente em 06/10) e `_quarentena_google_0.0.8/` (script `apply_op23_02.ps1` que ele deixou em `agent/`). Só registro. |

### 8.2 Arquivos que importam

| Arquivo | Para quê |
|---|---|
| `work/translation/agent/PLANO.md`, `PROMPT_AGENTE.md`, `INDICE.md`, `GLOSSARIO.md`, `LOTES.md`, `examples/op01.json` | Pacote do tradutor externo. |
| `work/translation/agent/batches/` | Lotes (`opNN_KK`, `xa_KK`, `xm_menuNNNN_KK`). Não editar à mão; gerados por `batches.py`. |
| `work/translation/agent/returns/` | Entregas do agente. **Nunca editar.** |
| `work/translation/agent/reviewer_fixes.json` | Todas as correções do revisor (`{lote: {ref: inglês}}`). |
| `work/translation/agent/validation/`, `review/` | Relatório do validador e página de revisão JP/EN por lote. |
| `work/translation/agent/handed.json`, `applied.json` | Lotes entregues ao agente (congelam a operação/grupo) e lotes aplicados. |
| `work/translation/auto/<grupo>.json`, `auto/overrides.json` | Linhas preenchidas automaticamente (`tm`/`repeat`) e as exceções com inglês próprio. |
| `work/translation/agent/width_waivers.json` | Dispensas de largura provisória de menu, com o motivo (hoje só `menu3077#54`). Conferir cada uma no jogo. |
| `work/ui/wide_0.0.9.txt` | Linhas mais largas que a maior linha japonesa da tabela (142, quase todas em `menu3055`/`3056`). Roteiro de teste. |
| `work/glossary/` | `names.json` (gerado), `decisions.json`, `terms.json`, `portraits.json`, `name_fixes.json`, `research/*.json`. |

### 8.3 Ciclo de um lote (receita)

Rode tudo com `.venv\Scripts\python.exe tools\ace2\<script>`.

1. **Entregar:** o prompt para o agente sai de `agent/PROMPT_AGENTE.md`. Registre os lotes com
   `batches.py hand <LOTE> ...` para congelá-los.
2. **Conferir a pasta:** ao receber, verifique que nada mudou fora de `agent/returns/` (o agente já aplicou sozinho,
   alterou ferramentas, regenerou arquivos e reescreveu o japonês).
3. **Validar:** `validate_return.py --all` gera `agent/validation/<LOTE>.md`.
   - Erros estruturais (linha a mais/a menos, `jp`/`phase` alterado, JSON inválido) **voltam ao agente**.
   - Erros de largura, caractere ou glossário podem ser corrigidos aqui, junto com a revisão.
4. **Revisar o sentido:** `review_returns.py <LOTE> ...` gera `agent/review/<LOTE>.md`. Leia todas as linhas.
   - Para levas grandes, use revisores em paralelo (subagentes, um bloco de operações cada). Eles gravam propostas
     num arquivo à parte (`{lote: {ref: inglês}}`) e testam com `check_fixes.py <arquivo>`, que não grava nada.
     O Claude lê **cada** proposta antes de aceitar. O prompt dos revisores está em `docs/REVISAO_PARALELA.md`;
     a lista de erros típicos está em 8.4.
5. **Juntar as correções** a `reviewer_fixes.json` e revalidar até APROVADO.
6. **Aplicar:** `validate_return.py <LOTE> --apply`, sempre a **operação inteira** (todos os lotes). Depois confira
   se a operação ficou 100% preenchida. No fim de uma leva, `validate_return.py --auto` (linhas automáticas de
   todos os grupos).
7. **Build:** `fix_names.py` → `merge_fill.py` → `build.py --version 0.0.N --write` →
   `audit_iso.py work/output/ACE2-EN-0.0.N.iso` → CHANGELOG → teste no PCSX2.
8. **Glossário:** propostas do agente com fonte vão para `research/agent_proposals.json`; depois `glossary.py --write`,
   `agent_docs.py` e `batches.py make` (que nunca reescreve grupos congelados).

### 8.4 Erros típicos do agente (o que a revisão procura)

- Hipóteses viradas em fato: らしい, ようだ, であろう, 推測される, 可能性, とのこと.
- Insultos e palavras inventados: "bastards", "scum", "fools", "half-breed", "runts", "noble sacrifice".
- Orações perdidas (軍務に復帰, 軍属, 建造中, 人質をとって, すでに, 少しずつ) e termos errados (犯行声明 = claim of
  responsibility; 宙域 ≠ airspace; 誤射 ≠ misfire; 戦略的 = strategic).
- Gênero: "he"/"that guy" para quem o texto ainda não identificou (a piloto do Buster Ark, operadores).
- Voz: falas duras sem contração para personagens casuais; "-chan"/"-san" em romaji.
- Frases divididas em duas linhas fechadas cedo, ou continuadas com maiúscula; objetivos de duas linhas tratados
  como dois.
- Nomes: "Amuro Rei" (é Ray), "Sho" (é Show), "Martian Successor" no lugar do nome da nave.
- `%` ASCII solto (use `％`), `;` e `~` (faltam nas fontes), espaços ASCII nas assinaturas de relatório.

### 8.5 Regras aprendidas (não regredir)

- **O agente externo só traduz.** Tudo fora de `agent/returns/` é nosso. Ele não obedece um "pare": cada arquivo de
  `returns/` é uma entrega independente.
- **Linhas por janela:** missão 2 linhas, 380 px (provisório); briefing e relatório 3 linhas, 430 px (medido); texto
  que não é fala mantém as linhas do japonês. Menus: limite = maior linha japonesa da tela (provisório, ver 8.7).
- **Rótulo de menu (botão da lista e célula de opção) acima de ~141 px não é desenhado** (teste da 0.0.9: 141 px
  aparece, 154 px some). O limite é por widget, não por tabela: textos de ajuda e títulos são mais largos. Está em
  `work/ui/limits.json` (`menu_label`). Ver o roteiro em 8.6.
- **`merge_fill.py` e o build com `PYTHONIOENCODING=utf-8`** no Windows; sem isso o merge para no "①" e deixa
  tabelas sem mesclar.
- **Glossário:** personagens do ACE3 de séries fora do ACE2 ficam de fora (`NOT_IN_ACE2`); toda busca respeita o
  limite da palavra em katakana e ignora um nome dentro de um nome mais longo (`longer_keys`: レイ em アムロ・レイ);
  grafias sem ponto entram como entradas próprias.
- **Prioridade dos nomes:** decisões > ACE3 > pesquisa.
- **Lotes congelados:** `batches.py make` nunca reescreve uma operação ou grupo entregue (`started()`).
- **`％` largo, nunca `%` solto** (o validador barra). Linhas automáticas que ficam erradas no contexto (metade de
  objetivo dividido) recebem inglês próprio em `auto/overrides.json`.
- **Retratos:** os 19 `<op(N,1)>` estão em `portraits.json`.
- **Depois de aplicar lotes, `validate_return.py --auto`**: reaplica as linhas automáticas de todos os grupos (grupos
  sem lote, como `menu3023`/`menu3074`, e cópias de linhas preenchidas depois).
- **Uma linha reescrita pelo revisor** ignora campos congelados alterados na entrega (aviso, não erro). Linhas
  acrescentadas, removidas ou reordenadas continuam bloqueando.
- **O validador só confere nomes por pedaço** (qualquer palavra de 4+ letras do nome oficial): "Will Wips", "Golaon",
  "Quincy Isser", "Wingel Binder" passaram. A revisão de sentido tem de conferir a grafia inteira.
- **Botões nos menus:** `決定` = "OK"; separadores com o espaço largo `　` onde o japonês tem; rótulo seguido de valor
  (`難易度：　`) termina em `:　`.
- **Reconhecimento de contêiner de missão** (0.0.17; a Op 04-01 ficou em japonês até a 0.0.16 por causa disso):
  - `00 01 00 00` com `+8` = 0 é tanto LZSS quanto contêiner com lista A vazia; `is_packed` decide pelo tamanho
    declarado (≤ 8× o recurso);
  - a lista A é lida pelo contador do byte +28, nunca até +12;
  - há contêiner sem diálogo (`+20` = 0) e com `+4` = 0.
  - Depois de mudar a descoberta, compare a contagem de locais do `export_text` antes e depois.
  - Fills indexados pela posição (`_fill/unit_names.json`) precisam ser remapeados pelo japonês quando a exportação
    insere linhas.
- **Memória das missões:** o jogo carrega tudo de uma missão numa única arena (`0x003afe00..0x01cfff00`) sem folga.
  Pedido que não cabe volta NULL e o jogo não confere. Nenhum recurso residente na missão pode carregar bytes mortos.
  Contêiner de missão cresce só o que as suas tabelas crescem (`audit_iso.py` confere) e toda mudança de tamanho em
  recurso de missão (contêineres, pacotes de HUD 38000–38006) entra no CHANGELOG com o número.
- **Letras por widget de texto:** cada widget reserva espaço para um número fixo de letras e o jogo não confere
  (texto maior escreve por cima do vizinho e trava depois). Espaços contam, quebras de linha não.
  - Janela de mensagem: 128 a partir da 0.0.13 (era 60), e no máximo 127 bytes visíveis por linha (`validate.py`).
  - **Capacidade padrão: 32** (init `0x289dfc`) para todo widget cujo dono não define outra, nas duas classes
    (buffer (7n + 11) × 16 e (11n + 12) × 16 + 32). Isso inclui objetivos, contadores, rótulos, nomes, condições da
    MISSION INFORMATION e a linha de ajuda da pausa. Está no `validate.py` (regra `widget`, para as tabelas `m6###` e
    `hud*`, e para a `menu3056` desde a 0.0.16) desde a 0.0.15.
  - **Contador do HUD:** rótulo + "：" + valor formatado num único widget de 32. Foi a causa do travamento da
    Op 11-1 ("Solar Facilities Destroyed：1 facilities", 39 letras). Está no `validate.check_counters` desde a
    0.0.16.
  - Pausa: itens 16, títulos 20, e mais 30 widgets de 20 e 22 de 24 ainda sem uso conhecido. Esses ainda não têm
    regra.
  - Menus definem capacidades próprias (`0x28aa20`: 42, 50, 64, 80, 120, 255). Falta mapear tela por tela.
  - `crash_watch.py` mostra a capacidade de cada texto em jogo, nas duas classes.

### 8.6 Fila de trabalho

0. **Travamento da Op 12-1: causa real achada na 0.0.13 (texto maior que o widget); falta o teste no jogo.**
   - **Sintoma:** ao voltar da cutscene antes da luta com Kaine (D-1 Custom), o jogo congela. Igual na 0.0.10 e na
     0.0.12.
   - **Captura** (`work/crash/20261010-110851-travamento-12-1/`: savestate, 3 dumps, `emulog`): "TLB Miss" do
     código de sprites 2D do HUD (`0x288480`–`0x28998c`), seguido de "sceGsSyncPath: DMA Ch.1 does not terminate".
     O descritor (`+0x98`) do sprite `0x016e9670` foi sobrescrito por glifos de texto.
   - **Causa:** a janela de mensagem reserva espaço para 60 letras (`0x292704`; buffer de (7·60 + 11) × 16 =
     `0x1af0` bytes) e o desenhista de glifos `0x1a1050` não confere o tamanho.
     - Linhas inglesas acima de 60 caracteres (m6121 #72/77/123: 65–67) escreveram além do fim do buffer, que é
       exatamente o descritor do sprite seguinte.
     - O sprite só é desenhado na fase do chefe.
     - O japonês nunca passa de 60 (briefings e HUD: exatamente 60); o inglês passava em ~1.960 linhas.
     - Detalhes e números no CHANGELOG 0.0.13.
   - **Diagnóstico errado registrado na 0.0.11 (falta de memória na arena):** a 0.0.12, com 256 KB a mais, travou do
     mesmo jeito. O que segue (arena, contêineres sem tabela morta) continua correto como melhoria, mas não era a
     causa.
     - Arena: `0x00345040` (capacidade, base, cursor, bloco do topo; marcas por nível em `0x00345084`), alocação de
       baixo para cima, um bloco tirado do topo, NULL quando não cabe.
   - **Correção (0.0.13):** capacidade da janela de mensagem 60 → 128 (`exe.py`), mais o limite de 127 bytes
     visíveis por linha de mensagem no `validate.py`, porque o texto é copiado para um campo de 128 bytes.
   - **Falta:**
     - jogar a 12-1 e uma pausa com `crash_watch.bat`: o recenseamento de widgets mostra a capacidade de cada texto
       e alerta no instante de qualquer transbordo;
     - mapear os widgets de 16/20/24 letras (itens de pausa, títulos) e pôr esses limites no validador.
   - **Melhoria da 0.0.11 (memória, continua valendo):**
     - `ace2lib.mission_relayout` reconstrói cada tabela no lugar da japonesa e move as seções seguintes;
     - os 1.531 pares de seções dos gêmeos 6###/42### são idênticos byte a byte em offsets diferentes, ou seja, as
       seções não guardam posições;
     - crescimento: 42121 de +6.480 para **+256**; maior contêiner de +24.800 para +800; total de +920 KB para
       −12 KB. Tabela por missão em `work/ui/memoria_missoes_0.0.11.txt`;
     - `audit_iso.py` agora reprova contêiner com bytes mortos.
   - **Achado à parte, corrigido na 0.0.17:** `ace2lib.small_tables` ia de +8 até +12 e não lia nada quando a lista
     B estava vazia (+12 = 0). Agora usa o contador do byte +28 (`list_a`), e `mission_container()` reconhece também
     os 43 contêineres sem diálogo. São 786 subtabelas (eram 442); `unit_names` foi de 89 para 120 linhas.
0b. **Memória +256 KB na 0.0.12** (`tools/ace2/exe.py`, decisão do usuário): a fronteira pilha/heap sobe de
   `0x01f00000` para `0x01f40000`. Uso máximo medido da pilha: 161 KB, agora de 768 KB. Conferido no PCSX2: arena
   `0x1990100`, jogo inicia. `crash_watch.py` vigia arena e pilha durante o jogo.
0c. **Falas dos parceiros (grupo `xp`, 34 lotes, 2.657 frases):**
   - estavam em japonês no jogo inteiro porque moram no pedaço `PMS` dos pacotes de modelo `VMD` (2NNN e 36300+NNN),
     que o `textdb` não lia;
   - pipeline pronto: descoberta, exportação para `partnerNNN.json`, lotes com a voz em `phase`, regravação
     testada;
   - **traduzidas pelo Claude e aplicadas na 0.0.14** (6.138/6.138 linhas; detalhes no CHANGELOG). Falta o teste
     no jogo: falas inteiras na janela e o lixo de planilha `C68`/`C183` (mantido como no japonês);
   - correção de uma fala: editar a linha em `returns/xp_NN.json` não vale (a entrega fica como registro); use
     `reviewer_fixes.json` e `validate_return.py xp_NN --apply`, como nos outros lotes;
   - nomes de piloto (`partner_names`) já preenchidos pelo glossário;
   - `FNM` (nome do modelo) ainda fora: conferir se aparece na tela antes de traduzir.
0d. **Segunda tabela dos contêineres de missão (`+24`), não extraída:**
   - guarda os nomes de objeto/alvo que aparecem no HUD; 76 contêineres, 116 linhas e 41 nomes únicos em japonês;
   - exemplos: チューリップ (6041, 6101, 6172; o alvo da própria 4-1), ソーラー施設 (6111, o "achado à parte" da
     0.0.16), ギガノス基地, ランチゲート, カトンボ, 無限起動砲;
   - `+24` já é campo de offset no `mission_fields`. Falta descobrir a tabela no `textdb`, exportar (provavelmente
     para a `unit_names`) e conferir o crescimento de memória.
0e. **Transbordo de widget achado depois da 0.0.17 (primeiro item da 0.0.18):** `work/ui/auditoria_transbordo_0.0.17.md`.
   - Encurtar `menu3041` #0, #18, #19, #29 (mensagens do cartão "em andamento", 85–100 letras num widget de 80) e
     `menu3055` #25 e #32 (lista da Free Mission, 33–34 em 32; mesmas frases em `brief63010` #4 e `brief63013` #5).
   - Estender a regra `widget` do `validate.py` a `menu*` e `brief*` (linha única sem tags, japonês ≤ 32) e encurtar
     o que ela acusar (~45 linhas).
   - No teste, com `crash_watch.bat`: enciclopédia, cartas, ajuda da preparação de saída, Options, `menu3072`,
     `menu3009`, salvar com cartão cheio e sem cartão. Fecha as capacidades que faltam.
1. **Teste da 0.0.10:** pausar no meio da missão (crash da 0.0.9) e anotar a operação/missão; telas Intermission,
   Options > Game e Options > Controller sem rótulo em branco. Se a pausa ainda travar, a causa não é largura de
   texto: próximos suspeitos são os contêineres de missão que cresceram e o atlas da fonte 38000/2501. Depois,
   conferir os outros 300 e poucos rótulos de menu que passam de 141 px (o script do levantamento mede
   `jp ≤ 141 < en` em linhas de uma linha): nomes de unidade, região, objetivo e telas de save/versus, cujas caixas
   ainda não foram medidas.
2. **Teste no PCSX2 da 0.0.9** (feito em parte em 09/10). Roteiro:
   - briefings de 3 linhas inteiras dentro da caixa;
   - fala de missão longa perto de 380 px, para confirmar o limite provisório;
   - assinaturas de relatório alinhadas com espaços largos; créditos finais (`m6285`, recuo com espaços largos);
   - objetivos divididos em duas linhas (Ops 06, 09, 14, 18, 22);
   - rótulo "Rei" numa missão da Layzner (Op 19); "81％" e outros `％` largos (Op 08, Op 21);
   - lista de comandos "Hold ① + □□□□□" (198 px num limite de 197);
   - nomes de patente com `#i` (`menu3001#24-35`: SS, S... Ace, Rookie) — o `#i` pode trocar de fonte;
   - "No. 00" do save (`menu3041#13`): o jogo pode gravar o número numa posição fixa;
   - menus: as linhas de `work/ui/wide_0.0.9.txt` e `width_waivers.json`;
   - nenhum travamento nas missões, cujos contêineres cresceram.
3. **Menus:** capturar as telas (`work/ui`), medir as caixas, gravar em `limits.json` e então desfazer as
   abreviações forçadas pelo limite provisório (listadas nos relatórios dos revisores: "Unid. Units in Tokyo Bay",
   "B. Rifle", "Sub Cann. 01", objetivos de `menu3057`...). A enciclopédia rola: se a caixa permitir mais linhas, os
   parágrafos (linhas em branco) podem voltar.
4. **Fora das tabelas** (8.8): texturas, título do save, filmes.
5. **Glossário:** entradas que faltam (Mirauli, Sally Po, Peacemillion, Ahmos Gale, Titans, Mobile
   Doll, Sanc Kingdom, Laplamiz, Adoclass, Golg Gang, Sekiha Tenkyoken, ハイパー化, スカル小隊, 地上人) e conferir as
   variantes Jovian Federation (木連/木星連合) e Mobile Battleship × Martian Successor Nadesico (`menu3018` × `3022`).
6. **Validador:** checar o nome inteiro, não só uma palavra dele (ver 8.5).

### 8.7 Decisões pendentes e riscos

- **Grafias:** Tak × Tack; Sinapus × Synapse; Barkholz × Barkholtz; Show (ACE3) × Sho (wiki); Gekiganger × Gekigangar;
  King of Hearts × King of Heart; Sarge Opus × Sarge Aupus.
- **Termos (provisórios):** 地上人 = Upper Earthling; ナナフシ = Nanafushi; トランスユニット = Trans Unit;
  Ｄ兵器 = D-weapons; ダンコフ = Dankova; 聖戦士 = Holy Warrior; ボドル基艦 = Boddole Flagship; 先輩 = "Senpai" (manter
  ou reescrever?); 優人部隊, 相転移炉, 四天王, 文化矯正隊, ザ・カール, 強攻型 ainda sem verbete.
- **Fonte com inconsistência:** Misa é 大尉 e 中尉 em linhas diferentes; base aérea "第五" × "第４"; frota de
  Boddole Zer "数百万" × "５００万". O inglês segue cada linha.
- **Riscos técnicos:** limite de 380 px da missão provisório; caixas dos menus não medidas; contêineres de missão
  maiores nunca testados no jogo; tela da fonte de 21 px desconhecida (`@` não coube); `brief63196#5` com 431 px
  num limite de 430.
- **Quarentena:** apagar `_quarentena_google_0.0.3` e `_0.0.8`?
- **Decisões novas (dos revisores de 08/10):**
  - 先輩: "Senpai" nas Ops 21 × "Senior Gale" em `m6009#22/24`. Escolher um e uniformizar.
  - Créditos: leituras incertas (田雑直泉 "Naozumi Tazashi", 池田吉志 "Yoshishi Ikeda" e outras 20 em
    `agent/review/revisores_2026-10-08/rev_op26_28.md`; as dúvidas de todos os revisores estão nessa pasta); estilo com vogais longas (Satou, Ohtsuka) × grafia pública dos dubladores
    (Toru Furuya, Akio Otsuka); 服巻 = Haramaki.
  - Misa: 早瀬大尉 = "Capt. Hayase" pela tabela de patentes, mas o glossário a descreve como Lieutenant.
  - Armas sem nome oficial em inglês (tutorial): Flame/Frey/Flare Bomb, Shorter/Shooter, Removed/Removable Arm,
    Slit Wafer, Railcannon. "X Transform" × "X Transformation".
  - Títulos curtos de séries em `menu3022` ("Gundam Wing: Endless Waltz"...).
- **`BASE_RULES.md` indisponível:** `D:\Ace 1` não existe mais nesta máquina (o AGENTS.md aponta para lá). Os
  revisores de 08/10 usaram o PLANO.md e as regras do prompt. Recuperar ou copiar o arquivo para `docs/`.

### 8.8 O que ainda falta traduzir (levantamento de 2026-10-08)

**Tabelas de texto: nada.** As 10.695 linhas únicas que pedem tradução estão em inglês (campanha 6.822, menus
2.171, tutorial 628, missões extras 457, missões curtas 142, flashbacks 122, HUD 256, nomes 89, janelas 8).

> **Correção de 2026-10-23:** esse "nada" valia só para as tabelas que o `textdb` enxergava.
> - A missão 04-01 (6041/42041), a 6907 e 344 tabelas de nomes de alvo em 125 contêineres ficaram de fora até a
>   0.0.16. Traduzidos na 0.0.17: 46 linhas de missão e 31 nomes.
> - A segunda tabela `+24` dos contêineres (8.6 item 0d) continua de fora.

Fora das tabelas:

| Onde | O que é | Situação |
|---|---|---|
| Texturas `50641` em `62050`, `62052`, `62054`, `62057` | Cabeçalho "プレイヤーユニット / アナザーユニット" (com "PLAYER UNIT / ANOTHER UNIT" pequeno embaixo) na seleção de unidade. | **Traduzir** (4 cópias da mesma imagem). |
| Textura `50019` em `38002`, `38003` | Aviso de abertura: "「Another Century's Episode2」のストーリーはゲーム用に独自に制作された物です…" (a história é original do jogo e difere das séries). | **Traduzir.** |
| Textura `50196` em `62057` | Copyright com os nomes das empresas em japonês (サンライズ, ジーベック…). | Opcional (aviso legal; romanizar). |
| Textura `50020` em `38005`, `38006` | Corte "明鏡止水" da G Gundam. | Estilizado; provavelmente manter. |
| Executável `SLPS_258.29` (0x219150) | Título do save: "アナザーセンチュリーズエピソード２／Ｎｏ．００" (aparece no navegador de cartão de memória do PS2). | Opcional; o resto são mensagens de depuração. |
| `MOVIE001.PSS`, `MOVIE002.PSS` | Abertura ("Glorious", do disco original) e o outro filme. | **Não conferido** (é preciso decodificar o vídeo para ver se há texto queimado). |
| CSVs `102–105` (e `106`, binária) | Listas de depuração do desenvolvedor ("前作…", "テスト"). | Não aparecem para o jogador: não traduzir. |
| Vozes (`VOICE/*.BIN`) | Áudio. | Fora do escopo. |

O censo das texturas (`tools/research/texture_census.py`, imagens em `work/ui/textures/`) achou 1.655 imagens no formato do jogo (cabeçalho de 32
bytes com TEX0): retratos, prévias de missão (já com "OP 01-02" em inglês), mapas, ícones, logotipos, tela título
("PRESS START BUTTON"), "WARNING", "U.C.E", "ROUND START / WIN / LOSE / DRAW". Só as quatro acima têm japonês.
Texturas em outro formato (por exemplo dentro dos modelos 3D das missões) não entraram no censo. As texturas novas
não podem mexer nos glifos e pixels originais fora da área trocada (mesma regra das fontes).

