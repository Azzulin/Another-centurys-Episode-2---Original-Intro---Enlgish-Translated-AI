# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Tradução para o inglês de *Another Century's Episode 2 – Special Vocal Version* (PS2, SLPS-25829). A pasta não é
repositório git. As regras do projeto estão no AGENTS.md e valem integralmente:

@AGENTS.md

## Início de sessão

- Leia `docs/ESTUDO_ACE2.md` seção 8 (estado, fila de trabalho em 8.6, regras aprendidas em 8.5, erros típicos do
  agente em 8.4) e o topo de `docs/CHANGELOG.md`. Numa máquina nova, `docs/RETOMADA.md` primeiro.
- Os dois ISOs base ficam na raiz com os nomes exatos que `tools/ace2/ace2lib.py` procura (`BASE`,
  `ORIGINAL_RELEASE`). SHA-256 de referência em `docs/RETOMADA.md` seção 1.

## Comandos

Windows, Python 3.14 no `.venv` da raiz (o `python` solto abre a Microsoft Store). Rode da raiz do projeto
(`Ace 2`), sempre com `PYTHONIOENCODING=utf-8`, senão o console quebra no "①" e o `merge_fill` para no meio
deixando tabelas sem mesclar:

```
$env:PYTHONIOENCODING='utf-8'                                   # Git Bash: export PYTHONIOENCODING=utf-8
.venv\Scripts\python.exe tools\ace2\<script>.py ...
```

- Build: `build.py --version 0.0.N` (ensaio, não grava) / `--write` → `work/output/ACE2-EN-0.0.N.iso` + `.json`.
  Leva ~2 min e grava 3,6 GB. A próxima versão é a seguinte à do topo do CHANGELOG.
- Auditoria (obrigatória antes do emulador): `audit_iso.py work\output\ACE2-EN-0.0.N.iso` → termina em `PASS ... SHA`.
- Testes: scripts soltos, sem pytest; rode um por vez. `test_identity.py [--pack-all]` (reconstrução sem edição
  reproduz os bytes), `test_textdb.py` (estresse 1,5x em todas as tabelas, não grava ISO), `test_disc.py` (grava e
  apaga duas ISOs completas em `work/output/_test`; lento).
- Mesclar traduções: `merge_fill.py [--check]`. Larguras/rótulos: `tools\research\label_widths.py table|over|try|source`.
- Ciclo completo de um lote do tradutor externo: receita em `docs/ESTUDO_ACE2.md` 8.3. Resumo:
  `validate_return.py --all` → `review_returns.py <LOTE>` → correções em `agent/reviewer_fixes.json`
  (testar com `check_fixes.py <proposta.json>`) → `validate_return.py <LOTE> --apply` (a operação inteira) →
  `validate_return.py --auto` → `fix_names.py --write` → `merge_fill.py` → `build.py --write` → `audit_iso.py` → CHANGELOG.
- Onde corrigir uma linha já aplicada depende da origem (lote do agente, linha automática, preenchimento à mão):
  tabela em `docs/RETOMADA.md` seção 5.

## Arquitetura (`tools/ace2/`)

Camadas, de baixo para cima:

- `ace2lib.py` — formatos: ISO9660, índice do `DATA.BIN` (binder `BND`, payloads alinhados a 2048), binders internos,
  LZSS do ACE3, tabela de texto (ponteiros + pool CP932), contêiner de missão (+20 aponta a tabela de diálogo,
  registros de subtabelas). O docstring do topo é a referência de layout.
- `textdb.py` — descobre **todas** as tabelas andando pelo `DATA.BIN` recursivamente (sem lista fixa). Uma
  localização é uma string (`'6012:m'`, `'6012:s219'`, `'62050/3004'`, `'1234:lz/5'`); localizações são agrupadas em
  tabelas lógicas (`m####`, `brief#####`, `menu####`, `hud####`, `unit_names`, `common`). Linhas são chaveadas pelo
  **texto japonês**, então uma tradução chega a toda cópia com o mesmo texto. Na gravação, tabela que cresce é
  anexada e o ponteiro reapontado — nunca in-place.
- `disc.py` — regrava o disco: `DATA.BIN` cresce, arquivos seguintes andam para a sobra do fim do disco (tamanho da
  imagem não muda), ISO9660 (ambos endians) e UDF reescritos, troca do `MOVIE001.PSS` inteiro vindo do ISO de 2006,
  e reverificação de tudo antes de retornar.
- `fonts.py` — completa ASCII imprimível nos pares fonte/atlas (gameplay 38000–38006, menu 62050–62057) só em espaço
  livre; glifos novos renderizados da TTF de `C:\Windows\Fonts` que mais se parece com a nativa. **Por isso o SHA da
  build depende das fontes instaladas** (escolha registrada na chave `fonts` do relatório JSON).
- `validate.py` (`check_row`: tokens de controle na mesma ordem do japonês, CP932, sem fullwidth, quebras de linha)
  é compartilhado por `merge_fill`, `validate_return`, `check_fixes` e `build` — o build para se uma linha falhar.
- `build.py` junta: `work/translation/en/<tabela>.json` (campo `en`) + fontes + filme → `disc.write_disc`.
  `audit_iso.py` é independente do build: só lê a saída e compara com os bases.

Fluxo de dados da tradução: `export_text.py` gera `en/<tabela>.json`; traduções entram em
`en/_fill/<tabela>.json` (`{índice: inglês}`), por mão ou por `validate_return.py --apply` (lotes do agente +
`reviewer_fixes.json` + linhas automáticas `tm`/`repeat` de `work/translation/auto/`); `merge_fill.py` valida, mede
a largura em px com a fonte completada e mescla em `en/<tabela>.json`.

Organização por operação (`operations.py` → `work/translation/operations.json`): cada operação tem briefing
estratégico, táticos por fase, missões (contêiner `6###` e gêmeo `42###`), debriefing e relatórios. Lotes
(`batches.py`) seguem a ordem de jogo da operação inteira; uma operação entregue (`handed.json`) fica congelada e
`batches.py make` não a reescreve.

Nomes: `glossary.py --write` gera `work/glossary/names.json` (decisões > ACE3 > pesquisa). `glossary.py` e
`agent_docs.py` dependem de `D:\Ace 1`, que não existe mais; build, validação e revisão não dependem deles.
`tools/research/` é pesquisa, fora do build, e a maioria tem `D:\Ace 2` fixo no código.

## Limites de tela conhecidos

Missão 2 linhas/380 px; briefing e relatório 3 linhas/430 px; menus = maior linha japonesa da tela; rótulo de menu
acima de ~141 px não é desenhado (`work/ui/limits.json`). Detalhes e o que ainda é provisório: ESTUDO 8.5 e 8.7.
