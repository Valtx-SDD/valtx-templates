# `.sdd/`

Aquí vive `universe.lock.json`, el manifiesto del universo de artefactos del
repo: los REQ de las specs, los ADR y los contratos, con su estado.

**El fichero no viene en la plantilla, y es correcto que no venga.** Un
manifiesto vacío sería peor que ninguno: G3 marcaría como alucinación cada REQ
citado en el código, y el repo nacería bloqueado por artefactos que sí existen.

Sin manifiesto, G3, G5, G7 y G10 devuelven `sin_datos` con un mensaje que dice
exactamente eso — que no hay contra qué comparar — en vez de un `pass` que no
ha comprobado nada (ADR-001).

Para generarlo, una vez que el repo tenga specs, ADR o contratos:

```bash
sdd manifest build
sdd manifest check   # falla si el lock se ha quedado atrás
```

`sdd manifest check` es lo que conviene tener en la CI: el lock es la fuente
contra la que cinco gates validan citas, y uno desfasado los hace juzgar un
universo que ya no existe.
