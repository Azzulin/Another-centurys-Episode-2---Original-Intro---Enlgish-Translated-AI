# Changelog

## Patch 0.0.17 publicado — 2026-10-27 (sem build nova)

- `make_patch.py --version 0.0.17` com o xdelta3 3.0.11 (`C:\Users\gabri\AceTools\xdelta3\xdelta3.exe`), 2 min 38 s:
  `ACE2-EN-0.0.17.xdelta` com 38.911.993 bytes (SHA-256
  `073c853666b7f43dcd04eecbee627e7eb46a426a0788734151fa02cece29ee06`). A decodificação de conferência passou. A
  saída com a abertura da SVV dá `8e8c5ed1740faa7924ce50f10913fcb1ecfb1ace0d80185185594ffc8e1be579`; com o
  `swap_movie.py` e o disco de 2006, `33fad6e5…2300a8d`, a 0.0.17 auditada.
- O `ace2lib.py` mudou um minuto depois da build da 0.0.17 (parâmetro `size` do `is_packed`, para o
  `crash_watch.py`). Conferido: `build.py --version 0.0.17 --svv-opening --write` com o código atual dá
  `8e8c5ed1…1be579`, igual à saída do patch. A build de conferência foi apagada.
- Repositório no estado da 0.0.17 (pre-release `v0.0.17` no GitHub). O `CLAUDE.md` passou a ir para o repositório
  (lista de cópia do `RELEASING.md` atualizada).
- Guia novo `docs/TAKING_OVER.md` (em inglês) para quem assumir o projeto ou começar uma tradução própria: montar o
  ambiente e provar que reproduz a 0.0.17, as regras, o ciclo de uma correção, a fila de trabalho em ordem (a mesma
  do ESTUDO 8.6, mais as recomendações da auditoria de transbordo), onde está cada registro, o que não roda mais.
- `STATUS.md`: patch publicado 0.0.17; problema 8 com o resultado de `work/ui/auditoria_transbordo_0.0.17.md`
  (mensagens do cartão de memória com 85–100 letras num widget de 80, `menu3055` #25 e #32 acima de 32, ~45
  prováveis); teste do cartão de memória na lista; campanha 6.865 linhas (com a `m6041`). Seção "What to test" sem
  a versão no título (os links `#what-to-test` dos outros guias voltam a funcionar).
- README com resumo em português; INSTALL_PATCH, BUILD_FROM_SOURCE, GLORIOUS_OPENING, MAKE_YOUR_OWN_*,
  TECHNICAL_REFERENCE com os números e SHA da 0.0.17.
- **Não corrigido ainda:** as linhas da auditoria de transbordo. É o primeiro item da 0.0.18.

## 0.0.17 — 2026-10-23 (teste interno)

- **Relato do teste da 0.0.16:** na Op 4, textos da missão e falas de piloto em japonês. Conferido na ISO 0.0.16
  (SHA `888f11d1…`): briefing 63003, táticos 63043–63045, debriefing 63171, relatório 63208 e o diálogo das missões
  6042/6043 estavam em inglês. **A missão 04-01 inteira (contêineres 6041/42041) estava em japonês:** objetivo,
  contador, rádio de abertura, todas as falas e "制限時間超過". Os nomes de alvo da 04-02 (ザクⅡ, ダウツェン,
  ＧＰ０２) também.
- **Causa 1 (`is_packed`, falso positivo):** na 6041 a lista A está vazia (`+8` = 0), e o cabeçalho
  `00 01 00 00 … 00 00 00 00` é idêntico à assinatura LZSS. O `mission_table` recusava o recurso como comprimido, o
  `try_unpack` falhava e o `textdb` pulava o recurso inteiro: nunca exportado, nunca em lote, nunca no build.
  - Correção: a assinatura só vale se o tamanho declarado (BE em `+4`) couber em 8× o recurso, porque o LZSS gera no
    máximo 128 bytes a cada 17 lidos. Os falsos positivos declaravam de 268 MB a 1,3 GB.
  - Na base inteira, só 203, 6041, 42041 e 6907 mudam de classe. Os outros 754 recursos comprimidos continuam iguais.
  - `is_packed(data, size)` aceita o tamanho do recurso quando só se tem o começo dele (`crash_watch.py`).
- **Causa 2 (`small_tables` e `patch_mission`, lista A):** liam os registros de `+8` até `+12`. Com a lista B vazia
  (`+12` = 0), não liam nada. Agora usam o contador do byte `+28` (`ace2lib.list_a`). É o "achado à parte" do ESTUDO
  8.6, item 0.
- **Causa 3 (contêiner sem diálogo):** 43 contêineres têm só a lista A (`+20` = 0): 6014–6016, 6030, 6034,
  6036–6039, 6050, 6330–6337, 6362, 6904, 6925, 6970, 6971, 6999 e gêmeos. O `_walk` só lia subtabelas quando havia
  diálogo. Agora `ace2lib.mission_container()` reconhece o contêiner com ou sem diálogo e é usado no `textdb`, no
  `audit_iso` e nos testes. `mission_text_bytes` e `patch_mission` aceitam a falta de diálogo.
- `mission_fields` aceita cabeçalho sem lista A (o tamanho do cabeçalho vem da primeira lista não vazia). Nos 244
  contêineres já aceitos, a lista de campos não muda. `mission_relayout` deixa como está um `+4` "tamanho" igual a
  0 (6904, 6999).
- **Descoberta agora:** 204 contêineres com diálogo (com 6041, 42041 e 6907) + 43 sem diálogo, com 786 subtabelas
  de nomes. O código da 0.0.16 lia 201 contêineres e 442 subtabelas: 125 contêineres ganharam 344 tabelas de nomes
  de alvo.
  - Tabelas novas: `m6041` (43 linhas, cópias 6041 e 42041) e `m6907` (3 linhas; missão extra da Nadesico).
  - `unit_names`: 89 → 120 linhas. Os nomes que já existiam chegam sozinhos às cópias novas (as linhas são chaveadas
    pelo japonês).
- **Traduzido pelo Claude** (`_fill` à mão):
  - `m6041`: 38 falas novas; as outras 5 repetem o inglês já usado (objetivo "Destroy 10+ Chulips", igual à
    `menu3056`; "Time Limit Exceeded"; "%d units"; "No enemy signatures in the area."; "No choice... Fall back for
    now!").
  - Contador "Chulips Destroyed：999 units" = 27 letras.
  - As linhas 300–314 são anotações de desenvolvimento ("作戦の補足", "バニングの喝"…) e ficaram entre parênteses, como as
    da `m6042`.
  - `m6907`: "Destroy all Batta", "Nadesico sunk" e uma fala.
  - 31 nomes de alvo novos pelo glossário (Nu Gundam, Devil Gundam, Gundam Head, Dankova, Zakaal, Geara Doga,
    Aestivalis (Ryoko/Hikaru/Izumi), VF-1A (Hikaru)…).
  - "ガンダムデスサイズヘル" ficou **"Deathscythe Hell"**: com o "Gundam" daria 243 px, acima da maior linha
    japonesa da tabela (225 px).
  - Quatro falas da 6041 acima de 380 px foram encurtadas ou quebradas em duas linhas. `merge_fill`: 0 linha larga
    nas três tabelas.
- **Cuidado do processo:** o `_fill/unit_names.json` é indexado pela posição da linha, e o `export_text` inseriu as
  linhas novas no meio (a ordem é a do japonês). O fill foi remapeado pelo japonês: índice antigo → japonês → índice
  novo. Nenhuma referência `unit_names#` em `auto/`, `reviewer_fixes.json` ou `width_waivers.json`. O
  `glossary.py --write`, que gerava esse fill, depende de `D:\Ace 1` e não roda mais.
- `operations.py` regenerado: a Op 4 agora tem `m6041` (222 linhas). A lista `shared` passou a mostrar as tabelas
  `partnerNNN` (o arquivo não era regenerado desde a 0.0.14).
- Testes: `test_identity.py` PASS (com a regravação sem edição dos contêineres sem diálogo) e `test_textdb.py` PASS
  (786 subtabelas, 651 recursos, sem bytes mortos, inclusive nos contêineres sem diálogo).
- **Memória:** 128 recursos diferentes da 0.0.16, todos contêineres de missão. 6041 e 42041: +384 bytes cada.
  6907: +0. Os demais variam de −16 a +16 (nomes em inglês às vezes ocupam menos que o japonês). Total +128 bytes
  em relação à 0.0.16.
  - Na auditoria: 247 contêineres regravados, o maior crescimento continua sendo +800 (6010), total −12.048 bytes
    (eram −12.176). Parceiros sem mudança (+512 no máximo).
- `audit_iso.py` passou: 651 recursos, 1.741 locais de texto (eram 1.394). SHA-256
  `33fad6e583aa305123afbf4e2d6c41f6b110d6ad395cc32789d87369e2300a8d`.
- Conferido na ISO 0.0.17: todas as tabelas da Op 4 (briefings, 6041/42041, 6042/42042 com os três nomes,
  6043/42043, debriefing, relatório) sem nenhuma linha em japonês.
- Fontes idênticas às da 0.0.16 (pacotes 38000–38006 e 62050–62057 byte a byte).
- **Achado à parte (não corrigido):** a segunda tabela do contêiner (`+24`) guarda os nomes de objeto e alvo no HUD
  e não é extraída. São 76 contêineres, 116 linhas e 41 nomes únicos em japonês, por exemplo チューリップ (6041,
  6101, 6172), ソーラー施設 (6111, o "achado à parte" da 0.0.16), ギガノス基地, ランチゲート, カトンボ. Na
  própria 4-1, o alvo travado ainda aparece como "チューリップ".
- **Para testar:** a Op 04-01 inteira (falas, contador, fim por tempo) e os nomes de alvo da 04-02. Se der, uma
  missão de Free Mission ou extra (6330–6362, 6904, 6970) para ver os nomes. Usar `crash_watch.bat`, que agora
  aponta para a 0.0.17.

## Patch 0.0.16 publicado — 2026-10-17 (sem build nova)

- `make_patch.py --version 0.0.16` com o xdelta3 3.0.11 oficial (nesta máquina em
  `C:\Users\gabri\AceTools\xdelta3\xdelta3.exe`), 3 min 23 s: `ACE2-EN-0.0.16.xdelta` com 38.906.005 bytes
  (SHA-256 `c558e76839cb8e3c8d6f7b5a4f87ca16396713e2424a9a0fc3a00b7cbe4ea9c3`). A decodificação de conferência passou.
  A saída com a abertura da SVV dá `1608ce46…f40890`, igual à build `--svv-opening` feita à parte no clone. Com o
  `swap_movie.py` e o disco de 2006, dá `888f11d1…4ac79e`, a 0.0.16 auditada.
- O patch é ~85 vezes maior que o da 0.0.10 (454.701 bytes). Causa provável, não medida recurso a recurso: desde a
  0.0.14 a build regrava os 108 pacotes de parceiro comprimidos (36xxx, 57,7 MB de recursos LZSS), e o fluxo
  comprimido muda inteiro a partir do primeiro byte alterado. Cabe com folga no limite do GitHub (2 GiB por arquivo).
- Publicado como pre-release `v0.0.16` no GitHub, com `.xdelta`, `-SHA256.txt` e `swap_movie.py`, e a tag no commit
  que traz este registro.
- `make_patch.py --svv-opening`, para quem não tem o disco de 2006: usa `ACE2-EN-<v>-svv-opening.iso` e confere a
  saída contra o SHA do próprio relatório; sem o disco de 2006, o arquivo de SHA sai sem as linhas do Glorious.
  - Testado simulando a ausência do disco de 2006 (a cópia de conferência `1608ce46…` no papel da build
    `--svv-opening`). Sem a opção, recusa. Com ela, gera um patch cuja saída é a mesma `1608ce46…`; o `.xdelta` só
    difere em 7 bytes, o nome do arquivo de destino que o xdelta3 grava no cabeçalho.
- Guia novo `docs/MAKE_YOUR_OWN_PATCH.md` (inglês): como qualquer pessoa gera e publica o próprio patch. Cobre nome
  de versão próprio, build, auditoria, xdelta3, `make_patch.py`, aplicar e conferir, e release no próprio fork
  (web ou `gh`). README, INSTALL_PATCH, STATUS, BUILD_FROM_SOURCE, MAKE_YOUR_OWN_TRANSLATION, GLORIOUS_OPENING e
  RELEASING apontam o patch 0.0.16 e o guia.
- README: a edição feita direto no GitHub em 17/10 (crédito do tradutor externo sem nomear o agente) foi trazida
  para esta pasta. O modelo de notas do RELEASING e as notas da release seguem o mesmo critério.

## Repositório público atualizado — 2026-10-17 (sem build nova)

- O GitHub estava na 0.0.10 (montado a partir de uma cópia antiga), com ferramentas que esta pasta não tinha. Agora
  os dois têm o estado da 0.0.16:
  - do repositório para cá: `swap_movie.py`, `make_patch.py`, `build.py --svv-opening`, `audit_iso.py
    --svv-opening`, `ACE2_FONTS` no `fonts.py`, a entrada de 15/10 abaixo, as linhas da seção 4 do ESTUDO e a regra
    do repositório no AGENTS.md. Também os guias em inglês (`README.md`, `CHANGELOG.md` e `docs/*.md` em inglês) e o
    `.gitignore`, para que a pasta seja a fonte de tudo o que vai para o GitHub;
  - daqui para o repositório: ferramentas 0.0.11–0.0.16 (`exe.py`, `mission_relayout`, VMD, regras de widget,
    `crash_watch`), todas as traduções (inclusive os parceiros), docs em português e relatórios 0.0.15/0.0.16.
  - Na fusão, o `--svv-opening` passou a manter o patch do executável (só o filme muda).
- Guias em inglês reescritos para a 0.0.16: STATUS (travamentos e causas, o que testar), widgets e limites para
  tradutores, tabelas `partnerNNN`, PCSX2 (CRC e savestates), `crash_watch`, Python 3.12 ou mais novo, e como
  atualizar o repositório a partir desta pasta (`docs/RELEASING.md`).
- `.gitignore`: `work/crash/`, `*.p2s`, `*.7z`, `*.url`, `*.chd`, `*.cso`, `work/output/_test/`.
- **Conferido:** build a partir do clone do repositório (`build.py --version 0.0.16 --write`, Python 3.12 do
  `%LOCALAPPDATA%\ace2-venv`; planejamento em 470 s) reproduziu o SHA-256 `888f11d1…4ac79e` e o relatório JSON
  byte a byte; `audit_iso.py` passou. A build `--svv-opening` dá `1608ce46831834437f53d427c8441b6c7ad9aeff0f4ebb5ae8b5caf9f8f40890`
  (auditoria `--svv-opening` passou), e o `swap_movie.py` com o disco de 2006 a leva de volta a `888f11d1…4ac79e`.

## 0.0.16 — 2026-10-16 (teste interno)

- **A 0.0.15 travou no mesmo ponto da Op 11-1, ao destruir a primeira instalação solar.** Desta vez houve captura com
  `crash_watch.bat` (`work/crash/20261016-152322/`: 3 dumps de RAM e savestates).
  - O vigia pegou o transbordo no instante exato: `TEXTO TRANSBORDA! capacidade 32, 39 letras: 'Solar Facilities
    Destroyed：1 facilities'` (o widget `018a6ba0` escreveu 4.544 bytes num buffer de 3.760). O jogo travou logo
    depois, com os mesmos endereços de DMA de sempre (`00632fd0`/`00789b20`). Esses endereços são buffers gerais
    de desenho e também aparecem no travamento da 12-1.
  - **Causa:** o contador do HUD desenha **rótulo + "：" + valor formatado num único widget de 32 letras**. Em
    japonês fica `ソーラー施設破壊数：1基` (12 letras). A regra da 0.0.15 media o rótulo e o valor separados (26 e
    13), e os dois passavam.
  - O objetivo de 35 letras corrigido na 0.0.15 não era o que travava aqui, mas o limite continua valendo.
- **Correção:** os contadores que passavam de 32 (contando 3 dígitos):
  - Op 11-1: valor `%d facilities` → `%d`, que mostra "Solar Facilities Destroyed：12" (`op11_01`);
  - Op 21-1: rótulo "Heavy Attackers Escaped" → "Heavy Attackers Passed" (重攻撃機通過数, como "Missiles Breached" da
    17-1), que mostra "Heavy Attackers Passed：7 units" (`op21_01`);
  - Op 22-2: valor `Durability: %d％` → `HP %d％`, que mostra "Resistance Facility：HP 100％" (`op22_02`).
- **A `menu3056` (objetivos nas telas de dados da missão e da Free Mission) usa o mesmo widget de 32.**
  - O vigia viu "Destroy 12 or more solar facilities" (35) nela.
  - As 12 linhas eram cópias `tm` do texto antigo. Agora recebem o inglês novo dos objetivos via
    `auto/overrides.json`.
- **`validate.py`:**
  - `check_counters(tabela, linhas)`: numa missão, uma linha simples com `%d` logo depois de uma linha simples (o
    rótulo) precisa caber em rótulo + 1 + valor ≤ 32. Ela roda no `build.py` e no `merge_fill.py`.
  - A regra `widget` passou a valer também para a `menu3056`.
  - Antes da correção, as duas regras acusavam exatamente esses 15 casos; agora, 0.
- **Achado à parte:** o alvo da 11-1 aparece no HUD como `ソーラー施設`, em japonês. Ele vem da lista de nomes do
  contêiner (42111 +0xd90), a mesma lista que o `small_tables` não lê (ESTUDO 8.6, item 0, "achado à parte").
  É lacuna de tradução, não causa de travamento.
- Memória: os contêineres de missão continuam com +800 bytes no máximo (6010) e somam −12.176 bytes. Os parceiros
  continuam com +512 no máximo. São os mesmos 605 recursos.
- `audit_iso.py` passou (SHA-256 `888f11d1e518cd45a7b71002cd041ee087e537e592d8e6d68cb8825f5b4ac79e`).
- **Para testar:** a Op 11-1 inteira (destruir as 12 instalações) e, se der, as Ops 21-1 e 22-2. Usar
  `crash_watch.bat`, que agora aponta para a 0.0.16.

## 0.0.15 — 2026-10-16 (teste interno)

- **Travamento da Op 11-1 na 0.0.14 (relato do usuário): texto mais longo que o widget, de novo, agora nos widgets
  de 32 letras.**
  - **Log do PCSX2** (`Downloads\PCSX2\logs\emulog.txt`, sem savestate): cerca de 107 s depois do boot, só
    "sceGsSyncPath: DMA Ch.1 does not terminate" em sequência, sem o "TLB Miss" da 12-1. A fila da GPU parou num
    pacote corrompido.
  - **Capacidade padrão:** todo widget de texto cujo dono não define a capacidade fica com **32 letras** (init
    `0x289dfc`). Os únicos que definem outra são a janela de mensagem (128), os itens da pausa (16/20/24) e algumas
    telas de menu (`0x28aa20` com 42, 50, 64, 80, 120, 255).
  - **Segunda classe de widget:** a captura da 12-1 tem também widgets com o alocador `0x28a0f0`, cujo buffer é de
    (11n + 12) × 16 + 32 bytes. Eles guardam as condições de vitória/derrota da tela MISSION INFORMATION e a linha
    de ajuda do menu de pausa ("Unpause and return to the game."). O `crash_watch.py` antigo não enxergava essa
    classe (65 widgets na captura; agora são 79).
  - **O que passava de 32:** o objetivo da 11-1, `m6111#0` "Destroy 12 or more solar facilities", tem 35 letras. Mais
    19 objetivos de missão (o japonês nunca passa de 16) e 7 linhas de ajuda da pausa (`hud3013` #16–18, #56–59,
    por exemplo "Review abilities and attack commands.", com 37 letras, que aparece só de passar o cursor em
    Commands).
  - O transbordo só trava quando o vizinho do buffer é usado depois, por isso nem toda linha longa travou (a 12-1
    tem objetivo de 38 letras e passou na 0.0.13). A ajuda da pausa é candidata forte ao travamento ao pausar da
    0.0.9.
- **Correção (sem patch no executável):** 27 linhas reescritas com até 32 letras, mudando o mínimo e no estilo
  telegráfico do japonês: "Destroy 12+ solar facilities", "4+ allied ships escape the area", "Raze all industrial
  facilities", "View abilities and commands.", "Start the mission over again."...
  - Linhas de lote em `reviewer_fixes.json`: 20 linhas de 15 lotes (xa_01/04/05, op02_01, op05_01, op06_01, op10_02,
    op11_01, op12_01, op12_02, op14_01, op16_02, op19_02, op21_01, xd_01).
  - `m6021#0` também é linha automática (`tm`) e foi para `auto/overrides.json`.
  - `m6173#0` e `m6192#1` são cópias (`repeat`) e acompanham pela regra automática.
  - `hud3013` foi corrigida em `_fill/`.
- **`validate.py`:** nova regra `widget`. Uma linha sem tags e sem quebra, de missão (`m6###`, fora os créditos
  `m6285`) ou do HUD, cujo japonês cabe em 32 letras, tem no máximo 32 letras em inglês (espaços contam; `%d` conta
  como 3). `check_row` recebe a tabela (`build.py`, `merge_fill.py`, `validate_return.py`). A regra pegava
  exatamente as 27 linhas; agora são 0.
- **`crash_watch.py`:** o recenseamento reconhece as duas classes de widget. O `crash_watch.bat` aponta para a
  0.0.15.
- Ainda sem regra: os 22 widgets de 24 e os 30 de 20 letras da pausa, que ficam vazios na captura (lista de
  comandos? legenda do mapa?). Também ficam de fora as linhas de menu acima de 32 letras (294), porque as telas de
  menu definem capacidades próprias.
- Memória: os contêineres de missão continuam com crescimento máximo de +800 bytes (6010) e total de −12.112 bytes.
  Os pacotes de parceiro continuam com +512 no máximo. São os mesmos 605 recursos alterados.
- `audit_iso.py` passou (SHA-256 `4281f242ee08eafeeeeded3aec95cff1482b53994e7cb11dec370fdeab9f5d1e`).
- **Para testar:** a Op 11-1 inteira, até e depois do "Mission Update". Pausar e navegar por todos os itens
  (Commands, Retry, To Intermission) e abrir MISSION INFORMATION e COMMAND LIST. Se possível, rodar com
  `crash_watch.bat`.

## Repositório público — 2026-10-15 (sem build nova)

- Documentação em inglês para o GitHub: `README.md`, `CHANGELOG.md` (raiz, em inglês) e `docs/INSTALL_PATCH.md`,
  `GLORIOUS_OPENING.md`, `BUILD_FROM_SOURCE.md`, `MAKE_YOUR_OWN_TRANSLATION.md`, `AI_TRANSLATION_WORKFLOW.md`,
  `TECHNICAL_REFERENCE.md`, `RELEASING.md`, `STATUS.md`. `.gitignore` exclui ISOs, `.PSS`, `.xdelta`, `.venv` e as
  quarentenas (uma tem uma ISO de 3,5 GB).
- `tools/ace2/swap_movie.py`: troca o `MOVIE001.PSS` de uma imagem pelo de outra, no mesmo lugar (os dois têm
  275.251.204 bytes), e confere o resultado. Só biblioteca padrão, para o jogador rodar sem o ambiente. Testado com
  as ISOs reais: SVV japonesa + Glorious, 0.0.10 `--svv-opening` + Glorious = SHA da 0.0.10, e a volta.
- `tools/ace2/make_patch.py`: xdelta da SVV intacta para a build **com a abertura da SVV recolocada** (o patch não
  carrega o filme de 2006), decodificação de conferência, SHA da versão Glorious recalculado e
  `work/release/ACE2-EN-<v>-SHA256.txt`. Rodado com o xdelta3 3.0.11 oficial (jmacd/xdelta-gpl): patch da 0.0.10 com
  454.701 bytes; saída com a abertura da SVV `60227c82…a2aa` (igual à build `--svv-opening` feita à parte); com o
  `swap_movie.py` e o disco de 2006, `3e8c6143…8c12` (a 0.0.10 auditada). Publicado como pre-release `v0.0.10` no
  GitHub.
- `build.py --svv-opening` e `audit_iso.py --svv-opening`: build sem o disco de 2006 (para usuários). O padrão
  continua sendo a abertura "Glorious".
- `fonts.py`: pasta das TTF configurável por `ACE2_FONTS` (padrão `C:\Windows\Fonts`).
- Ambiente desta máquina conferido: `build.py --version 0.0.10 --write` reproduziu o SHA-256
  `3e8c6143…8c12`.
- Observação (17/10): o repositório foi montado a partir de uma cópia da 0.0.10. As ferramentas e entradas acima
  não estavam nesta pasta até a atualização de 17/10.

## 0.0.14 — 2026-10-10 (teste interno)

- Teste da 0.0.13 (relato do usuário): as cutscenes não travam mais e o gameplay ficou estável até agora.
- **Falas dos parceiros em inglês:** 107 parceiros, 6.138 linhas (2.657 frases únicas). As linhas restantes são
  cópias da mesma frase, preenchidas pela repetição automática.
  - Por decisão do usuário, quem traduziu foi o Claude, não o agente externo. As entregas estão em
    `agent/returns/xp_01..34.json`, marcadas no `translator_summary` como "Translated by Claude". Os 34 lotes
    estão em `handed.json` e `applied.json`, e passaram pelo mesmo validador (0 erros).
  - Voz de cada personagem conforme o PLANO (Gato e Zechs formais, Duo e Kaine soltos, Rei em frases curtas de
    máquina como na campanha: "Alarm message: ..."). Nomes e termos pelo glossário: Gavlet Gablae, Ashura Temple,
    Upper Earthling, Hawk of Giganos, Skull Leader, "Gundam Fight!! Ready... go!!".
  - Os trocadilhos da Izumi viraram trocadilhos em inglês com a mesma forma (確認/角煮 → "confirmed / confit",
    帰還/きかん → "return to sender"...). A lista está nas `uncertainties` de `xp_20`.
  - 14 linhas reescritas mais curtas para caber em 2 linhas de 380 px. Três falas da Marina (`partner201#48/51/52`)
    não têm token nenhum, por isso o lote as limita a 1 linha.
  - O original tem lixo de planilha visível em quatro linhas: `C235` depois do `<ed()>` (`partner060#48`), `C68`
    (`060#51`), `C183` (`172#49`) e `+C89` (`022#54`). Foi mantido igual ao japonês. Também há duas falas de teste
    ("僚機ダミーボイス再生中"), traduzidas ao pé da letra.
  - Dúvida: ヤルフの神 (Black Knight, `partner064#46`) não está no glossário e ficou "the god Yarf".
- **Memória:** os 108 pacotes de parceiro, que ficam residentes na missão, crescem no máximo **+512 bytes**
  (2022, Gato). O `DATA.BIN` cresce +737.280 bytes em relação à 0.0.13, e a sobra no fim do disco é de 20,2 MB.
- Ambiente: esta máquina usa um venv local (`%LOCALAPPDATA%\ace2-venv`, Python 3.12 com o `requirements.txt`). O
  `.venv` da pasta aponta para o Python da outra máquina. As fontes escolhidas são iguais às da 0.0.13.
- Nada mudou em menus, missões e HUD. São os mesmos 605 recursos alterados da 0.0.13, agora com o texto dos
  parceiros em inglês.
- `audit_iso.py` passou (SHA-256 `ee93ee69969950b22f1e076e9913cda6530b0c815a554a79591e7dce0ae9e74d`).
- **Para testar:** escolher parceiros de séries diferentes (Gato, Izumi, Layzner/Rei, Gon Jem) e conferir se as
  falas aparecem inteiras na janela, inclusive as quebradas em duas linhas. Conferir também se `C68`/`C183`
  aparecem na tela, como no japonês.

## 0.0.13 — 2026-10-10 (teste interno)

- **Causa real do travamento da Op 12-1 (a 0.0.12 travou igual): texto mais longo que o widget.**
  - **Correção do diagnóstico:** a falta de memória da 0.0.11/0.0.12 estava errada. A 0.0.12 tem 256 KB a mais e
    travou com a mesma assinatura, na mesma rotina (`0x288480`) e nos mesmos endereços.
  - **Como o motor desenha texto:** cada widget de texto (init `0x289bd0`) reserva uma vez um buffer de
    (7·n + 11) × 16 bytes para n letras (`0x289e30`). O desenhista (`0x1a1050`) escreve 7 qwords por caractere,
    espaços incluídos, sem conferir o tamanho.
  - **O limite da janela de mensagem:** ela pede n = 60 (`0x292704`). O japonês nunca passa de 60 (briefings e HUD
    batem exatamente 60); o inglês passava em ~1.960 linhas.
  - **O que travou a 12-1:** linhas de 65 a 67 letras antes da cutscene, por exemplo `m6121#72` "Our fleet has
    reached the objective. / Albion, thanks for the cover.", escreveram além do buffer, por cima do descritor de um
    sprite de HUD vizinho. Esse sprite só é desenhado na fase do chefe: daí "TLB Miss" e fila da GPU parada.
  - **Medições:** na captura, o texto da janela usou 375 qwords (52 letras) de um buffer de `0x1af0`, que termina
    exatamente no descritor corrompido, com o rastro de glifos passando dele. O rótulo do nome usa n = 32.
- **Correção:** o patch `0x292704` (`exe.py`) muda a capacidade da janela de mensagem de 60 para 128, o que custa
  +7,6 KB por janela.
  - O texto da janela é copiado para um campo de 128 bytes (com contador logo depois), então 128 cobre tudo o que
    a janela consegue mostrar.
  - `validate.py`: linha de janela de mensagem (com `<sp(`) tem no máximo 127 bytes visíveis (sem `<...>` e sem
    códigos de cor, com as quebras). O build barra o que passar disso.
  - 7 linhas de briefing passavam de 127 bytes. Foram reescritas com o mínimo (`reviewer_fixes.json`; a
    `brief63200#6` é linha automática, ficou em `auto/overrides.json`), sem perder sentido; em três, sai um
    acréscimo que o japonês não tem ("strictly"...).
- **Provável causa também da pausa da 0.0.9:** as confirmações do menu de pausa (`hud3013` #21–23, #60–61) têm de
  89 a 96 letras numa janela de 60.
- `crash_watch.py`: recenseia todos os widgets de texto na RAM a cada 3 s (capacidade, letras, texto) e grava
  savestate + RAM no instante em que um passa do buffer.
  - Na captura da 12-1 ele achou 65 widgets: itens de pausa com 16 letras, títulos com 20, rótulos com 32 e a
    mensagem com 60.
  - Os widgets com 16/20/24 ainda não têm regra no validador. O recenseamento no jogo vai dizer quais textos usam
    cada um.
- As mudanças da 0.0.11/0.0.12 continuam valendo: os contêineres sem tabela morta tiram ~930 KB de desperdício, e a
  pilha mais curta dá +256 KB de margem. Mas elas não eram a causa deste travamento.
- **Falas dos parceiros nunca tinham sido extraídas** (relato do usuário: companheiros falam em japonês em todas as
  missões).
  - Elas ficam dentro do pacote de modelo de cada parceiro (`O:\sr\model\partner\pNNN`, recurso `2NNN` e cópia
    compactada `36300+NNN`), no pedaço `PMS` do formato `VMD`, que é uma tabela de texto comum. O `textdb` só
    procurava tabelas no início de um recurso ou em pacotes `BND`.
  - 107 parceiros, 6.138 linhas, 2.658 frases únicas. Os nomes de piloto (`PPN1`/`PPN2`, 51 nomes) foram
    preenchidos pelo glossário em `_fill/partner_names.json`.
- O `VMD` é uma cadeia de pedaços percorrida pelos tamanhos, sem nenhum offset absoluto.
  `ace2lib.vmd_chunks`/`vmd_replace` reconstroem a tabela com o tamanho que precisar e movem os pedaços seguintes;
  o resto do pedaço (frases velhas sem ponteiro) é preservado.
  - `textdb` descobre `2070:vPMS`, `36370:lz:vPMS`... (1.394 locais de texto, eram 934); famílias `partnerNNN`
    (janela de diálogo de missão) e `partner_names`.
  - `export_text.py` grava `work/translation/partners.json` (quem fala em cada tabela).
  - `batches.py` tem o grupo `xp`: 34 lotes com a voz no campo `phase` ("speaker: Kou | unit: GP01").
  - `PLANO.md` do agente explica o grupo.
- Testes: `test_identity.py` (460 tabelas de pacote de parceiro reproduzidas byte a byte) e `test_textdb.py` (texto
  1,5x em 1.394 locais, 605 recursos reconstruídos, o disco ainda sobra 20 MB). O `audit_iso.py` informa o maior
  crescimento dos pacotes de parceiro, que ficam na memória durante a missão (os 256 KB da 0.0.12 cobrem).
- Fica de fora por enquanto: `FNM` (nome do modelo, em 535 pacotes, inclusive inimigos). Não se sabe se aparece na
  tela ou se o jogo o usa como chave.
- As falas em si (`partnerNNN`) ainda **não estão traduzidas** nesta build: faltam os 34 lotes `xp`. Só os nomes
  de piloto já estão em inglês.

## 0.0.12 — 2026-10-10 (teste interno)

- **Memória do jogo +256 KB** (decisão do usuário: o jogo inteiro traduzido sem risco de travar por memória).
  - O jogo dá a uma arena tudo o que fica entre o executável e a pilha. A pilha tinha 1 MB e o maior uso medido foi
    161 KB (boot, menus, briefing, Op 12-1 e a cutscene).
  - `tools/ace2/exe.py` sobe a fronteira pilha/heap de `0x01f00000` para `0x01f40000`: 3 palavras do
    `SLPS_258.29` (`0x10019c`, `0x1001a0`, `0x12b268`). A pilha fica com 768 KB e o topo não muda; a segunda área de
    2 MB segue o fim da arena (getter `0x150290`).
  - Conferido no PCSX2: capacidade da arena `0x1950100` → `0x1990100` (+256 KB), jogo inicia normalmente, sem "TLB
    Miss", pilha em 161 KB de 768 KB.
  - Com isso, o pior caso de crescimento da tradução numa missão (~1,9 KB: contêiner +800, HUD +1.056) fica mais de
    130 vezes abaixo do espaço ganho.
- `disc.py` aceita trocar um arquivo por bytes prontos; `build.py` grava o executável corrigido; `audit_iso.py`
  exige que o executável seja o original com exatamente esses patches.
- No PCSX2 o CRC do jogo muda (savestates da 0.0.11 e anteriores não carregam nesta build); saves do memory card
  continuam valendo. As correções do GameDB do PCSX2 são por serial e continuam valendo.
- `crash_watch.py` mede o uso máximo da pilha desde o boot (alerta acima de 600 KB).
- Texto e recursos do `DATA.BIN` iguais aos da 0.0.11.
- `audit_iso.py` passou (SHA-256 `feada09f94d4275077415193b9d3c7d7da0b7fe75d599084b37ba655e461f14b`).

## 0.0.11 — 2026-10-10 (teste interno)

- **Travamento da Op 12-1 (0.0.10) corrigido na origem: falta de memória.**
  - Sintoma: o jogo congelava ao voltar da cutscene antes da luta com Kaine (D-1 Custom).
  - Causa: o jogo põe a missão numa única arena de memória (`0x003afe00..0x01cfff00`), e o alocador devolve NULL
    quando o pedido não cabe. Ao sair da cutscene, a arena encheu, sprites do HUD da fase do chefe ficaram sem
    descritor, gravaram em 0x0 e a fila de desenho da GPU travou. Diagnóstico completo em `ESTUDO_ACE2.md` 8.6, item 0.
  - Parte da tradução: a 0.0.10 punha nessa arena 7,5 KB a mais que o original. O contêiner 42121 crescia +6.480
    bytes porque a tabela inglesa era anexada no fim e a japonesa ficava morta; o pacote de HUD 38000 crescia
    +1.056 bytes por causa das fontes.
  - Correção: `ace2lib.mission_relayout` reconstrói cada tabela de um contêiner de missão no lugar da japonesa, com
    o tamanho que precisar, e move as seções seguintes, atualizando todos os offsets do cabeçalho e das listas.
    Comprovado que as seções não guardam posições: os 1.531 pares de seções dos gêmeos 6###/42### são idênticos em
    offsets diferentes.
  - Efeito: 42121 de +6.480 para **+256** bytes; maior contêiner de +24.800 para +800; total dos 201 de +920 KB
    para **−12 KB**. Tabela por missão em `work/ui/memoria_missoes_0.0.11.txt`.
  - Provavelmente é a mesma causa do travamento ao pausar da 0.0.9.
- Texto, fontes, menus e HUD **idênticos** à 0.0.10: os 188 recursos que não são contêineres saíram byte a byte
  iguais, e os 201 contêineres têm as mesmas linhas. O ambiente desta máquina (Python 3.12, mesmas fontes) reproduz
  a 0.0.10.
- `audit_iso.py`: nova checagem "mission memory". Um contêiner tem de crescer exatamente o que as suas tabelas
  crescem, e a auditoria imprime o maior crescimento. A 0.0.10 reprova (201 contêineres com bytes mortos).
- Testes adaptados: `test_identity.py` (relayout com a tabela original reproduz os 201 contêineres byte a byte),
  `test_textdb.py` (texto sintético 1,5x em todas as 934 tabelas sem bytes mortos; o `DATA.BIN` diminui 53 KB) e
  `test_disc.py`.
- Nova ferramenta `tools/research/crash_watch.py` (só lê o jogo), ligada ao PCSX2 pela PINE:
  - vigia a arena de memória ~50 vezes por segundo (espaço livre, mínimos, bloco do topo, níveis) e a lista de
    recursos carregados;
  - acha o contêiner da missão na RAM e compara com a ISO por seção;
  - grava savestate + dump da RAM em `work/crash/<data-hora>/` quando a arena fica quase cheia, quando a tabela de
    diálogo é sobrescrita ou quando o usuário digita `d`;
  - o modo `check` lê um dump ou savestate: registradores EE, pilha, arena, recursos carregados.

  `crash_watch.bat` (clique duplo) abre o PCSX2 com a ISO e o monitor. No PCSX2 desta máquina (`Downloads\PCSX2`)
  a PINE e o log "EE Console" foram ligados; o `PCSX2.ini` anterior ficou em `inis\PCSX2.ini.antes-pine.bak`.
- Achado à parte, não corrigido: em 82 contêineres os nomes de inimigo (lista A sem lista B depois) nunca foram
  exportados e continuam em japonês (`ESTUDO_ACE2.md` 8.6, item 0).
- 389 recursos alterados; `audit_iso.py` passou (SHA-256
  `374a798d8c6bd0877cb648b77f319f991fc2f4f9423807aeec9d0952f7025a77`).

## 0.0.10 — 2026-10-09 (teste interno)

- Primeiro teste no PCSX2 desde a 0.0.1 (feito com a 0.0.9). Achados:
  - **Rótulos de menu somem por inteiro acima de ~141 px** (fonte de menu): tudo até 141 px aparece ("Flight
    Reverse", "Invert Y-Axis", "Encyclopedia"); tudo a partir de 154 px fica em branco ("Return to Menu",
    "Controller Type", "Camera Priority", "Reset to Defaults", "Auto Altitude Adjustment"). Não é limite de bytes
    ("Flight Reverse" e "Return to Menu" têm 14). Os lotes de menu tinham saído com `max_line_px` 350.
  - **Crash ao pausar no meio da missão** (o log do PCSX2 não registra nada). Suspeita: o mesmo tipo de limite, sem a
    proteção que os menus têm. Não confirmado.
- Menus (correção em `reviewer_fixes.json`; as cópias herdam pela repetição automática):
  - `menu3004#15` "Back to Menu" (também `menu3040#11`, `menu3054#7`);
  - `menu3070#8` "Defaults" (também `menu3071#10`, `3072#8`, `3073#5`, `3076#7`);
  - Target: "Camera" / "Facing" / "Distance" / "Damage" (`menu3070#14-17`);
  - Controller: "Control Type", "Camera", "Auto Altitude" (`menu3071#3/5/8`).
- Menu de pausa (`hud3013`): cada item ficou dentro da largura do japonês. "Resume", "Commands", "To Intermission",
  "To Free Mission", "To Versus Menu", "1P/2P Commands"; barra "Select:㊤㊦　Exit:⑪　OK:○" (241 px, JP 245); ajuda
  "Restart the mission from the start.", "Review 1P's/2P's abilities and commands."; faixa "Mission Complete"
  (168 px, JP de faixa até 191).
- `merge_fill.py` quebrava no console do Windows ao imprimir "①" (`UnicodeEncodeError`) e deixava parte das tabelas
  sem mesclar. Rodar com `PYTHONIOENCODING=utf-8`.
- 389 recursos alterados; `audit_iso.py` passou (SHA-256
  `3e8c61433aab58bafa3fb0ff6c0f55d95c63d8eefde1be441d8737be5d578c12`).
- Para continuar em outra máquina: `docs/RETOMADA.md` (o que copiar, `requirements.txt`, fontes, SHA de referência,
  o que estava só na memória do Claude). Nova ferramenta de pesquisa: `tools/research/label_widths.py`.

## 0.0.9 — 2026-10-08 (teste interno)

- **Todo o texto das tabelas do jogo em inglês**: campanha 6.822/6.822, menus 2.171/2.171, missões extras 457,
  tutorial 628, flashbacks 122, missões curtas 142, HUD, nomes e janelas do sistema. Os 150 lotes do agente estão
  aplicados.
- Extras revisados (mesmo ciclo das operações; cada proposta lida aqui antes de entrar): `xa` 76 correções,
  `xb`+`xd` 107, `xc` + menus 3000–3018 92, enciclopédia e menus 3019–3029 121, menus 3032–3057 110, menus
  3061–3077 121.
  - Enciclopédia (`menu3019`, 69 verbetes) e mensagens privadas (`menu3029`, 19 cartas) **retraduzidas por inteiro**:
    o agente resumiu, cortou parágrafos e inventou conteúdo (carta de Nina virou autoapresentação, Barkholz
    "fundador" do Design Bureau, Poseidal "com mão de ferro").
  - Linhas deslocadas (`m6006#23-25`, `m6302#140/141`), condições de falha traduzidas como ordem
    ("Destroy allied Aries"), falante errado nos flashbacks (`m6322#13`, `m6324#20`).
  - Botões: `決定` = "OK" (como `common`/`hud3013`), separadores com o espaço largo do japonês; `対戦` = Versus.
- Pipeline:
  - `validate_return.py --auto` reaplica as linhas automáticas de todos os grupos (172 linhas que ficavam de fora:
    `menu3023` e `menu3074` não têm lote, e cópias de linhas preenchidas depois do próprio grupo);
  - `agent/width_waivers.json`: dispensa registrada de largura provisória de menu (só `menu3077#54`, onde os dois
    nomes do glossário já ocupam o limite);
  - overrides novos em `auto/overrides.json`: `menu3002#3` "Recovery Dev.", `menu3013#5` "Player Unit".
- `merge_fill` lista 142 linhas WIDE (mais largas que a maior linha japonesa da tabela), quase todas nos objetivos
  copiados para `menu3055`/`menu3056`: `work/ui/wide_0.0.9.txt`. Conferir no jogo.
- 389 recursos alterados; `audit_iso.py` passou (SHA-256
  `3ec584ee6a6490687cf3671a144f20b48ef67dba7b88e7708cd14e65d8076da0`).

## 0.0.8 — 2026-10-08 (teste interno)

- **Campanha completa: Ops 01–28, 6.822 de 6.822 linhas de enredo.** Novas nesta build: Ops 22–28.
- O agente devolveu os 150 lotes. A única coisa fora de `returns/` foi um script dele (`apply_op23_02.ps1`), movido
  para `agent/_quarentena_google_0.0.8/`.
- Op 22: o agente "consertou" a linha extra de `op22_04` copiando o japonês e a tradução de `m6223#38` para a
  `m6223#37`. A linha foi retraduzida pelo revisor (`reviewer_fixes.json`) em vez de voltar ao agente.
- Revisão de sentido em paralelo (3 revisores para as Ops 23–28), com cada proposta lida aqui antes de entrar:
  Op 22 2, Ops 23–24 67, Op 25 204, Ops 26–28 94 correções. Problemas típicos: sentido invertido
  (`brief63300#3` "zero damage confirmed", `m6252#13`, `m6272#15`), hipóteses viradas em fato, nomes que passavam
  pelo validador só por um pedaço (Golaon, Baron Zu, Will Wips, Quincy Isser), "戦域" = airspace, frases de
  relatório truncadas, falas sem contração.
- Créditos (`m6285`): mojibake `ã€€` (espaço largo gravado como cp1252) consertado em 1.436 lugares; cargos em
  inglês, nomes em Hepburn com vogais longas, BANPRESTO/FromSoftware/Sunrise; "五十音順" = Japanese kana order.
- Pipeline:
  - `validate_return.py --all` e `review_returns.py` agora pegam todos os lotes (antes só `op*`, os extras ficavam
    de fora);
  - `merge_fill.widths` não quebra mais com caractere fora do cp932 (o validador o reporta como erro);
  - `#i…#i` (nomes de patente em `menu3001`) é código de controle (`textdb.TOKEN` e os `STRIP`);
  - uma linha reescrita pelo revisor ignora campos congelados alterados na entrega (vira aviso), como na `op22_04`.
- 339 recursos alterados; `audit_iso.py` passou (SHA-256
  `8326913d37c982445b9e0b3fe6ac73ef69cc4cb1145950dc49cd0ad215626401`).

### Preparação (sessão anterior)

- Lotes para o texto fora das 28 operações (`batches.py make --extras`), no mesmo formato, com o mesmo validador e
  as mesmas regras. São 57 lotes e 4.108 linhas:
  - `xa`: missões extras (6 lotes);
  - `xb`: tutorial (4);
  - `xc`: flashbacks Tak × Marina (2);
  - `xd`: missões curtas e de sistema (2);
  - `xm_menuNNNN`: telas de menu, enciclopédia e mensagens (43).
- Os grupos extras ganharam linhas automáticas próprias (`auto/<grupo>.json`) e congelamento por `hand`. O
  validador acha as linhas automáticas pelo nome do grupo do lote.
- Entregues ao agente: Ops 23–28 (22 lotes) e os 57 lotes extras. A Op 22 aguarda 2 consertos estruturais.
- Documentação para continuar em outra sessão: ESTUDO, seção 8 (reescrita) e `docs/REVISAO_PARALELA.md` (prompt
  dos revisores).

## 0.0.7 — 2026-10-08 (teste interno)

- **Operações 09 a 21 completas** (3.164 linhas). Com as Ops 01–08, são 4.832 de 6.822 linhas de enredo aplicadas.
- Revisão de sentido feita por três revisores em paralelo (Ops 09–13, 14–18, 19–22). Cada proposta foi lida e
  aceita aqui antes de entrar em `agent/reviewer_fixes.json`, e conferida por `tools/ace2/check_fixes.py`
  (novo: testa propostas sem gravar nada).
  - 348 correções: 95 nas Ops 09–13, 130 nas Ops 14–18 e 123 nas Ops 19–22.
  - Problemas típicos:
    - hipóteses (らしい, ようだ, であろう, 推測される) viradas em fato;
    - insultos inventados ("bastards", "scum", "half-breed", "fools", "runts");
    - orações perdidas (軍務に復帰, 軍属, 建造中, 人質をとって);
    - termos errados (犯行声明 = claim of responsibility; 戦略的 = strategic; 誤射 ≠ misfire);
    - frases divididas quebradas;
    - falas sem contração;
    - "-chan"/"-san" em romaji;
    - "he" para pilotos ainda não identificados.
- Pipeline:
  - `％` largo: um `%` ASCII solto vira início de conversão de printf. 7 linhas corrigidas, uma delas já na 0.0.6
    (6082#29). O validador agora barra `%` solto.
  - Objetivos divididos em duas linhas (…を / 掃討する) recebiam a cópia automática de outra operação ("military
    units"). Novo `work/translation/auto/overrides.json` dá inglês próprio a essas linhas (Ops 14, 18 e 22).
- Decisão provisória: 地上人 = "Upper Earthling" (Dunbine).
- Op 22 fica para a próxima build: o agente acrescentou uma linha a `op22_04` e alterou um campo `phase` em
  `op22_02`; a correção já foi pedida.
- 286 recursos alterados; `audit_iso.py` passou (SHA-256
  `a1853fe7ceec93aeaecdfb1ae21c654573239df5875955bfca7003247b94c366`).

## 0.0.6 — 2026-10-07 (teste interno)

- **Operações 03 a 08 completas**, em todas as camadas (1.221 linhas):
  - Op03 Novis Noah;
  - Op04 Kimbareid;
  - Op05 Guardian;
  - Op06 Konpei Island;
  - Op07 La Vie en Rose;
  - Op08 Interception Limit.
  Junto com as Ops 01 e 02, são 1.668 linhas de enredo aplicadas.
- Tradução do agente externo, validada (`validate_return.py`) e revisada linha a linha aqui: 56 correções em
  `agent/reviewer_fixes.json`.
  - Op03: 7. Op04: 7. Op05: 10. Op06: 10. Op07: 5. Op08: 17.
  - Erros de sentido corrigidos, entre outros:
    - objetivo dividido em duas linhas traduzido como dois objetivos soltos (63005#2/#3);
    - 星の屑 = Operation Stardust;
    - hipótese que virou afirmação (63216#4);
    - "Amuro Rei" (6082#36);
    - "that guy" para a piloto ainda não revelada (6032#31);
    - frases de relatório truncadas (63205#1, 63212#3/#5, 63213#6);
    - insultos acrescentados ("scum", "bastard", "fools");
    - Kou e Nina sem contrações.
- Bug do glossário corrigido:
  - レイ (Rei, o computador da Layzner) casava dentro de アムロ・レイ e ia para o glossário do lote. Foi isso que
    levou o agente a escrever "Amuro Rei".
  - Agora um nome do glossário dentro de um nome mais longo não conta (`validate_return.longer_keys`), tanto na
    validação quanto na geração dos lotes.
  - Nova regra em `name_fixes.json`: "Amuro Rei" → "Amuro Ray".
- 195 recursos alterados; `audit_iso.py` passou (SHA-256
  `874de9a95ad6bd03412e618e584f8a2da3a82d28ecb7823c6ac77466d6c99bff`).

## 0.0.5 — 2026-10-07 (teste interno)

- HUD completo: `hud3024` (38 linhas) traduzido. É a segunda cópia, em 38004, da lista de comandos `hud3020`; usa
  exatamente as mesmas traduções aprovadas na 0.0.2 (Ability, Weapon, Combo, Sub Combo, Purge, Pursuit Combo,
  "Hold ① + □"...).
  - A linha "Hold ① + □□□□□" tem 198 px num limite de 197, igual à da `hud3020`; conferir no jogo.
- 144 recursos alterados; `audit_iso.py` passou (SHA-256
  `54017e959c6412564c46ec974cf59daa3b99f172213cb25c72cb71a290411319`).

- O agente externo entregou 16 lotes (`op03_01` … `op08_01`) sem parar entre eles. Nada foi aplicado ainda.
  - Validador: 9 aprovados e 7 rejeitados (29 erros).
  - A partir da Op 05 as notas e a leitura de contexto caíram; essas entregas precisam de revisão mais minuciosa
    (ESTUDO, seção 8.1).
- `batches.py hand <LOTE>` registra o lote entregue ao agente (`agent/handed.json`). Uma operação entregue ou
  devolvida fica congelada: o `make` não reescreve mais os lotes nem as linhas automáticas dela, porque os limites
  dos lotes mudam quando a memória de tradução cresce.
- ESTUDO, seção 8: estado atual, receita do ciclo de um lote, regras aprendidas, fila de trabalho, decisões
  pendentes e escopo restante fora das operações.

## 0.0.4 — 2026-10-06 (teste interno)

- Material de contexto para o tradutor, como no ACE1:
  - `work/translation/agent/INDICE.md`: premissa, facções, enredo das 28 operações (lido do texto japonês, com
    referências `tabela#linha`), tom e voz por série e por personagem, pistas de contexto dos lotes, pontos sensíveis
    (spoilers, gênero ambíguo) e exemplos aprovados;
  - `work/translation/agent/GLOSSARIO.md` (`tools/ace2/agent_docs.py`): os 450 nomes e termos que existem no texto do
    jogo, por categoria e série, com forma curta, gênero, papel e voz;
  - PLANO e PROMPT agora mandam ler INDICE e GLOSSARIO antes de cada lote.
- Terminologia das séries: 89 termos pesquisados com fonte (`research/series_terms.json`), entre eles Aura Battler,
  Aura Power, Protoculture, GERWALK, Chulip, Distortion Field, Kimbareid, Hyper Mode e Antibody, além do vocabulário de
  sistema do ACE3 (Ace Points, Module, Free Mission...). As formas sem ponto que o jogo usa (グラビティブラスト,
  アンチボディ) agora são reconhecidas.
- Correção no glossário: entravam personagens do ACE3 de séries que não estão no ACE2 (Eureka Seven, Gundam X, King
  Gainer, Getter, Turn A, SEED, Macross Plus). Saíram 50 nomes e 34 formas curtas.
  - Bug visível: o rótulo de quem fala レイ (hud3021) estava "Ray" (Ray Beams, Eureka Seven) desde a 0.0.2. Agora é
    **"Rei"**, o computador da Layzner (como no ACE1).
  - O glossário de cada lote passou a respeitar o limite da palavra em katakana (レイ não casa mais dentro de
    リクレイマー ou ドレイク).
- Retratos de briefing: os 19 identificados (36 Noin, 41 Global, 43 Tak, 46 Amuro, 49 Nina, 55 operador da ponte).
- Lotes 03–28 regenerados com o glossário novo. A Op 02 aprovada foi conferida contra a terminologia nova, sem
  divergências.
- Decisões provisórias, pendentes do dono do projeto: ナナフシ = Nanafushi; トランスユニット = Trans Unit;
  Ｄ兵器 = D-weapons; ダンコフ = Dankova (só a MAHQ); 聖戦士 = Holy Warrior na fala; ボドル基艦 = Boddole Flagship.
- 144 recursos alterados; `audit_iso.py` passou (SHA-256
  `1db3c02d1182c0ab16ff8d58916f5d3dc0ef35d289dc23b954a30ada0341af34`).

## 0.0.3 — 2026-10-06 (teste interno)

- Operação 02 completa, em todas as camadas (190 linhas):
  - briefing estratégico 63001;
  - táticos 63033 e 63034;
  - missões 6021 e 6022;
  - debriefing 63169;
  - relatório 63200.
- Tradução feita pelo agente externo (lotes `op02_01` a `op02_03`), validada e revisada aqui:
  - 187 linhas entregues, 3 lotes APROVADOS (`work/translation/agent/validation/`);
  - 30 correções do revisor (`agent/reviewer_fixes.json`):
    - 14 de sentido, entre elas: Zeon e Giganos "ambos" defendendo a autonomia (63200#4); "Severing" inventado
      (6022#35); 報奨金 = reward, não bounty (6021#48); あえて omitido (63200#6); frases truncadas (63001#10,
      6021#12, 6022#57);
    - 16 compactações para caber no limite de linhas.
  - 6 propostas de glossário aceitas (`work/glossary/research/agent_proposals.json`).
- Incidente: o agente aplicou a própria tradução, alterou `merge_fill.py`, gerou uma ISO 0.0.3 e reescreveu este
  CHANGELOG.
  - Tudo isso foi para `work/translation/agent/_quarentena_google_0.0.3/`, e a árvore voltou ao estado da 0.0.2.
  - A Op 01 e as tabelas compartilhadas foram conferidas e estavam intactas.
  - Esta 0.0.3 foi refeita pelo pipeline.
- Procedimento do ACE1 adotado (regra em `AGENTS.md`):
  - `work/translation/agent/` com `batches/`, `returns/`, `validation/`, `review/`, `PLANO.md`, `PROMPT_AGENTE.md`,
    `LOTES.md` e `examples/op01.json`;
  - o agente só grava em `returns/`;
  - `tools/ace2/validate_return.py` (validação + `--apply`) e `tools/ace2/review_returns.py` (revisão) substituem o
    antigo `batches.py apply`.
- Limite de linhas por janela, tirado do próprio jogo:
  - fala de missão: 2 linhas;
  - briefing: 3 linhas (nenhuma das 1.281 falas de briefing em japonês passa disso; a Op 01 também não);
  - a regra antiga "japonês + 1" permitia 4 linhas no briefing.
- Lotes regenerados para as Ops 03–28:
  - `<on()>` agora conta como janela nova;
  - cada linha traz a lista `tokens`;
  - 5.957 linhas a traduzir; 248 já traduzidas e 360 repetições são preenchidas automaticamente
    (`work/translation/auto/`).
- 144 recursos alterados; `audit_iso.py` passou (SHA-256
  `c1cd08f6676e289b8bd068ebcbd456efe40a72b6910e5c1ab4e2cacfae1774c7`).


## 0.0.2 — 2026-10-02 (teste interno)

- Operação 01 completa, em todas as camadas:
  - briefing estratégico 63000;
  - **briefings táticos de cada fase** 63028 e 63029;
  - missões 6011 e 6012 (e as gêmeas 42011 e 42012);
  - debriefing 63168;
  - relatórios da Preventer 63196 e 63197, com a assinatura alinhada à direita.
- Nomes:
  - de quem fala, nas missões (hud3021, 118) e nos briefings (menu3014, 83);
  - todas as 89 unidades da mira (unit_names), em todos os contêineres de missão.
- Interface:
  - menu de pausa, resultados e legenda do mapa (hud3013);
  - lista de comandos (hud3020);
  - títulos, rodapé e locais do briefing (menu3010).
- Glossário: 319 entradas pesquisadas, com fonte, em `work/glossary/research/`, fundidas com o glossário do ACE3 em
  `work/glossary/names.json`. Nos conflitos vale a grafia do ACE3.
- Patentes: 少尉 Ensign, 中尉 Lieutenant, 大尉 Captain (Gundam Wiki); Gato = Major; Cowen = Commodore (o jogo diz
  准将).
- Grafias da wiki aplicadas por script e reversíveis (`work/glossary/name_fixes.json`):
  - Tak (antes Tack);
  - Sinapus;
  - Barkholz;
  - Giganos.
- Limites de largura medidos: briefing 430 px (pela captura da 0.0.1); falas 380 px (provisório).
- 139 recursos alterados; `audit_iso.py` passou.

## 0.0.1 — 2026-10-02 (teste interno, não testado no jogo)

- Base: Special Vocal Version (SLPS-25829) intacta; `MOVIE001.PSS` da edição original de 2006 (abertura "Glorious").
- Fontes: ASCII imprimível completado nas 4 fontes (2500 gameplay 19 px e 21 px, 2500 menus, 2501 HUD), em todos os
  13 pacotes. Nenhum glifo original alterado. Na fonte de 21 px, `@` ficou de fora por falta de espaço.
- Texto: janelas do sistema (`common`, 3 cópias), briefing da Operação 01 (`brief63000`), Operação 01-1 completa
  (`m6011` → contêineres 6011 e 42011) e o nome "Gun Ark".
- Briefing com linhas propositalmente largas, para medir a caixa no jogo.
- `DATA.BIN` +47 KB; os arquivos seguintes foram deslocados; ISO9660 e UDF reescritos. A auditoria (`audit_iso.py`)
  passou.
