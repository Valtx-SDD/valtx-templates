# valtx-templates

Las seis plantillas de las que nace todo repo gobernado por Valtx SDD.

| Plantilla | `repo.role` | Para qué |
|---|---|---|
| `project-arch` | `arch` | El repo de arquitectura de un proyecto multi-repo: ADR, contratos, diseño y stack. Sin código |
| `project-mono` | `mono` | Proyecto de un solo repo: specs, arquitectura y código juntos |
| `service-python` | `service` | Servicio de backend en Python |
| `service-go` | `service` | Servicio de backend en Go |
| `service-typescript` | `service` | Servicio de backend en TypeScript |
| `web-frontend` | `web` | Frontend |

## `_common/`

No es una plantilla: es el material que llevan **todas**. Hoy son cuatro
ficheros —el workflow de gates, `CODEOWNERS`, `.specify/extensions.yml` y el
README de `.sdd/`— y están copiados byte a byte dentro de cada plantilla.

La copia es deliberada. La provisión sube `_common/` + `<kind>/` en un único
commit por la API de Git (§7.4), así que cada plantilla tiene que ser
instanciable por sí sola; partir esto en seis repos template obligaría a un job
de sync y volvería real la duplicación que aquí es solo aparente.

Lo que la sostiene es la CI: `.github/workflows/ci.yml` falla si un fichero de
`_common/` difiere del que lleva cualquier plantilla. Editar `_common/` y
propagar es un paso, no una convención que alguien recuerde.

## Cómo se provisiona

No se usa `POST /repos/{owner}/{repo}/generate`: no sabe subir un
subdirectorio. El hub crea el repo vacío y sube el árbol en un commit
(blobs → tree → commit → ref), reescribiendo por encima los ficheros que
dependen del proyecto: `sdd.yaml`, `constitution.yaml` y `project.yaml`.

Por eso los valores `template-project` que verás en las plantillas son
placeholders con la **forma** correcta, no valores que sobrevivan a la
provisión. Una plantilla enseña la forma antes que el contenido.

## Comprobar que cumplen el estándar que reparten

```bash
pip install "valtx-sdd-core @ git+https://github.com/Valtx-SDD/valtx-sdd-core.git@v0.0.3"
python scripts/validar_plantillas.py            # las seis
python scripts/validar_plantillas.py service-go # una
```

Valida cada `sdd.yaml`, `constitution.yaml` y `project.yaml` contra los JSON
Schema del pack de `valtx-governance` resuelto — nunca contra una copia local,
que sería una segunda fuente de verdad (I1).

Las desviaciones que la plantilla no puede arreglar porque el defecto está en el
estándar se declaran en `DESVIACIONES`, dentro del propio script, cada una con
su motivo y su hito de cierre. Se reportan siempre; no bloquean. Una excepción
sin motivo escrito es un silencio.

## El workflow que se reparte

`_common/.github/workflows/sdd-gates.yml` corre **un job por fase** del ciclo
(`constitution`, `specify`, `plan`, `implement`, `merge`), que entre las cinco
cubren los 13 gates exactamente una vez. `tasks` no aparece: no tiene gates
asignados, y publicar un sobre sin gates sería registrar como limpio un run que
no comprobó nada.

Cada repo provisionado necesita dos cosas configuradas en la organización:

- `vars.VALTX_HUB_URL` — variable, no secreto. El dominio del hub no es secreto,
  y hornearlo en cada repo rompería I11.
- `secrets.VALTX_HUB_SECRET` — el mismo valor que `GATES_WEBHOOK_SECRET` en el
  hub. Sin él la ingesta responde 401 y el repo se queda sin evidencia.

Si falta la URL, la Action avisa y omite el envío: el veredicto de la CI no
depende de que el hub esté vivo (I3).
