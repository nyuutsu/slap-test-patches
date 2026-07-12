#!/usr/bin/env python3
"""Hand-built VCDIFF fixtures exercising the RFC arc's custom code table.

No tool emits custom code tables (xdelta3 removed support), so these are built
by hand, every byte justified against docs/vcdiff/rfc-vcdiff/upstream/rfc3284.txt
(§5.6 the default table, §7 the custom-table envelope), with the expected result
written down here BEFORE slap runs (slap must not grade its own homework).

The default 1536-byte table image below is reconstructed independently from the
RFC §5.6 prose — it is the oracle, not a copy of slap's own table.

Run from anywhere:

    python3 generate.py          # writes the .vcdiff files beside this script

Custom-table wire layout (RFC 3284 §4.1, §7):
  header = magic(D6 C3 C4) version(00) Hdr_Indicator(VCD_CODETABLE=0x02)
           code_table_length(varint)        # counts the two size bytes + inner delta
           s_near(byte) s_same(byte)
           inner_delta(bytes)               # a self-contained VCDIFF delta file
  then the ordinary windows, decoded against the built table.

The inner delta is itself a complete VCDIFF patch (it has the magic): RFC §7's
no-nesting rule forbids it declaring its own VCD_CODETABLE, a header bit, which
only makes sense if the inner delta carries a header. slap decodes it by reusing
its own parse+apply against the serialized default image.
"""

from pathlib import Path

MAGIC = bytes([0xD6, 0xC3, 0xC4])

# Instruction type tags (RFC §5.4).
NOOP, ADD, RUN, COPY = 0, 1, 2, 3


def varint(value: int) -> bytes:
    """RFC §2 big-endian base-128, high bit = continue."""
    groups = [value & 0x7F]
    value >>= 7
    while value:
        groups.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(groups))


def window(win_indicator, target_size, data, inst, addr, segment=None):
    """One window, delta_encoding_length computed from the fields it covers."""
    segment_bytes = b""
    if segment is not None:
        seg_len, seg_pos = segment
        segment_bytes = varint(seg_len) + varint(seg_pos)
    body = (varint(target_size)
            + bytes([0x00])                      # Delta_Indicator: nothing compressed
            + varint(len(data)) + varint(len(inst)) + varint(len(addr))
            + data + inst + addr)
    return bytes([win_indicator]) + segment_bytes + varint(len(body)) + body


# --- the default code table image, rebuilt from RFC §5.6 --------------------
# Each of the 256 entries is two (type, size, mode) triples. A size of 0 means
# "size coded separately"; mode is meaningful only for COPY.

def default_entries():
    entries = []                                  # (t1, s1, m1, t2, s2, m2)

    def single(t, s, m):
        return (t, s, m, NOOP, 0, 0)

    # index 0: RUN, size coded separately
    entries.append(single(RUN, 0, 0))
    # 1..18: ADD size 0 (coded), then ADD sizes 1..17
    entries.append(single(ADD, 0, 0))
    for size in range(1, 18):
        entries.append(single(ADD, size, 0))
    # 19..162: for each mode 0..8: COPY size 0 (coded), then COPY sizes 4..18
    for mode in range(0, 9):
        entries.append(single(COPY, 0, mode))
        for size in range(4, 19):
            entries.append(single(COPY, size, mode))
    # 163..234: ADD(1..4)+COPY(4..6), modes 0..5
    for mode in range(0, 6):
        for add_size in range(1, 5):
            for copy_size in range(4, 7):
                entries.append((ADD, add_size, 0, COPY, copy_size, mode))
    # 235..246: ADD(1..4)+COPY(4), modes 6..8
    for mode in range(6, 9):
        for add_size in range(1, 5):
            entries.append((ADD, add_size, 0, COPY, 4, mode))
    # 247..255: COPY(4)+ADD(1), modes 0..8
    for mode in range(0, 9):
        entries.append((COPY, 4, mode, ADD, 1, 0))

    assert len(entries) == 256, len(entries)
    return entries


def serialize_table(entries) -> bytes:
    """RFC §7a: six 256-byte slices — types1, types2, sizes1, sizes2, modes1, modes2."""
    cols = list(zip(*entries))                    # (t1s, s1s, m1s, t2s, s2s, m2s)
    t1, s1, m1, t2, s2, m2 = cols
    return bytes(list(t1) + list(t2) + list(s1) + list(s2) + list(m1) + list(m2))


DEFAULT_IMAGE = serialize_table(default_entries())
assert len(DEFAULT_IMAGE) == 1536


def poke(image: bytes, offset: int, value: int) -> bytes:
    return image[:offset] + bytes([value]) + image[offset + 1:]


# Slice bases within the 1536-byte image.
TYPES1, TYPES2, SIZES1, SIZES2, MODES1, MODES2 = 0, 256, 512, 768, 1024, 1280


def inner_delta_for(image: bytes) -> bytes:
    """A self-contained VCDIFF that ADDs `image` verbatim — the simplest delta
    that produces a given 1536-byte table, source-independent (pure ADD)."""
    add_inst = bytes([ADD]) + varint(len(image))  # code byte 1 = ADD size coded; then the size
    win = window(0x00, len(image), image, add_inst, b"")
    return MAGIC + bytes([0x00, 0x00]) + win


def custom_table_patch(s_near, s_same, inner_delta, *windows) -> bytes:
    table_data = bytes([s_near, s_same]) + inner_delta
    header = MAGIC + bytes([0x00, 0x02]) + varint(len(table_data)) + table_data
    return header + b"".join(windows)


# code-table indices we reach for in outer windows (default §5.6 layout):
ADD5  = bytes([1 + 5])                             # single ADD, size 5  -> index 6
COPY4_MODE6 = bytes([20 + 16 * 6 + (4 - 4)])      # COPY mode 6, size 4 -> index 116
                                                   # (index 19+16*m is the size-coded
                                                   #  entry; sizes 4..18 follow at +1..)


# --- fixture A: identity table, default caches ------------------------------
# Custom table byte-identical to the default, s_near=4 s_same=3 (the defaults).
# Outer: one self-contained window, ADD "HELLO". Proves the whole pipeline —
# frame the table, decode its inner delta, build it, decode the window against
# it — with output unchanged from the default-table reading.
# Expected: applies to "HELLO"; flavor RFC 3284; info names a custom code table.
fixtureA = custom_table_patch(4, 3, inner_delta_for(DEFAULT_IMAGE),
                              window(0x00, 5, b"HELLO", ADD5, b""))
fixtureA_source = b""
fixtureA_expected = b"HELLO"

# --- fixture B: nested custom table -----------------------------------------
# The inner delta is itself a patch declaring VCD_CODETABLE. RFC §7c forbids it.
# Expected: refused, "slap can't find a place to start reading this patch's
# instruction table".
inner_nested = (MAGIC + bytes([0x00, 0x02]) + varint(2) + bytes([4, 3])
                + window(0x00, 5, b"HELLO", ADD5, b""))
fixtureB = custom_table_patch(4, 3, inner_nested,
                              window(0x00, 5, b"HELLO", ADD5, b""))
fixtureB_expected = "refused: slap can't find a place to start reading this patch's instruction table"

# --- fixture C: inner delta yields an invalid entry -------------------------
# Poke types1[0] to 4 (no such instruction type; COPY=3 is the max).
# Expected: refused, "the instruction table this patch brought with it names an
# instruction that doesn't exist" (type byte 4).
imageC = poke(DEFAULT_IMAGE, TYPES1 + 0, 0x04)
fixtureC = custom_table_patch(4, 3, inner_delta_for(imageC),
                              window(0x00, 5, b"HELLO", ADD5, b""))
fixtureC_expected = "refused: the instruction table this patch brought with it names an instruction that doesn't exist"

# --- fixture D: a do-nothing (NOOP+NOOP) entry ------------------------------
# Poke entry 1 (ADD size 0) to type NOOP, leaving size 0 / mode 0 / second NOOP:
# a legal but pointless do-nothing entry. The outer window never indexes it.
# Expected: applies to "HELLO"; a note that the table has 1 do-nothing entry.
imageD = poke(DEFAULT_IMAGE, TYPES1 + 1, NOOP)
fixtureD = custom_table_patch(4, 3, inner_delta_for(imageD),
                              window(0x00, 5, b"HELLO", ADD5, b""))
fixtureD_source = b""
fixtureD_expected = b"HELLO"  # + note: 1 do-nothing entry

# --- fixture E: non-default cache size, reinterpreting a mode ----------------
# Identity table contents, but s_near=6 (so modes 2..7 are near, 8..10 same).
# The outer window's COPY uses code byte 115 = COPY mode 6. Under the default
# s_near=4 that mode is same-cache block 0 (a one-byte operand, fresh -> 0);
# under s_near=6 it is near slot 4 (a varint operand, fresh slot -> 0 + v).
# addr section is the single byte 0x03 (varint 3 == same-byte 3). So:
#   under s_near=6 (ours): address 0 + 3 = 3 -> COPY source[3:7] = "3456"
#   under s_near=4 (default): same[3] = 0   -> COPY source[0:4] = "0123"
# Output "3456" is one the default config could not have produced.
fixtureE = custom_table_patch(6, 3, inner_delta_for(DEFAULT_IMAGE),
                              window(0x01, 4, b"", COPY4_MODE6, bytes([0x03]),
                                     segment=(10, 0)))
fixtureE_source = b"0123456789"
fixtureE_expected = b"3456"

# --- fixture F: a COPY mode the declared caches do not reach -----------------
# s_near=4 s_same=3 -> highest mode is 8. Poke entry 19's mode (a COPY) to 9.
# deserialize carries the mode verbatim; the table-build mode check rejects it.
# Expected: refused, "the instruction table this patch brought with it doesn't
# agree with itself about how copy addresses are written" (mode 9, modes 0
# through 8 defined).
imageF = poke(DEFAULT_IMAGE, MODES1 + 19, 9)
fixtureF = custom_table_patch(4, 3, inner_delta_for(imageF),
                              window(0x00, 5, b"HELLO", ADD5, b""))
fixtureF_expected = "refused: the instruction table this patch brought with it doesn't agree with itself about how copy addresses are written"


def main() -> None:
    here = Path(__file__).resolve().parent
    fixtures = [
        ("fixtureA-identity.vcdiff",        fixtureA),
        ("fixtureB-nested.vcdiff",          fixtureB),
        ("fixtureC-invalid-entry.vcdiff",   fixtureC),
        ("fixtureD-noop-noop.vcdiff",       fixtureD),
        ("fixtureE-larger-near-cache.vcdiff", fixtureE),
        ("fixtureF-mode-out-of-range.vcdiff", fixtureF),
    ]
    for name, blob in fixtures:
        (here / name).write_bytes(blob)
        print(f"wrote {name}: {len(blob)} bytes")
    (here / "sourceA.bin").write_bytes(fixtureA_source)
    (here / "sourceD.bin").write_bytes(fixtureD_source)
    (here / "sourceE.bin").write_bytes(fixtureE_source)
    print()
    print(f"A identity         -> applies to {fixtureA_expected!r}, flavor RFC, names custom table")
    print(f"B nested           -> {fixtureB_expected}")
    print(f"C invalid entry    -> {fixtureC_expected}")
    print(f"D noop+noop        -> applies to {fixtureD_expected!r} + do-nothing-entry note")
    print(f"E larger near cache-> applies to {fixtureE_expected!r} (default config would give b'0123')")
    print(f"F mode out of range-> {fixtureF_expected}")


if __name__ == "__main__":
    main()
