"""
list_endpoints.py
==================
Descubre los endpoints reales disponibles en la instalación de OpenBB
actual, en vez de adivinar nombres que pueden haber cambiado entre versiones.

Uso:
    python .claude/skills/openbb-query/scripts/list_endpoints.py
    python .claude/skills/openbb-query/scripts/list_endpoints.py government
    python .claude/skills/openbb-query/scripts/list_endpoints.py equity.ownership
"""

from __future__ import annotations

import sys


def main():
    try:
        from openbb import obb
    except ImportError:
        print("OpenBB no está instalado en este entorno. Activa el venv e instala requirements.txt.")
        sys.exit(1)

    query = sys.argv[1] if len(sys.argv) > 1 else ""

    target = obb
    path_so_far = []
    if query:
        for part in query.split("."):
            path_so_far.append(part)
            if hasattr(target, part):
                target = getattr(target, part)
            else:
                print(f"No existe '{'.'.join(path_so_far)}' en esta instalación de OpenBB.")
                print("Atributos disponibles en el nivel anterior:")
                _print_members(obb if len(path_so_far) == 1 else target)
                sys.exit(1)

    print(f"Miembros disponibles bajo 'obb.{query}':" if query else "Miembros disponibles bajo 'obb':")
    _print_members(target)


def _print_members(obj):
    members = [m for m in dir(obj) if not m.startswith("_")]
    for m in sorted(members):
        print(f"  - {m}")


if __name__ == "__main__":
    main()
