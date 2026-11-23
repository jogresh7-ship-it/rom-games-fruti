# PlayStation Portable (PSP) games

1. Make a folder here named after the game. The folder name is the game's title in the launcher.
2. Put the game in that folder: one file, or all of its parts.

```
rom/PSP/
  My Game/
    My Game.part001.zip
    My Game.part002.zip
    My Game.part003.zip
    cover.jpg            (optional)
```

- `.zip`, `.7z` and plain ROM files all work.
- Parts are joined in order. Names like `My Game.part001.zip`, `My Game part 1.zip`, `My Game (Part 1).zip` and `My Game.zip.001` all work.
- A game that is one complete file can also go straight into `rom/PSP/`. Its file name is the title. Parts must be in a game folder.
- A `.jpg` or `.png` in the game's folder becomes its cover.

PSP notes:

- Game files: `.iso`, `.cso` or `.pbp`, or a `.zip` / `.7z` with one inside. A 7z cut into parts named `.zip` (like `My Game.part001.zip`) works.
- Upload **every** part, or the game can't be put back together.
- PSP games only play on the website (GitHub Pages), on a computer with an up-to-date Chrome, Edge or Firefox. They don't play when `index.html` is opened from your computer.
- Big games take a while to download and unpack the first time, and need a lot of memory (roughly 2 to 3 times the game's size).
