# slap-test-patches

> "Slap is a multi-format ROM patching tool." — me, 2026

Test patches for [slap](https://github.com/nyuutsu/slap).

Stored separately so cloning slap doesn't require cloning a bunch of patches too. Maybe the entire test directory should be the submodule instead?

Many patch files in this repository are other people's work. See `CREDITS.md` for... credits. The MIT license asserted in `LICENSE` is for the subset that are my own work.

## Base ROMs

Tests apply patches against base ROM files that you provide. Place each file at the expected path. The test harness skips suites whose base ROM is missing.

| Game | File | Path | CRC32 |
|------|------|------|-------|
| Yu-Gi-Oh! Duel Monsters 4: Battle of Great Duelist - Yuugi Deck (Japan) | base.gbc | dm4y/ | `4d6105f6` |
| Pokemon Stadium 2 (USA) | base.z64 | stadium2/ | `a9998e09` |
| Fire Emblem: The Binding Blade (Japan) | base.gba | fe6/ | `d38763e1` |
| Final Fantasy Tactics Advance (USA) | base.gba | ffta/ | `5645e56c` |
| Mother 3 (Japan) | base.gba | mother3/ | `42ac9cb9` |
| Kirby's Dream Land 2 | base.gb | kirby-dl2/ | `8dc07c35` |
| Tetris (World) | base.gb | tetris/ | `46df91ad` |
| Paper Mario (USA) | base.z64 | paper-mario/ | `a7f5cd7e` |
| Banjo-Tooie (USA) | base.z64 | banjo-tooie/ | `bab803ef` |
| Castlevania: Symphony of the Night (Japan, Rev 2, Track 1) | base-track1.bin | sotn/ | `d8114e7d` |
| Suikoden (USA) | base.bin | suikoden/ | `5cb74712` |
| Splatoon 2 v5.0.0 (decompressed NSO) | base.nso | splatoon2/ | `ff45a757` |
| Splatoon 3 v7.0.0 (decompressed NSO) | base.nso | splatoon3/ | `f3749928` |
| Tears of the Kingdom v1.1.0 (decompressed NSO) | base.nso | totk/ | `c11a9a2c` |

## License

MIT
