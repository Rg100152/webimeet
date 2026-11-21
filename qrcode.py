"""Tiny self-contained QR Code generator (byte mode, EC level M, versions 1-10).

No third-party dependency — only Python stdlib. Produces an SVG string so the
RSVP pass stays crisp at any print resolution.
"""

# (ecc_codewords_per_block, group1_blocks, group1_data, group2_blocks, group2_data)
_ECC_TABLE = {
    1: (10, 1, 16, 0, 0),
    2: (16, 1, 28, 0, 0),
    3: (26, 1, 44, 0, 0),
    4: (18, 2, 32, 0, 0),
    5: (24, 2, 43, 0, 0),
    6: (16, 4, 27, 0, 0),
    7: (18, 4, 31, 0, 0),
    8: (22, 2, 38, 2, 39),
    9: (22, 3, 36, 2, 37),
    10: (26, 4, 43, 1, 44),
}

_ALIGNMENT = {
    1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30],
    6: [6, 34], 7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46],
    10: [6, 28, 50],
}


def _gf_mul(x, y):
    z = 0
    for i in range(7, -1, -1):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z


def _rs_divisor(degree):
    result = [0] * (degree - 1) + [1]
    root = 1
    for _ in range(degree):
        for i in range(degree):
            result[i] = _gf_mul(result[i], root)
            if i + 1 < degree:
                result[i] ^= result[i + 1]
        root = _gf_mul(root, 0x02)
    return result


def _rs_remainder(data, divisor):
    result = [0] * len(divisor)
    for byte in data:
        factor = byte ^ result[0]
        result = result[1:] + [0]
        for i in range(len(divisor)):
            result[i] ^= _gf_mul(divisor[i], factor)
    return result


def _data_codewords(payload):
    count = len(payload)
    for version in range(1, 10):
        ecc_len, g1n, g1d, g2n, g2d = _ECC_TABLE[version]
        capacity = g1n * g1d + g2n * g2d
        if count + 2 <= capacity:  # mode+count overhead = 2 bytes for v1-9
            break
    else:
        raise ValueError("Text too long for QR version 9")

    bits = []

    def append(value, length):
        for i in range(length - 1, -1, -1):
            bits.append((value >> i) & 1)

    append(0b0100, 4)           # byte mode
    append(len(payload), 8)     # character count (versions 1-9)
    for byte in payload:
        append(byte, 8)

    capacity_bits = capacity * 8
    append(0, min(4, capacity_bits - len(bits)))
    while len(bits) % 8:
        bits.append(0)
    pads = [0xEC, 0x11]
    pad_index = 0
    while len(bits) < capacity_bits:
        append(pads[pad_index % 2], 8)
        pad_index += 1

    data_bytes = [int("".join(str(b) for b in bits[i:i + 8]), 2)
                  for i in range(0, len(bits), 8)]

    blocks = []
    pos = 0
    for _ in range(g1n):
        blocks.append(data_bytes[pos:pos + g1d]); pos += g1d
    for _ in range(g2n):
        blocks.append(data_bytes[pos:pos + g2d]); pos += g2d

    divisor = _rs_divisor(ecc_len)
    ecc_blocks = [_rs_remainder(block, divisor) for block in blocks]

    final = []
    for i in range(max(len(b) for b in blocks)):
        for block in blocks:
            if i < len(block):
                final.append(block[i])
    for i in range(ecc_len):
        for ecc in ecc_blocks:
            final.append(ecc[i])
    return version, final


def _mask_fn(mask, x, y):
    if mask == 0: return (x + y) % 2 == 0
    if mask == 1: return y % 2 == 0
    if mask == 2: return x % 3 == 0
    if mask == 3: return (x + y) % 3 == 0
    if mask == 4: return (y // 2 + x // 3) % 2 == 0
    if mask == 5: return x * y % 2 + x * y % 3 == 0
    if mask == 6: return (x * y % 2 + x * y % 3) % 2 == 0
    return ((x + y) % 2 + x * y % 3) % 2 == 0


def _penalty(modules, size):
    score = 0
    # Rules 1 & 2: runs and 2x2 blocks
    for y in range(size):
        for x in range(size):
            color = modules[y][x]
            run = 1
            while x + run < size and modules[y][x + run] == color:
                run += 1
            if run >= 5:
                score += 3 + (run - 5)
            run = 1
            while y + run < size and modules[y + run][x] == color:
                run += 1
            if run >= 5:
                score += 3 + (run - 5)
            if x + 1 < size and y + 1 < size:
                if color == modules[y][x + 1] == modules[y + 1][x] == modules[y + 1][x + 1]:
                    score += 3
    # Rule 3: finder-like patterns 1:1:3:1:1 with 4 light modules on a side
    pattern = [True, False, True, True, True, False, True]
    for y in range(size):
        for x in range(size - 6):
            if modules[y][x:x + 7] == pattern:
                if (x >= 4 and modules[y][x - 4:x] == [False] * 4) or \
                   (x + 11 <= size and modules[y][x + 7:x + 11] == [False] * 4):
                    score += 40
    for x in range(size):
        for y in range(size - 6):
            col = [modules[y + i][x] for i in range(7)]
            if col == pattern:
                if (y >= 4 and [modules[y + i][x] for i in range(-4, 0)] == [False] * 4) or \
                   (y + 11 <= size and [modules[y + i][x] for i in range(7, 11)] == [False] * 4):
                    score += 40
    # Rule 4: dark module ratio
    dark = sum(row.count(True) for row in modules)
    deviation = abs(dark * 20 - size * size * 10) // (size * size)
    score += deviation * 10
    return score


def _build_matrix(version, codewords):
    size = version * 4 + 17
    modules = [[False] * size for _ in range(size)]
    is_function = [[False] * size for _ in range(size)]

    def put(x, y, dark):
        if 0 <= x < size and 0 <= y < size:
            modules[y][x] = dark
            is_function[y][x] = True

    # Timing patterns first — finder patterns are drawn over them afterwards.
    for i in range(size):
        put(6, i, i % 2 == 0)
        put(i, 6, i % 2 == 0)

    # Finder patterns + separators
    for cx, cy in ((3, 3), (size - 4, 3), (3, size - 4)):
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                dist = max(abs(dx), abs(dy))
                put(cx + dx, cy + dy, dist != 2 and dist != 4)

    # Alignment patterns
    centers = _ALIGNMENT[version]
    for i, cx in enumerate(centers):
        for j, cy in enumerate(centers):
            if (i == 0 and j == 0) or (i == 0 and j == len(centers) - 1) or \
               (i == len(centers) - 1 and j == 0):
                continue
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    put(cx + dx, cy + dy, max(abs(dx), abs(dy)) != 1)

    # Format info (EC level M = 00)
    def set_format(mask):
        data = mask  # (00 << 3) | mask
        rem = data
        for _ in range(10):
            rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        bits = ((data << 10) | rem) ^ 0x5412
        bit = lambda i: (bits >> i) & 1
        for i in range(6): put(8, i, bit(i))
        put(8, 7, bit(6))
        put(8, 8, bit(7))
        put(7, 8, bit(8))
        for i in range(9, 15): put(14 - i, 8, bit(i))
        for i in range(8): put(size - 1 - i, 8, bit(i))
        for i in range(8, 15): put(8, size - 15 + i, bit(i))
        put(8, size - 8, True)

    set_format(0)

    # Data placement
    bit_index = 0
    total_bits = len(codewords) * 8
    right = size - 1
    while right >= 1:
        if right == 6:
            right = 5  # skip the vertical timing pattern column
        for vert in range(size):
            for j in range(2):
                x = right - j
                upward = ((right + 1) & 2) == 0
                y = size - 1 - vert if upward else vert
                if not is_function[y][x]:
                    if bit_index < total_bits:
                        modules[y][x] = ((codewords[bit_index >> 3] >> (7 - (bit_index & 7))) & 1) == 1
                        bit_index += 1
                    else:
                        modules[y][x] = False
        right -= 2

    # Choose the best mask
    best_mask, best_score = 0, None
    for mask in range(8):
        for y in range(size):
            for x in range(size):
                if not is_function[y][x] and _mask_fn(mask, x, y):
                    modules[y][x] = not modules[y][x]
        set_format(mask)
        score = _penalty(modules, size)
        if best_score is None or score < best_score:
            best_mask, best_score = mask, score
        for y in range(size):
            for x in range(size):
                if not is_function[y][x] and _mask_fn(mask, x, y):
                    modules[y][x] = not modules[y][x]
        set_format(0)

    # Apply the winning mask
    for y in range(size):
        for x in range(size):
            if not is_function[y][x] and _mask_fn(best_mask, x, y):
                modules[y][x] = not modules[y][x]
    set_format(best_mask)
    return modules


def qr_svg(text, border=3):
    """Return an SVG string for ``text`` encoded as a QR code."""
    version, codewords = _data_codewords(text.encode("utf-8"))
    modules = _build_matrix(version, codewords)
    size = len(modules)
    dimension = size + border * 2
    paths = []
    for y, row in enumerate(modules):
        for x, dark in enumerate(row):
            if dark:
                paths.append(f"M{x + border} {y + border}h1v1h-1z")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {dimension} {dimension}" '
        f'shape-rendering="crispEdges" role="img" aria-label="QR code for {text}">'
        f'<rect width="{dimension}" height="{dimension}" fill="#ffffff"/>'
        f'<path d="{"".join(paths)}" fill="#09090B"/></svg>'
    )
