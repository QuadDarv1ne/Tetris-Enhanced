#!/usr/bin/env python3
"""Проверяет, какие зависимости из requirements.txt реально импортируются."""
import ast, os

targets = [
    'tetris_enhanced.py', 'tetris_enhanced_fixed.py',
    'game_config.py', 'config_manager.py', 'ui_components.py',
]
for d in ('game', 'ui', 'utils'):
    for root, _, fs in os.walk(d):
        for f in fs:
            if f.endswith('.py'):
                targets.append(os.path.join(root, f))

found = {}
for path in targets:
    tree = ast.parse(open(path, encoding='utf-8').read())
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                found.setdefault(a.name.split('.')[0], set()).add(path)
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            found.setdefault(n.module.split('.')[0], set()).add(path)

declared = ['pygame-ce', 'numpy', 'pillow', 'psutil']
for pkg in declared:
    alias = {'pygame-ce': 'pygame', 'pillow': 'PIL'}.get(pkg, pkg)
    users = sorted(found.get(alias, []))
    if not users:
        print(f'{pkg:12s}: НЕ ИСПОЛЬЗУЕТСЯ (alias={alias})')
    else:
        for u in users:
            print(f'{pkg:12s}: {u}')
