"""Comprueba que cada plantilla cumple el estándar que reparte.

`valtx-templates` no tenía CI propio: sus workflows viven dentro de cada
plantilla (`<plantilla>/.github/workflows/`), no en la raíz, así que ninguna PR
contra este repo ejecutaba nada. Por eso `extends: template-project@latest`
—que no valida contra el schema y apunta a una constitución inexistente—
sobrevivió en cuatro plantillas hasta que un comando del motor lo destapó.

Una plantilla que no cumple el estándar reparte el incumplimiento a cada repo
que nace de ella. Esto lo comprueba antes de repartirlo.

Uso::

    python scripts/validar_plantillas.py            # todas
    python scripts/validar_plantillas.py service-go # una
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from valtx_sdd.governance.resolver import resolve_governance
from valtx_sdd.governance.schema import SchemaNoDisponible, validate_document

RAIZ = Path(__file__).resolve().parent.parent

# Los ✓/✗ salen ilegibles en una consola Windows con cp1252 y, peor, revientan
# el script con UnicodeEncodeError. Es el mismo arreglo que hace `valtx_sdd.cli`.
for _flujo in (sys.stdout, sys.stderr):
    if hasattr(_flujo, "reconfigure"):
        _flujo.reconfigure(encoding="utf-8", errors="replace")

# `_common` no es una plantilla instanciable: es el material que se copia dentro
# de las demás, y no tiene `sdd.yaml` propio.
PLANTILLAS = sorted(
    p.name for p in RAIZ.iterdir() if p.is_dir() and (p / "sdd.yaml").is_file()
)

# Incumplimientos que la plantilla **no puede** arreglar porque el defecto está
# en el estándar. Se reportan siempre y no tumban la CI, pero cada uno tiene que
# traer su motivo y su hito de cierre: es el mismo trato que `sdd.yaml` le da a
# un gate en `off`. Una excepción sin motivo escrito es un silencio.
#
# Clave: (plantilla, fichero, fragmento del mensaje de error).
DESVIACIONES: dict[tuple[str, str, str], str] = {
    ("project-arch", "sdd.yaml", "'code' is a required property"): (
        "un repo `-arch` no tiene código —solo ADR, contratos, diseño y stack— pero "
        "`sdd-config.schema.json` exige `code` con minItems 1, y el enum de `lang` "
        "(python, typescript, javascript, go, java, sql) no admite nada que un repo de "
        "arquitectura pueda declarar sin mentir. Lo arregla el estándar haciendo `code` "
        "condicional a `repo.role`. Cierra: próximo release de valtx-governance"
    ),
}


def _cargar(path: Path) -> dict:
    datos = yaml.safe_load(path.read_text(encoding="utf-8"))
    return datos if isinstance(datos, dict) else {}


def _motivo_de(nombre: str, fichero: str, error: str) -> str | None:
    for (plantilla, doc, fragmento), motivo in DESVIACIONES.items():
        if plantilla == nombre and doc == fichero and fragmento in error:
            return motivo
    return None


def revisar(nombre: str) -> tuple[list[str], list[str]]:
    """``(errores, desviaciones)``. Sin errores = la plantilla cumple."""
    raiz = RAIZ / nombre
    errores: list[str] = []
    desviaciones: list[str] = []

    cfg = _cargar(raiz / "sdd.yaml")
    fuente = str((cfg.get("governance") or {}).get("source") or "")
    if not fuente:
        return [f"{nombre}/sdd.yaml no declara `governance.source`"], []

    gov = resolve_governance(fuente)
    if gov.error:
        return [f"{nombre}: no se pudo resolver la gobernanza ({gov.error})"], []

    # Cada documento contra el schema del estándar, nunca contra una copia
    # local: si el schema cambia, esto tiene que enterarse (I1).
    for fichero, schema in (
        ("sdd.yaml", "sdd-config.schema.json"),
        ("constitution.yaml", "constitution.schema.json"),
        ("project.yaml", "project.schema.json"),
    ):
        path = raiz / fichero
        if not path.is_file():
            continue
        try:
            fallos = validate_document(_cargar(path), gov.path, schema)
        except SchemaNoDisponible as exc:
            # No se puede comprobar ≠ correcto (ADR-001).
            errores.append(f"{nombre}/{fichero}: {exc}")
            continue
        for fallo in fallos:
            motivo = _motivo_de(nombre, fichero, fallo)
            destino = desviaciones if motivo else errores
            detalle = f" — {motivo}" if motivo else ""
            destino.append(f"{nombre}/{fichero} · {fallo}{detalle}")

    return errores, desviaciones


def main(argv: list[str]) -> int:
    objetivo = argv[1:] or PLANTILLAS
    desconocidas = [p for p in objetivo if p not in PLANTILLAS]
    if desconocidas:
        print(f"No son plantillas: {', '.join(desconocidas)}", file=sys.stderr)
        return 2

    total: list[str] = []
    conocidas: list[str] = []
    for nombre in objetivo:
        fallos, desviaciones = revisar(nombre)
        icono = "✗" if fallos else ("~" if desviaciones else "✓")
        print(f"{icono} {nombre}")
        for f in fallos:
            print(f"    ✗ {f}", file=sys.stderr)
        for d in desviaciones:
            print(f"    ~ {d}")
        total += fallos
        conocidas += desviaciones

    if conocidas:
        print(
            f"\n{len(conocidas)} desviación(es) conocida(s) del estándar, con motivo "
            "declarado en DESVIACIONES. No bloquean, pero tampoco se olvidan."
        )
    if total:
        print(f"\n{len(total)} problema(s) en las plantillas.", file=sys.stderr)
        return 1
    print(f"\nLas {len(objetivo)} plantillas cumplen el estándar que reparten.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
