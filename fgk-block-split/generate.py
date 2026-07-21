#!/usr/bin/env python3
"""Regenerate patch.vcdiff for the FGK block-split fixture.

FGK is xdelta3's adaptive-Huffman secondary compressor (catalog id 16).
Its coder keeps tree nodes in ranked order and groups equal-ranked nodes
into blocks that a weight bump shuffles as a unit. A block is usually the
whole run of nodes tied at one weight, but it can be finer: a raised node
only ever merges into the block to its right, so a same-weight node that
ends up to the left and is never raised again stays a block of its own.
Reproducing xdelta3's output then needs each node's block membership, not
just its weight -- see rusty-slap/src/xdelta3_fgk.rs.

The tree only develops such a finer block after a good many symbols, so a
section has to be sizeable to reach one. expected.bin is 37000 bytes of
literal data lifted from a dense ROM diff, long enough that decoding it
matures the tree past that point. Compressing it with -S fgk and no source
puts all of it through the FGK coder as one section; the fixture is that
patch, and applying it must return expected.bin byte for byte.

expected.bin is committed as the input of record. This script derives only
patch.vcdiff from it, so the fixture stays reproducible from a checkout.

Usage: python3 generate.py   (needs xdelta3 on PATH)
"""

import pathlib
import subprocess

here = pathlib.Path(__file__).resolve().parent
expected = here / "expected.bin"
patch = here / "patch.vcdiff"

subprocess.run(
    ["xdelta3", "-f", "-S", "fgk", "-e", str(expected), str(patch)],
    check=True,
)
print(f"wrote {patch} ({patch.stat().st_size} bytes)")
