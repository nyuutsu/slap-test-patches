#!/usr/bin/env python3
"""Hand-built VCDIFF fixtures exercising the RFC arc's VCD_TARGET feature.

No tool in the world emits VCD_TARGET windows, so these are built by hand,
every byte justified against docs/vcdiff/rfc-vcdiff/upstream/rfc3284.txt, with
the expected result written down here BEFORE slap runs (slap must not grade its
own homework).

Run from anywhere:

    python3 generate.py          # writes the three .vcdiff files beside this script

Wire layout recap (RFC 3284 §4):
  header  = magic(D6 C3 C4) version(00) Hdr_Indicator
  window  = Win_Indicator
            [if a copy-source bit set] segment_length(varint) segment_position(varint)
            delta_encoding_length(varint)        # bytes from here through addr section
            target_window_size(varint)
            Delta_Indicator
            data_length(varint) inst_length(varint) addr_length(varint)
            [if VCD_ADLER32] adler32(4 bytes, big-endian)
            data_section inst_section addr_section

Win_Indicator bits: 0=VCD_SOURCE, 1=VCD_TARGET, 2=VCD_ADLER32.

Default code-table indices used below (RFC 3284 §5.6):
  ADD size k (1..17), single instruction  -> index 1 + k
  COPY mode m, size s (4..18), mode 0 = SELF (address is a plain varint)
                                          -> index 20 + 16*m + (s - 4)
"""

from pathlib import Path

MAGIC = bytes([0xD6, 0xC3, 0xC4])


def varint(value: int) -> bytes:
    """RFC 3284 §2 big-endian base-128, high bit = continue. (All values
    here are < 128, so each is a single byte; the loop keeps this a complete encoder.)"""
    groups = [value & 0x7F]
    value >>= 7
    while value:
        groups.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(groups))


def window(win_indicator, target_size, data, inst, addr,
           segment=None, adler=None):
    """Assemble one window, computing delta_encoding_length from the fields it
    actually covers so the framing can never silently disagree with itself."""
    segment_bytes = b""
    if segment is not None:
        seg_len, seg_pos = segment
        segment_bytes = varint(seg_len) + varint(seg_pos)

    adler_bytes = adler if adler is not None else b""
    assert adler is None or len(adler) == 4

    # delta_encoding_length spans everything after the length field itself,
    # through the end of the address section.
    body = (varint(target_size)
            + bytes([0x00])                      # Delta_Indicator: nothing compressed
            + varint(len(data)) + varint(len(inst)) + varint(len(addr))
            + adler_bytes
            + data + inst + addr)

    return bytes([win_indicator]) + segment_bytes + varint(len(body)) + body


def patch(hdr_indicator, *windows) -> bytes:
    return MAGIC + bytes([0x00, hdr_indicator]) + b"".join(windows)


# --- fixture 1: cross-window VCD_TARGET copy --------------------------------
# window 0: self-contained ADD of "ABCDEFGH" (8 bytes). inst = ADD size 8 = index 9.
# window 1: VCD_TARGET, segment = produced-target[2:6] = "CDEF"; one COPY of
#           length 4 at superstring address 0 (SELF, reads the segment start).
# Expected apply output: "ABCDEFGH" + "CDEF" = "ABCDEFGHCDEF". Flavor: RFC 3284.
ADD8 = bytes([9])
COPY4_SELF, ADDR0 = bytes([0x14]), bytes([0x00])
fixture1 = patch(0x00,
                 window(0x00, 8, b"ABCDEFGH", ADD8, b""),
                 window(0x02, 4, b"", COPY4_SELF, ADDR0, segment=(4, 2)))
fixture1_expected = b"ABCDEFGHCDEF"

# --- fixture 2: empty first-window VCD_TARGET -------------------------------
# One VCD_TARGET window, segment length 0, target size 0: reaches nothing,
# applies as a no-op. Expected: empty output + the empty-segment note.
fixture2 = patch(0x00, window(0x02, 0, b"", b"", b"", segment=(0, 0)))
fixture2_expected = b""

# --- fixture 3: VCD_TARGET + Adler32 = neither dialect ----------------------
# fixture 1 with VCD_ADLER32 also set on window 1. A VCD_TARGET window (RFC)
# carrying a per-window Adler32 (xdelta3) belongs to neither dialect.
# Expected: refused, naming the per-window Adler32. (Adler value is arbitrary;
# it is read to reach the refusal, then the patch is declined.)
fixture3 = patch(0x00,
                 window(0x00, 8, b"ABCDEFGH", ADD8, b""),
                 window(0x06, 4, b"", COPY4_SELF, ADDR0,
                        segment=(4, 2), adler=bytes([0, 0, 0, 0])))
fixture3_expected = "refused: VCD_TARGET window + a per-window Adler32 (neither dialect)"


def main() -> None:
    here = Path(__file__).resolve().parent
    for name, blob in [("fixture1-cross-window.vcdiff", fixture1),
                       ("fixture2-empty-segment.vcdiff", fixture2),
                       ("fixture3-target-plus-adler.vcdiff", fixture3)]:
        (here / name).write_bytes(blob)
        print(f"wrote {name}: {len(blob)} bytes  ({blob.hex(' ')})")
    print()
    print(f"fixture1 expected apply output: {fixture1_expected!r}")
    print(f"fixture2 expected apply output: {fixture2_expected!r} + empty-segment note")
    print(f"fixture3 expected: {fixture3_expected}")


if __name__ == "__main__":
    main()
