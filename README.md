# Stoneshard Character Lab

**Experimental desktop save editor for Stoneshard**  
**Version:** 0.5.0

**Made in Argentina 🇦🇷 by antuankerbage — osirix89**

[English](#english) | [Español](#español)

---

# English

## About

**Stoneshard Character Lab** is an experimental desktop application for inspecting, editing, validating, and managing Stoneshard character save files.

The project was developed as a local research and experimentation environment for understanding the game's save structure, testing character data modifications, and exploring the possibilities of save editing.

It is a standalone Python desktop application. It does not require a web server or an online account.

## Features

- Load a complete `character_N` save folder or an individual `data.sav` file.
- Inspect character save slots, including autosaves and exit saves.
- Edit character identity and appearance fields.
- Modify character attributes and progression.
- Manage perks and learned skills.
- Inspect and edit advanced JSON data.
- Compare a save with another character save.
- Copy selected data between saves.
- Scan save folders and ZIP archives for identifiers.
- Import and export catalog data.
- Validate save structure and checksum.
- Save changes directly to the loaded `data.sav`.
- Clone an edited character into a separate `character_N` folder.
- Export save data in a ZIP archive with a backup.
- View diagnostic information and application logs.

The available fields depend on the save structure and the data exposed by the application.

## Requirements

- Python 3.10 or newer.
- Tkinter.
- No third-party Python packages are required for normal application use.

### Install Tkinter

On Debian or Ubuntu:

```bash
sudo apt update
sudo apt install python3 python3-tk
```

On Fedora:

```bash
sudo dnf install python3-tkinter
```

On Arch Linux:

```bash
sudo pacman -S tk
```

## Run the application

Clone the repository:

```bash
git clone https://github.com/antuankerbage/Stoneshard-Character-Lab.git
cd Stoneshard-Character-Lab
```

Run with Python:

```bash
python3 run.py
```

Alternatively, on Linux or macOS:

```bash
chmod +x run.sh
./run.sh
```

On Windows:

```powershell
py run.py
```

## Working with save files

Stoneshard character saves are commonly stored in a directory named `characters_v1`.

### Windows

```text
%LocalAppData%\StoneShard\characters_v1
```

You can open this location by pressing `Win + R` and entering the path.

### Linux / Steam Proton

A common location is:

```text
~/.steam/steam/steamapps/compatdata/625960/pfx/drive_c/users/steamuser/AppData/Local/StoneShard/characters_v1
```

Your Steam library location or Proton configuration may change this path.

### Important folder structure

A typical character folder contains a structure similar to:

```text
characters_v1/
└── character_1/
    ├── character.map
    ├── autosave_1/
    │   ├── data.sav
    │   ├── save.map
    │   └── preview.png
    └── exitsave_1/
        ├── data.sav
        ├── save.map
        └── preview.png
```

When using the folder scanner, select the complete `character_N` folder, not its parent `characters_v1` directory.

## Saving changes safely

**Always close Stoneshard before modifying or replacing save files.**

The application supports different ways to preserve edited data:

- **Direct save:** writes the changes to the loaded `data.sav`.
- **Save character for the game:** creates a separate character folder for testing.
- **ZIP export:** exports the edited save together with a backup.

When directly saving, the application creates `data.sav.bak` if a backup does not already exist. Keep an independent backup of your original save as well.

The application checks the save checksum after writing. A valid checksum confirms file integrity, but it does not guarantee that every modified value will be accepted by the game. Always test edited saves in Stoneshard.

## Built-in catalog

The project includes an initial catalog of identifiers collected from available character saves.

The catalog is a starting point for experimentation, not a complete database of every possible Stoneshard character, appearance, class, perk, or skill identifier.

Additional save files can help expand the available data.

## Run tests

From the project root:

```bash
python3 -m unittest discover -s tests -v
```

To check Python source compilation:

```bash
python3 -m compileall .
```

## Build a standalone executable (optional)

The application can optionally be packaged with PyInstaller.

Install it:

```bash
python3 -m pip install pyinstaller
```

Build:

```bash
pyinstaller --noconfirm --clean --windowed --name StoneshardCharacterLab run.py
```

The generated executable will be placed in the `dist/` directory.

**Important:** PyInstaller builds should be generated separately on each target operating system. It is not a cross-compiler.

## Logs

The application stores diagnostic logs in the user's home directory.

On Linux and macOS:

```text
~/.stoneshard_character_lab/stoneshard_character_lab.log
```

The Windows location is inside the user's home directory.

## Related project

This Python application is the original experimental desktop project used to investigate Stoneshard save data and test backend-level modifications.

The related browser-based implementation is maintained separately:

**[Stoneshard Player Editor](https://github.com/antuankerbage/Stoneshard-Player-Editor)**

The browser project is independent and does not require this Python application to run.

## Game links

- [Stoneshard on Steam](https://store.steampowered.com/app/625960/Stoneshard/)
- [Official Stoneshard website](https://stoneshard.com/)

## Disclaimer

This is an unofficial community project. It is not affiliated with, endorsed by, or associated with Ink Stains Games.

Stoneshard, its trademarks, game content, and assets belong to their respective owners.

Use this software at your own risk. Always keep backups of your save files.

## Support development

If you find this project useful and would like to support its development, you can make an optional donation:

**PayPal: @osirix89**  
https://www.paypal.me/osirix89

Contact: antuankerbage@gmail.com

**Made in Argentina 🇦🇷 by antuankerbage — osirix89**

---

# Español

## Acerca del proyecto

**Stoneshard Character Lab** es una aplicación de escritorio experimental para inspeccionar, editar, validar y administrar archivos de guardado de personajes de Stoneshard.

El proyecto fue desarrollado como un entorno local de investigación y experimentación para comprender la estructura de los archivos de guardado, probar modificaciones en los datos de los personajes y explorar las posibilidades de edición.

Es una aplicación de escritorio independiente desarrollada en Python. No necesita un servidor web ni una cuenta en línea.

## Funciones

- Cargar una carpeta completa `character_N` o un archivo `data.sav` individual.
- Inspeccionar las partidas del personaje, incluidos autosaves y exitsaves.
- Editar campos de identidad y apariencia.
- Modificar atributos y progresión.
- Administrar perks y habilidades aprendidas.
- Inspeccionar y editar datos JSON avanzados.
- Comparar una partida con otra.
- Copiar grupos de datos seleccionados entre partidas.
- Escanear carpetas y archivos ZIP para detectar identificadores.
- Importar y exportar catálogos.
- Validar la estructura y el checksum de los archivos.
- Guardar cambios directamente en el `data.sav` cargado.
- Clonar un personaje editado en una carpeta `character_N` independiente.
- Exportar partidas en ZIP junto con una copia de seguridad.
- Consultar información de diagnóstico y registros de la aplicación.

Los campos disponibles dependen de la estructura de la partida y de los datos que expone la aplicación.

## Requisitos

- Python 3.10 o superior.
- Tkinter.
- No se necesitan paquetes Python de terceros para ejecutar la aplicación normalmente.

### Instalar Tkinter

En Debian o Ubuntu:

```bash
sudo apt update
sudo apt install python3 python3-tk
```

En Fedora:

```bash
sudo dnf install python3-tkinter
```

En Arch Linux:

```bash
sudo pacman -S tk
```

## Ejecutar la aplicación

Cloná el repositorio:

```bash
git clone https://github.com/antuankerbage/Stoneshard-Character-Lab.git
cd Stoneshard-Character-Lab
```

Ejecutá con Python:

```bash
python3 run.py
```

Alternativamente, en Linux o macOS:

```bash
chmod +x run.sh
./run.sh
```

En Windows:

```powershell
py run.py
```

## Trabajar con partidas guardadas

Stoneshard almacena habitualmente las partidas de los personajes en un directorio llamado `characters_v1`.

### Windows

```text
%LocalAppData%\StoneShard\characters_v1
```

Podés abrir esta ubicación presionando `Win + R` e ingresando la ruta.

### Linux / Steam Proton

Una ubicación habitual es:

```text
~/.steam/steam/steamapps/compatdata/625960/pfx/drive_c/users/steamuser/AppData/Local/StoneShard/characters_v1
```

La ubicación de tu biblioteca de Steam o la configuración de Proton pueden modificar esta ruta.

### Estructura habitual

Una carpeta de personaje puede tener una estructura similar a esta:

```text
characters_v1/
└── character_1/
    ├── character.map
    ├── autosave_1/
    │   ├── data.sav
    │   ├── save.map
    │   └── preview.png
    └── exitsave_1/
        ├── data.sav
        ├── save.map
        └── preview.png
```

Al utilizar el escáner de carpetas, seleccioná la carpeta completa `character_N`, no el directorio superior `characters_v1`.

## Guardar los cambios de forma segura

**Cerrá siempre Stoneshard antes de modificar o reemplazar archivos de guardado.**

La aplicación ofrece distintas formas de conservar los datos editados:

- **Guardado directo:** escribe los cambios en el `data.sav` cargado.
- **Guardar personaje para el juego:** crea una carpeta de personaje independiente para realizar pruebas.
- **Exportar ZIP:** exporta la partida editada junto con una copia de seguridad.

Al guardar directamente, la aplicación crea `data.sav.bak` si todavía no existe una copia de respaldo. Conservá también una copia independiente del archivo original.

Después de escribir, la aplicación comprueba el checksum. Un checksum válido confirma la integridad del archivo, pero no garantiza que el juego acepte todos los valores modificados. Probá siempre las partidas editadas dentro de Stoneshard.

## Catálogo integrado

El proyecto incluye un catálogo inicial de identificadores recopilados de partidas de personajes disponibles.

Este catálogo es un punto de partida para experimentar, no una base de datos completa de todos los personajes, apariencias, clases, perks o habilidades posibles de Stoneshard.

La incorporación de más partidas puede ayudar a ampliar los datos disponibles.

## Ejecutar las pruebas

Desde la carpeta principal del proyecto:

```bash
python3 -m unittest discover -s tests -v
```

Para comprobar la compilación del código Python:

```bash
python3 -m compileall .
```

## Crear un ejecutable independiente (opcional)

La aplicación puede empaquetarse con PyInstaller.

Instalalo:

```bash
python3 -m pip install pyinstaller
```

Compilá:

```bash
pyinstaller --noconfirm --clean --windowed --name StoneshardCharacterLab run.py
```

El ejecutable generado se ubicará en la carpeta `dist/`.

**Importante:** PyInstaller debe ejecutarse por separado en cada sistema operativo de destino. No es un compilador cruzado.

## Registros

La aplicación almacena registros de diagnóstico en el directorio personal del usuario.

En Linux y macOS:

```text
~/.stoneshard_character_lab/stoneshard_character_lab.log
```

En Windows, la ubicación equivalente se encuentra dentro del directorio personal del usuario.

## Proyecto relacionado

Esta aplicación de Python es el proyecto experimental original utilizado para investigar los datos de guardado de Stoneshard y probar modificaciones a nivel de backend.

La implementación relacionada para navegador se mantiene en un repositorio independiente:

**[Stoneshard Player Editor](https://github.com/antuankerbage/Stoneshard-Player-Editor)**

El proyecto web es independiente y no necesita esta aplicación de Python para funcionar.

## Enlaces del juego

- [Stoneshard en Steam](https://store.steampowered.com/app/625960/Stoneshard/)
- [Página oficial de Stoneshard](https://stoneshard.com/)

## Aviso legal

Este es un proyecto comunitario no oficial. No está afiliado, respaldado ni asociado con Ink Stains Games.

Stoneshard, sus marcas, contenido y recursos pertenecen a sus respectivos propietarios.

Utilizá este programa bajo tu propia responsabilidad. Conservá siempre copias de seguridad de tus partidas.

## Apoyar el desarrollo

Si el proyecto te resulta útil y querés colaborar con su desarrollo, podés realizar una donación voluntaria:

**PayPal: @osirix89**  
https://www.paypal.me/osirix89

Contacto: antuankerbage@gmail.com

**Hecho en Argentina 🇦🇷 por antuankerbage — osirix89**
