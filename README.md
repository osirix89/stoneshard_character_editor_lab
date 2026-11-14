# Stoneshard Character Lab v0.5

Editor experimental local para partidas de Stoneshard.

## Guardar el archivo editado

1. Cerrá Stoneshard.
2. Abrí el personaje y editá los campos que quieras.
3. Pulsá el botón verde **GUARDAR data.sav (Ctrl+S)**, que está inmediatamente debajo del título y por encima de las pestañas.
4. Confirmá el guardado. El programa escribe directamente sobre el `data.sav` que cargaste y crea/actualiza `data.sav.bak` como respaldo.
5. El programa vuelve a leer el archivo y comprueba el checksum antes de confirmar que se guardó.

Este botón guarda el `data.sav` editado directamente; no crea un ZIP ni un personaje nuevo. Si preferís no sobrescribir el archivo cargado, usá **GUARDAR PERSONAJE PARA EL JUEGO** para crear una carpeta `character_N` separada.

## Otras funciones

- Catálogo inicial con identificadores detectados en los saves de Dirwin y Jonna.
- Edición de identidad, apariencia, atributos, progresión, perks, habilidades y JSON avanzado.
- Clonación opcional a un nuevo `character_N`.
- Exportación opcional a ZIP con respaldo.

## Ejecutar

Requisitos: Python 3.10+ y Tkinter. En Debian/Ubuntu: `sudo apt install python3-tk`.

Desde la carpeta del proyecto:

```bash
./run.sh
```

Alternativamente: `python3 run.py`.

**Importante:** cerrá Stoneshard antes de escribir el save. El checksum correcto confirma la integridad del formato, pero la aceptación del personaje debe comprobarse dentro del juego.
