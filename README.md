# slap-test-patches

> "Slap is a multi-format ROM patching tool." — me, 2026

Test patches for [slap](https://github.com/nyuutsu/slap). This repo is used as a git submodule; this is done so *merely* cloning slap proper, doesn't pull in ~500 MB of patches. To set the test patches up from the slap repo:

```
git submodule update --init
```

Many patch files in this repository are other people's work. See `CREDITS.md` for... credits. The MIT license asserted in `LICENSE` is for the subset that are my own work.

## Lineage

The test suite has four classifications:

* Real: a real-world patch from some actual project
* Converted: a "real" patch repackaged into a different patch format\*
* Synthetic: the patch target was fabricated (e.g. via PRNG XOR).\*\*
* Broken: a known-broken patch, skipped by the runner. Unused at time of writing.

\* We apply the patch to the input rom using some outside tool (such as, say, [flips](https://git.disroot.org/Sir_Walrus/Flips)), producing an output rom. We use some tool (say, [xdelta3](https://github.com/xorgy/xdelta3)), the input rom, and the output from to create a patch in a different format.

\*\* We take some rom and make a bunch of changes to a copy of it. We then use some outside tool, the input rom, and the output rom to create a patch.

## Suite format

*Paths are relative to the slap repo root.*

Test scenarios are in `test/suites/*.suite`. Each names an input rom, the expected SHA1 of the output rom, and one or more patches that should produce the output. The test runner discovers suite files automatically and skips any whose input rom is missing.

An example of the `.suite` format is provided. The `.suite` format documentation is in `test/suites/README.MD` 

*This patch is actually mine! It's a working copy of the "[DM4 Translation](https://nyuu.page/projects/dm4-translation/)" project.*

```
base:   test/data/dm4y/base.gbc
sha1:   10f5981bca3660127d308778b60a343e2e44dec7
desc:   dm4y translation (4 MB GBC, 14 formats)

BPS      | test/data/dm4y/patch.bps       | real      | dm4-hacking translation project
IPS      | test/data/dm4y/patch.ips       | converted | Flips
IPS32    | test/data/dm4y/patch.ips32     | converted | sips
UPS      | test/data/dm4y/patch.ups       | converted | Go ups
PPF3     | test/data/dm4y/patch.ppf       | converted | MakePPF3
PPF1     | test/data/dm4y/patch.ppf1.ppf  | converted | RomPatcher.js
PPF2     | test/data/dm4y/patch.ppf2.ppf  | converted | RomPatcher.js
EBP      | test/data/dm4y/patch.ebp       | converted | RomPatcher.js
APS-N64  | test/data/dm4y/patch.aps       | converted | RomPatcher.js
NINJA2   | test/data/dm4y/patch.rup       | converted | RomPatcher.js
VCDIFF   | test/data/dm4y/patch.vcdiff    | converted | xdelta3 -S none
bsdiff   | test/data/dm4y/patch.bsdiff    | converted | bsdiff
xdelta1  | test/data/dm4y/patch.xdelta1   | converted | xdelta 1.1.4
GDIFF    | test/data/dm4y/patch.gdiff     | converted | javaxdelta
```

The fourth column names the tool or project that produced the patch.

## Base ROMs

Tests apply patches against base ROM files that you provide. Place
each file at the expected path. The test harness skips suites whose
base ROM is missing.

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
