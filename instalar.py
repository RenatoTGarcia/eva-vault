#!/usr/bin/env python3
"""Cria a sua vault a partir do modelo e instala a skill-ponte `eva`.

    python instalar.py --destino "C:/Minha Vault" --nome "Ana"
    python instalar.py --destino ~/Minha-Vault --nome "Ana" --vault-nome "Cofre da Ana"

O que faz:
1. Copia a pasta vault/ deste repositório para --destino (que não pode existir com conteúdo).
2. Troca {{NOME}} e {{VAULT}} pelos seus valores em todos os .md e .yaml copiados.
3. Instala a ponte `eva` em cada pasta de skills (padrão: ~/.claude/skills e ~/.agents/skills),
   apontando para o caminho absoluto da vault.
4. Gera o índice e roda a auditoria.
Só usa a biblioteca padrão do Python 3.8+.
"""
import argparse, shutil, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TEXTO = {'.md', '.yaml', '.yml', '.jsonl'}


def preencher(pasta, valores):
    for arq in pasta.rglob('*'):
        if arq.is_file() and arq.suffix in TEXTO:
            t = arq.read_text(encoding='utf-8')
            for k, v in valores.items():
                t = t.replace('{{%s}}' % k, v)
            arq.write_text(t, encoding='utf-8', newline='\n')


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser(description='Cria a vault da Eva e instala a skill-ponte')
    p.add_argument('--destino', required=True, type=Path, help='pasta da nova vault (caminho absoluto de preferência)')
    p.add_argument('--nome', required=True, help='seu nome, usado nas regras da Eva')
    p.add_argument('--vault-nome', help='nome da vault (padrão: "<nome> Vault")')
    p.add_argument('--skills', type=Path, action='append',
                   help='pasta de skills onde instalar a ponte (repita a opção para várias). '
                        'Padrão: ~/.claude/skills e ~/.agents/skills')
    p.add_argument('--sem-ponte', action='store_true', help='só cria a vault, sem instalar a skill-ponte')
    a = p.parse_args()

    destino = a.destino.expanduser().resolve()
    if destino.exists() and any(destino.iterdir()):
        sys.exit(f'A pasta {destino} já existe e não está vazia. Escolha outra ou esvazie-a.')
    vault_nome = a.vault_nome or f'{a.nome} Vault'
    valores = {'NOME': a.nome, 'VAULT': vault_nome}

    shutil.copytree(AQUI / 'vault', destino, dirs_exist_ok=True)
    preencher(destino, valores)
    print(f'Vault criada em {destino}')

    skill_memoria = destino / '.agents' / 'skills' / 'eva-memory' / 'SKILL.md'
    if not a.sem_ponte:
        pastas = a.skills or [Path.home() / '.claude' / 'skills', Path.home() / '.agents' / 'skills']
        for base in pastas:
            alvo = base.expanduser().resolve() / 'eva'
            if alvo.exists():
                print(f'Pulando {alvo}: já existe uma skill eva aí (apague-a para reinstalar).')
                continue
            shutil.copytree(AQUI / 'ponte' / 'eva', alvo)
            preencher(alvo, dict(valores, CAMINHO_VAULT=str(destino), CAMINHO_SKILL=str(skill_memoria)))
            print(f'Ponte eva instalada em {alvo}')

    script = destino / '.agents' / 'skills' / 'eva-memory' / 'scripts' / 'eva_memory.py'
    subprocess.run([sys.executable, str(script), 'index'], check=True)
    r = subprocess.run([sys.executable, str(script), 'audit'])
    print('\nPronto. Abra a pasta no Obsidian ("Open folder as vault") e peça para a sua IA: "Eva, o que você sabe sobre mim?"'
          if r.returncode == 0 else '\nA auditoria encontrou problemas; veja a saída acima.')
    sys.exit(r.returncode)


if __name__ == '__main__':
    main()
