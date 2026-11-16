#!/usr/bin/env python3
"""Importa um histórico de memórias (CSV) para 08 - Eva/01 - Memórias Importadas, sem reescrever as fontes.

Colunas aceitas: title, text, category, importance, last_modified, reason (ou justification), memory_id (opcional).
Exemplo em exemplos/memorias-exemplo.csv.

    python import_eva_csv.py historico.csv --vault "/caminho/da/vault" --dry-run
"""
import argparse, csv, hashlib, json, sys, uuid
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser(description='Importa export histórico da Eva sem reescrever fontes')
    p.add_argument('csv_file', type=Path)
    p.add_argument('--vault', type=Path, required=True)
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()
    raw = args.csv_file.read_bytes()
    source_hash = digest(raw)
    rows = list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
    target = args.vault / '08 - Eva' / '01 - Memórias Importadas'
    if not args.dry_run:
        target.mkdir(parents=True, exist_ok=True)
    manifest = []
    for index, row in enumerate(rows, 1):
        canonical = json.dumps(row, ensure_ascii=False, sort_keys=True).encode('utf-8')
        record_hash = digest(canonical)
        memory_id = row.get('memory_id') or str(uuid.uuid5(uuid.NAMESPACE_URL, record_hash))
        title = (row.get('title') or f'Memória importada {index}').replace('/', '-').replace('\\', '-')
        filename = f'{index:06d}__{memory_id}__{title[:80]}.md'
        text = row.get('text', '')
        reason = row.get('reason', row.get('justification', ''))
        body = f'''---
type: eva-memory
status: imported
confidentiality: private
memory_id: "{memory_id}"
category: "{row.get('category', 'fact')}"
importance: "{row.get('importance', 'medium')}"
last_modified: "{row.get('last_modified', '')}"
source: "{args.csv_file.name}"
source_sha256: "{source_hash}"
record_sha256: "{record_hash}"
immutable_source: true
topics: []
entities: []
tags: [eva/memory]
---

# {title}

> Fonte histórica e imutável. Correções devem ser registradas em Memória Viva.

{text}

## Justificativa original

{reason}
'''
        manifest.append({'file': filename, 'memory_id': memory_id, 'record_sha256': record_hash})
        if not args.dry_run:
            (target / filename).write_text(body, encoding='utf-8')
    print(json.dumps({'source_sha256': source_hash, 'records': len(rows), 'manifest': manifest}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
