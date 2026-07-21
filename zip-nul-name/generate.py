#!/usr/bin/env python3
# A ZIP whose single entry's name carries a NUL byte ("a.ips\0b").
# The `zip` tool and Python's zipfile both sanitize the NUL, so the raw central
# directory is written by hand. slap read the NUL as a name separator and saw two
# phantom candidates; the by-index unwrap sees the one real entry. Store method,
# valid CRC, so a conformant reader extracts the IPS inside.
import struct, zlib

content = b'PATCH' + bytes([0, 0, 5]) + bytes([0, 3]) + b'abc' + b'EOF'  # a tiny valid IPS
name = b'a.ips\x00b'
crc = zlib.crc32(content) & 0xffffffff
n = len(content)

local = struct.pack('<IHHHHHIIIHH', 0x04034b50, 20, 0, 0, 0, 0, crc, n, n, len(name), 0) + name + content
central = struct.pack('<IHHHHHHIIIHHHHHII', 0x02014b50, 20, 20, 0, 0, 0, 0, crc, n, n, len(name), 0, 0, 0, 0, 0, 0) + name
end = struct.pack('<IHHHHIIH', 0x06054b50, 0, 0, 1, 1, len(central), len(local), 0)

with open('entry.zip', 'wb') as f:
    f.write(local + central + end)
