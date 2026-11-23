# PlayStation 2 (PS2) games

1. Make a folder here named after the game. The folder name is the game's title in the launcher.
2. Put the game's disc in that folder: one file, or all of its parts.

```
rom/PS2/
  My Game/
    My Game.part001.iso
    My Game.part002.iso
    My Game.part003.iso
    cover.jpg            (optional)
```

PS2 notes:

- Disc files: `.iso`, `.cso`, `.chd` or `.bin`. **Not zipped or 7-zipped**: the PS2 emulator reads the disc while you play, straight from the site, so there's no big download first, but it can't read inside a `.zip` / `.7z`.
- Big discs: cut them into parts (the Game Splitter does it, or names like `My Game.iso.001`, `.002`, ...). A `.cso` or `.chd` is smaller than the `.iso`, so it needs fewer parts.
- Upload **every** part, in the same folder.
- PS2 games only play on the website (GitHub Pages), on a fast computer with an up-to-date Chrome, Edge or Firefox. On phones most games are too slow.
- PS2 in the browser is an experiment (Play! emulator): many games run slowly, have graphics glitches or don't start. No BIOS file is needed.
