---
name: valtx-gates
description: Ejecuta los gates de gobernanza Valtx SDD sobre este repo. Se invoca desde los hooks before_implement y after_implement de .specify/extensions.yml. Usar antes de escribir código en una feature y al terminarla.
---

# valtx-gates

Envuelve el CLI del motor: `sdd gates run --phase <fase> --json`.

Existe porque los hooks de spec-kit son **slash-commands, no comandos de shell**
(`IMPLEMENTATION.md` §6.4). Esta skill es lo que permite enganchar los gates sin forkear spec-kit.

## `valtx.gates.pre` — antes de implementar

1. Determina la fase: `implement`.
2. Ejecuta `sdd gates run --phase implement --json`.
3. Lee el resultado:
   - algún gate en **`block`** → **detén la implementación**, muestra el gate, su finding y su
     remediación, y no escribas código.
   - algún gate en `warn` o `sin_datos` → repórtalo y continúa.
   - todo en `pass` u `off` → continúa.

## `valtx.gates.post` — después de implementar

1. Ejecuta `sdd gates run --phase implement --json`.
2. Reporta el resultado completo. **No abortes**: el trabajo ya está hecho y el veredicto que
   cuenta lo emite la CI.

## Lo que esta skill NO hace

- **No publica el sobre al hub.** Eso lo hace la CI, que decide primero y publica después. Que un
  agente publique evidencia saltándose la CI rompe I3.
- **No decide el resultado de un gate.** Solo ejecuta el motor y transmite lo que dice.
- **No modifica `sdd.yaml` ni la constitución** para que un gate pase. Si un gate bloquea, la
  salida correcta es arreglar el código o pedir un waiver, nunca bajar el listón.

## Si `sdd` no está instalado

Dilo explícitamente y detén el hook. No lo trates como «gates en verde»: un gate que no corrió no
es un gate que pasó — es exactamente el fallo que la plataforma existe para impedir.
