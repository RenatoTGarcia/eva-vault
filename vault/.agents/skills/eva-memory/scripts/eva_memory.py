#!/usr/bin/env python3
"""Memória canônica da Eva: search, context, capture, index e audit.

Uso (sempre com caminhos absolutos):
    python eva_memory.py search "termos da busca"
    python eva_memory.py context "termos" --max-chars 8000
    python eva_memory.py capture --title "..." --text "..." --category decision --importance high --source "conversa de 2026-11-16"
    python eva_memory.py index
    python eva_memory.py audit

A raiz da vault é descoberta pela posição deste arquivo
(<vault>/.agents/skills/eva-memory/scripts/eva_memory.py); use --vault para apontar outra.
"""
import argparse, json, re, sys, uuid
from datetime import date
from pathlib import Path

SKIP = {'.obsidian', '.agents', '.git'}
EVA = '08 - Eva'
VIVA = Path(EVA, '03 - Memória Viva')
IMPORTADAS = Path(EVA, '01 - Memórias Importadas')
INDICE = Path(EVA, '90 - Operação', 'indice-memorias.jsonl')
OBRIGATORIOS = [
    'AGENTS.md', 'Bem-vindo.md', '00 - Início', '01 - Identidade', '02 - Estratégia', '03 - Execução',
    '04 - Portfólio', '05 - Aprendizado', '06 - Revisões', '07 - Diário', EVA, '90 - Templates',
    '99 - Referências', '.agents/skills/eva-memory/SKILL.md', INDICE.as_posix(),
]
CAMPOS_VIVA = ('memory_id', 'category', 'importance', 'source', 'consolidation_status')


def vault_root():
    return Path(__file__).resolve().parents[4]


def markdown_files(root):
    return [p for p in root.rglob('*.md') if not any(x in SKIP for x in p.relative_to(root).parts)]


def frontmatter(text):
    """Lê os campos simples (chave: valor) do frontmatter YAML, sem dependências externas."""
    m = re.match(r'^---\n(.*?)\n---\n', text, flags=re.S)
    campos = {}
    if m:
        for linha in m.group(1).splitlines():
            if ':' in linha and not linha.startswith((' ', '-')):
                k, v = linha.split(':', 1)
                campos[k.strip()] = v.strip().strip('"')
    return campos


def search(root, query):
    terms = query.casefold().split()
    hits = []
    for path in markdown_files(root):
        text = path.read_text(encoding='utf-8')
        score = sum(text.casefold().count(t) for t in terms)
        if score:
            hits.append((score, path, text))
    return sorted(hits, key=lambda x: (-x[0], str(x[1])))


def safe_title(value):
    value = re.sub(r'[<>:"/\\|?*]', '', value).strip()
    return re.sub(r'\s+', ' ', value)[:100] or 'Memória'


def capture(root, args):
    memory_id = str(uuid.uuid4())
    today = date.today().isoformat()
    title = safe_title(args.title)
    path = root / VIVA / f'{today}__{memory_id[:8]}__{title}.md'
    body = f'''---
type: eva-memory
status: active
confidentiality: private
memory_id: "{memory_id}"
category: "{args.category}"
importance: "{args.importance}"
created: {today}
updated: {today}
source: "{args.source.replace('"', "'")}"
capture_mode: {args.capture_mode}
consolidation_status: pending
supersedes: []
topics: []
entities: []
related_notes: []
tags:
  - eva/memory
  - eva/live
---

# {title}

{args.text}

## Conexões canônicas

- Pendente de consolidação
'''
    path.write_text(body, encoding='utf-8')
    print(path)


def index(root):
    """Regenera o índice derivado (uma linha JSON por memória viva ou importada)."""
    linhas = []
    for pasta in (VIVA, IMPORTADAS):
        for path in sorted((root / pasta).glob('*.md')):
            fm = frontmatter(path.read_text(encoding='utf-8'))
            if fm.get('type') != 'eva-memory':
                continue
            titulo = path.stem.split('__')[-1]
            linhas.append({'memory_id': fm.get('memory_id', ''), 'date': fm.get('created') or fm.get('last_modified', ''),
                           'category': fm.get('category', ''), 'importance': fm.get('importance', ''),
                           'status': fm.get('status', ''), 'title': titulo, 'path': path.relative_to(root).as_posix()})
    destino = root / INDICE
    destino.write_text(''.join(json.dumps(l, ensure_ascii=False) + '\n' for l in linhas), encoding='utf-8')
    print(json.dumps({'indice': str(destino), 'memorias': len(linhas)}, ensure_ascii=False))


def audit(root):
    missing = [item for item in OBRIGATORIOS if not (root / item).exists()]
    malformed = []
    for path in (root / VIVA).glob('*.md'):
        if path.name == 'LEIA-ME.md':  # nota explicativa da pasta, nao e memoria
            continue
        fm = frontmatter(path.read_text(encoding='utf-8'))
        malformed += [f'{path.name}: sem {k}' for k in CAMPOS_VIVA if not fm.get(k)]
    result = {'vault': str(root), 'missing': missing, 'malformed_live_memories': malformed,
              'critical_errors': len(missing) + len(malformed)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result['critical_errors'] else 0


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='Memória canônica da Eva')
    parser.add_argument('--vault', type=Path, default=vault_root())
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('search'); p.add_argument('query')
    p = sub.add_parser('context'); p.add_argument('query'); p.add_argument('--max-chars', type=int, default=8000)
    p = sub.add_parser('capture')
    p.add_argument('--title', required=True); p.add_argument('--text', required=True)
    p.add_argument('--category', choices=['fact', 'preference', 'instruction', 'decision', 'context'], required=True)
    p.add_argument('--importance', choices=['high', 'medium', 'low'], required=True)
    p.add_argument('--source', required=True)
    p.add_argument('--capture-mode', choices=['automatic', 'explicit'], default='explicit')
    sub.add_parser('index')
    sub.add_parser('audit')
    args = parser.parse_args()
    root = args.vault.resolve()
    if not root.is_dir():
        sys.exit(f'Vault indisponível: {root}')
    if args.command == 'audit':
        sys.exit(audit(root))
    if args.command == 'capture':
        capture(root, args); return
    if args.command == 'index':
        index(root); return
    hits = search(root, args.query)
    if args.command == 'search':
        for score, path, _ in hits:
            print(f'{score}\t{path.relative_to(root).as_posix()}')
    else:
        remaining = args.max_chars
        for score, path, content in hits:
            if remaining <= 0:
                break
            block = f'\n===== {path.relative_to(root).as_posix()} | score={score} =====\n{content}\n'
            print(block[:remaining], end='')
            remaining -= len(block)


if __name__ == '__main__':
    main()
