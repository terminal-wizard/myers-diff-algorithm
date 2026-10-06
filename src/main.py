import sys


def _furthest(a, b, dmax):
    n = len(a)
    m = len(b)
    V = {}
    x = 0
    while x < n and x < m and a[x] == b[x]:
        x += 1
    V[0] = x
    for d in range(1, dmax + 1):
        Vn = {}
        for k in range(-d, d + 1, 2):
            xc = -1
            v = V.get(k + 1)
            if v is not None:
                xc = v
            v = V.get(k - 1)
            if v is not None and v + 1 > xc:
                xc = v + 1
            if xc < 0:
                continue
            x = xc
            y = x - k
            if x > n or y > m or y < 0:
                continue
            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1
            Vn[k] = x
        V = Vn
    return V


def _dist(a, b):
    n = len(a)
    m = len(b)
    if n == 0:
        return m
    if m == 0:
        return n
    V = {}
    x = 0
    while x < n and x < m and a[x] == b[x]:
        x += 1
    V[0] = x
    if x == n and x == m:
        return 0
    target = n - m
    d = 0
    while True:
        d += 1
        Vn = {}
        for k in range(-d, d + 1, 2):
            xc = -1
            v = V.get(k + 1)
            if v is not None:
                xc = v
            v = V.get(k - 1)
            if v is not None and v + 1 > xc:
                xc = v + 1
            if xc < 0:
                continue
            x = xc
            y = x - k
            if x > n or y > m or y < 0:
                continue
            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1
            Vn[k] = x
        V = Vn
        if V.get(target, -1) >= n:
            return d


def _solve(a, b, i0, i1, j0, j1, out):
    if i0 == i1:
        for j in range(j0, j1):
            out.append(('+', -1, j))
        return
    if j0 == j1:
        for i in range(i0, i1):
            out.append(('-', i, -1))
        return
    while i0 < i1 and j0 < j1 and a[i0] == b[j0]:
        out.append(('=', i0, j0))
        i0 += 1
        j0 += 1
    if i0 == i1:
        for j in range(j0, j1):
            out.append(('+', -1, j))
        return
    if j0 == j1:
        for i in range(i0, i1):
            out.append(('-', i, -1))
        return
    i2, j2 = i1, j1
    while i2 > i0 and j2 > j0 and a[i2 - 1] == b[j2 - 1]:
        i2 -= 1
        j2 -= 1
    if i2 == i0:
        for j in range(j0, j2):
            out.append(('+', -1, j))
        for t in range(i1 - i2):
            out.append(('=', i2 + t, j2 + t))
        return
    if j2 == j0:
        for i in range(i0, i2):
            out.append(('-', i, -1))
        for t in range(i1 - i2):
            out.append(('=', i2 + t, j2 + t))
        return
    A = a[i0:i2]
    B = b[j0:j2]
    D = _dist(A, B)
    if D == 0:
        for t in range(i2 - i0):
            out.append(('=', i0 + t, j0 + t))
    elif D == 1:
        n2 = i2 - i0
        m2 = j2 - j0
        p = 0
        while p < n2 and p < m2 and A[p] == B[p]:
            p += 1
        if m2 == n2 + 1:
            for t in range(p):
                out.append(('=', i0 + t, j0 + t))
            out.append(('+', -1, j0 + p))
            for t in range(p, n2):
                out.append(('=', i0 + t, j0 + p + 1))
        else:
            for t in range(p):
                out.append(('=', i0 + t, j0 + t))
            out.append(('-', i0 + p, -1))
            for t in range(p, m2):
                out.append(('=', i0 + t + 1, j0 + t))
    else:
        df = (D + 1) // 2
        dr = D - df
        n2 = i2 - i0
        m2 = j2 - j0
        Vf = _furthest(A, B, df)
        W = _furthest(A[::-1], B[::-1], dr)
        split = None
        for k in range(-df, df + 1, 2):
            kp = (n2 - m2) - k
            if kp < -dr or kp > dr or (kp - dr) & 1:
                continue
            xf = Vf.get(k)
            xr = W.get(kp)
            if xf is None or xr is None:
                continue
            if xf + xr >= n2:
                split = (n2 - xr, m2 - (xr - kp))
                break
        if split is None:
            for xp in range(n2 + 1):
                for yp in range(m2 + 1):
                    if _dist(A[:xp], B[:yp]) + _dist(A[xp:], B[yp:]) == D:
                        split = (xp, yp)
                        break
                if split is not None:
                    break
        xp, yp = split
        _solve(a, b, i0, i0 + xp, j0, j0 + yp, out)
        _solve(a, b, i0 + xp, i2, j0 + yp, j2, out)
    for t in range(i1 - i2):
        out.append(('=', i2 + t, j2 + t))


def diff_seq(a, b):
    out = []
    _solve(a, b, 0, len(a), 0, len(b), out)
    return out


def _ranges(pos):
    if not pos:
        return "."
    parts = []
    start = pos[0]
    prev = pos[0]
    for p in pos[1:]:
        if p == prev + 1:
            prev = p
            continue
        parts.append("%d-%d" % (start, prev + 1))
        start = p
        prev = p
    parts.append("%d-%d" % (start, prev + 1))
    return ",".join(parts)


def _hunk_ranges(old, new):
    s = old.decode("utf-8")
    t = new.decode("utf-8")
    ops = diff_seq(s, t)
    del_pos = []
    ins_pos = []
    for op in ops:
        if op[0] == '-':
            del_pos.append(op[1])
        elif op[0] == '+':
            ins_pos.append(op[2])
    return (_ranges(del_pos).encode("ascii") + b" | " +
            _ranges(ins_pos).encode("ascii"))


def _emit(a, b, ops, highlight):
    chunks = []
    i = 0
    n = len(ops)
    while i < n:
        op = ops[i]
        if op[0] == '=':
            chunks.append(b" " + a[op[1]] + b"\n")
            i += 1
            continue
        dels = []
        inss = []
        while i < n and ops[i][0] != '=':
            if ops[i][0] == '-':
                dels.append(ops[i][1])
            else:
                inss.append(ops[i][2])
            i += 1
        for ix in dels:
            chunks.append(b"-" + a[ix] + b"\n")
        for t in range(len(inss)):
            chunks.append(b"+" + b[inss[t]] + b"\n")
            if highlight and t < len(dels):
                chunks.append(b"? " +
                              _hunk_ranges(a[dels[t]], b[inss[t]]) + b"\n")
    return b"".join(chunks)


def _read_lines(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
    except Exception:
        sys.stderr.write("error: cannot read file: " + repr(path) + "\n")
        sys.exit(2)
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    return lines


def main():
    args = sys.argv
    if len(args) != 4 or (args[1] != "lines" and args[1] != "highlight"):
        sys.stderr.write("error: usage: python diff.py <lines|highlight> A B\n")
        sys.exit(2)
    a = _read_lines(args[2])
    b = _read_lines(args[3])
    ops = diff_seq(a, b)
    data = _emit(a, b, ops, args[1] == "highlight")
    sys.stdout.buffer.write(data)


if __name__ == "__main__":
    main()
