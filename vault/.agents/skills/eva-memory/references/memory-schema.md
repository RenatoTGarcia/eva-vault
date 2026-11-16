# Schema de memória

## Memória viva

Use frontmatter com `type: eva-memory`, `status: active`, `confidentiality: private`, UUID, categoria, importância, datas, origem auditável, modo de captura, consolidação, substituições, tópicos, entidades, notas relacionadas e tags `eva/memory` e `eva/live`.

Nome: `AAAA-MM-DD__8_caracteres_do_uuid__Título legível.md`.

Categorias: `fact`, `preference`, `instruction`, `decision`, `context`. Importância: `high`, `medium`, `low`.

## Memória importada

Use `status: imported`, IDs originais, datas, arquivo e hashes de origem, `immutable_source: true`, mantendo texto e justificativa sem reescrita.
