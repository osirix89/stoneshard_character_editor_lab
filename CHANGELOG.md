# Changelog

## 0.5.0
- Added a large, full-width **GUARDAR data.sav (Ctrl+S)** button directly below the title, always visible above the tabs.
- The button applies the current form values and writes the edited `data.sav` directly to the loaded file path.
- Creates/refreshes a `data.sav.bak` backup before overwriting and verifies the saved checksum.
- Added Ctrl+S shortcut. Character cloning and ZIP export remain separate optional actions.

## 0.4.0
- Prominent direct-save action for creating a game-ready `character_N` folder.
- Clear destination picker guidance for selecting `characters_v1`.
- Automatically corrects selection of an individual `character_N` folder to its parent.
- Save confirmation lists the generated game files and checksum verification.

## 0.3.0
- Bundled starter catalog from the eight valid saves provided by the user.
- Form values are committed automatically before export and clone.
- Clone writes a new character folder and verifies all three checksums.

## 0.2.0
- Initial editable identity, attributes, perks, skills, comparison, and raw JSON interface.
