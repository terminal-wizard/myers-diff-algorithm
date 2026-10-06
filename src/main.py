import sys


def read_lines(path):
    with open(path, "rb") as f:
        data = f.read()
    parts = data.split(b"\n")
    if parts and parts[-1] == b"":
        parts.pop()
    return parts


def myers(a, b):
    n = len(a)
    m = len(b)
    p = 0
    while p < n and p < m and a[p] == b[p]:
        p += 1
    qn = n
    qm = m
    while qn > p and qm > p and a[qn - 1] == b[qm - 1]:
        qn -= 1
        qm -= 1
    ops = []
    for i in range(p):
        ops.append(("=", a[i]))
    if p < qn or p < qm:
        ops.extend(_fallback_core(a[p:qn], b[p:qm]))
    for i in range(qn, n):
        ops.append(("=", a[i]))
    return ops


def _solve(a, b, i0, i1, j0, j1, ops):
    n = i1 - i0
    m = j1 - j0
    if n == 0:
        ops.extend(("+", x) for x in b[j0:j1])
        return
    if m == 0:
        ops.extend(("-", x) for x in a[i0:i1])
        return
    p = 0
    while p < n and p < m and a[i0 + p] == b[j0 + p]:
        p += 1
    qn = n
    qm = m
    while qn > p and qm > p and a[i0 + qn - 1] == b[j0 + qm - 1]:
        qn -= 1
        qm -= 1
    for t in range(p):
        ops.append(("=", a[i0 + t]))
    _solve_mid(a, b, i0 + p, i0 + qn, j0 + p, j0 + qm, ops)
    for t in range(qn, n):
        ops.append(("=", a[i0 + t]))


def _solve_mid(a, b, i0, i1, j0, j1, ops):
    n = i1 - i0
    m = j1 - j0
    if n == 0:
        ops.extend(("+", x) for x in b[j0:j1])
        return
    if m == 0:
        ops.extend(("-", x) for x in a[i0:i1])
        return
    D = _distance(a, b, i0, i1, j0, j1)
    if D == 0:
        for t in range(n):
            ops.append(("=", a[i0 + t]))
        return
    if D == 1:
        if n == m + 1:
            for i in range(n):
                if a[i0:i0 + i] + a[i0 + i + 1:i1] == b[j0:j1]:
                    for t in range(i):
                        ops.append(("=", a[i0 + t]))
                    ops.append(("-", a[i0 + i]))
                    for t in range(i + 1, n):
                        ops.append(("=", a[i0 + t]))
                    return
        if m == n + 1:
            for i in range(m):
                if b[j0:j0 + i] + b[j0 + i + 1:j1] == a[i0:i1]:
                    for t in range(i):
                        ops.append(("=", a[i0 + t]))
                    ops.append(("+", b[j0 + i]))
                    for t in range(i, n):
                        ops.append(("=", a[i0 + t]))
                    return
    if D <= 16:
        ops.extend(_small_trace(a, b, i0, i1, j0, j1, D))
        return
    d = D // 2
    e = D - d
    vf = _row(a, b, i0, i1, j0, j1, d, False)
    vr = _row(a, b, i0, i1, j0, j1, e, True)
    off = n + m
    delta = n - m
    xb = yb = -1
    for k in range(-d, d + 1, 2):
        x = vf[k + off]
        K = delta - k
        if -e <= K <= e:
            cand = n - vr[K + off]
            ycand = cand - k
            if 0 <= cand <= x and 0 <= ycand and ycand <= x - k:
                xb = cand
                yb = ycand
                break
    vf = vr = None
    if xb < 0:
        ops.extend(_fallback_core(a[i0:i1], b[j0:j1]))
        return
    _solve(a, b, i0, i0 + xb, j0, j0 + yb, ops)
    _solve(a, b, i0 + xb, i1, j0 + yb, j1, ops)


def _small_trace(a, b, i0, i1, j0, j1, maxd):
    n = i1 - i0
    m = j1 - j0
    off = maxd
    V = [0] * (2 * maxd + 1)
    trace = []
    found = maxd
    for D in range(maxd + 1):
        for k in range(-D, D + 1, 2):
            if k == -D or (k != D and V[k - 1 + off] < V[k + 1 + off]):
                x = V[k + 1 + off]
            else:
                x = V[k - 1 + off] + 1
            y = x - k
            while x < n and y < m and a[i0 + x] == b[j0 + y]:
                x += 1
                y += 1
            V[k + off] = x
            if x >= n and y >= m:
                found = D
                trace.append(V[:])
                break
        else:
            trace.append(V[:])
            continue
        break
    rev = []
    x = n
    y = m
    for D in range(found, 0, -1):
        k = x - y
        prev_row = trace[D - 1]
        if k == -D or (k != D and prev_row[k - 1 + off] < prev_row[k + 1 + off]):
            pk = k + 1
        else:
            pk = k - 1
        px = prev_row[pk + off]
        py = px - pk
        if pk == k + 1:
            sx = px
            sy = py + 1
            while x > sx and y > sy:
                x -= 1
                y -= 1
                rev.append(("=", a[i0 + x]))
            rev.append(("+", b[j0 + py]))
        else:
            sx = px + 1
            sy = py
            while x > sx and y > sy:
                x -= 1
                y -= 1
                rev.append(("=", a[i0 + x]))
            rev.append(("-", a[i0 + px]))
        x = px
        y = py
    rev.reverse()
    return rev


def _fallback_core(a, b):
    n = len(a)
    m = len(b)
    if n == 0:
        return [("+", x) for x in b]
    if m == 0:
        return [("-", x) for x in a]
    maxd = n + m
    off = maxd
    size = 2 * maxd + 1
    V = [0] * size
    trace = []
    found = maxd
    for D in range(maxd + 1):
        for k in range(-D, D + 1, 2):
            if k == -D or (k != D and V[k - 1 + off] < V[k + 1 + off]):
                x = V[k + 1 + off]
            else:
                x = V[k - 1 + off] + 1
            y = x - k
            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1
            V[k + off] = x
            if x >= n and y >= m:
                found = D
                trace.append(V[:])
                break
        else:
            trace.append(V[:])
            continue
        break
    rev = []
    x = n
    y = m
    for D in range(found, 0, -1):
        k = x - y
        prev_row = trace[D - 1]
        if k == -D or (k != D and prev_row[k - 1 + off] < prev_row[k + 1 + off]):
            pk = k + 1
        else:
            pk = k - 1
        px = prev_row[pk + off]
        py = px - pk
        if pk == k + 1:
            sx = px
            sy = py + 1
            while x > sx and y > sy:
                x -= 1
                y -= 1
                rev.append(("=", a[x]))
            rev.append(("+", b[py]))
        else:
            sx = px + 1
            sy = py
            while x > sx and y > sy:
                x -= 1
                y -= 1
                rev.append(("=", a[x]))
            rev.append(("-", a[px]))
        x = px
        y = py
    while x > 0 and y > 0 and a[x - 1] == b[y - 1]:
        x -= 1
        y -= 1
        rev.append(("=", a[x]))
    rev.reverse()
    return rev


def _distance(a, b, i0, i1, j0, j1):
    n = i1 - i0
    m = j1 - j0
    if n == 0:
        return m
    if m == 0:
        return n
    maxd = n + m
    off = maxd
    V = [0] * (2 * maxd + 1)
    target = n - m
    for D in range(maxd + 1):
        for k in range(-D, D + 1, 2):
            if k == -D or (k != D and V[k - 1 + off] < V[k + 1 + off]):
                x = V[k + 1 + off]
            else:
                x = V[k - 1 + off] + 1
            y = x - k
            while x < n and y < m and a[i0 + x] == b[j0 + y]:
                x += 1
                y += 1
            V[k + off] = x
        if V[target + off] >= n:
            return D
    return n + m


def _row(a, b, i0, i1, j0, j1, d, rev):
    n = i1 - i0
    m = j1 - j0
    maxd = n + m
    off = maxd
    V = [0] * (2 * maxd + 1)
    if rev:
        for D in range(d + 1):
            for k in range(-D, D + 1, 2):
                if k == -D or (k != D and V[k - 1 + off] < V[k + 1 + off]):
                    x = V[k + 1 + off]
                else:
                    x = V[k - 1 + off] + 1
                y = x - k
                while x < n and y < m and a[i1 - 1 - x] == b[j1 - 1 - y]:
                    x += 1
                    y += 1
                V[k + off] = x
        return V
    for D in range(d + 1):
        for k in range(-D, D + 1, 2):
            if k == -D or (k != D and V[k - 1 + off] < V[k + 1 + off]):
                x = V[k + 1 + off]
            else:
                x = V[k - 1 + off] + 1
            y = x - k
            while x < n and y < m and a[i0 + x] == b[j0 + y]:
                x += 1
                y += 1
            V[k + off] = x
    return V


def line_ops(lines_a, lines_b):
    return myers(lines_a, lines_b)


def change_positions(a, b):
    ops = myers(a, b)
    old_marks = []
    new_marks = []
    i = 0
    j = 0
    for op, ch in ops:
        if op == "=":
            i += 1
            j += 1
        elif op == "-":
            old_marks.append(i)
            i += 1
        else:
            new_marks.append(j)
            j += 1
    return old_marks, new_marks


def ranges(marks):
    if not marks:
        return "."
    out = []
    s = marks[0]
    t = s + 1
    for x in marks[1:]:
        if x == t:
            t += 1
        else:
            out.append(str(s) + "-" + str(t))
            s = x
            t = x + 1
    out.append(str(s) + "-" + str(t))
    return ",".join(out)


def highlight(old, new):
    om, nm = change_positions(old, new)
    return ranges(om), ranges(nm)


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ("lines", "highlight"):
        print("usage: diff.py lines|highlight A B", file=sys.stderr)
        sys.exit(2)
    mode = sys.argv[1]
    try:
        a = read_lines(sys.argv[2])
        b = read_lines(sys.argv[3])
    except Exception:
        print("error: cannot read file", file=sys.stderr)
        sys.exit(2)
    ops = line_ops(a, b)
    out = bytearray()
    i = 0
    while i < len(ops):
        if ops[i][0] == "=":
            out.extend(b" " + ops[i][1] + b"\n")
            i += 1
            continue
        dels = []
        inss = []
        while i < len(ops) and ops[i][0] != "=":
            if ops[i][0] == "-":
                dels.append(ops[i][1])
            else:
                inss.append(ops[i][1])
            i += 1
        for d0 in dels:
            out.extend(b"-" + d0 + b"\n")
        for idx, ins in enumerate(inss):
            out.extend(b"+" + ins + b"\n")
            if mode == "highlight" and idx < len(dels):
                old = dels[idx].decode("utf-8")
                new = ins.decode("utf-8")
                o, n = highlight(old, new)
                out.extend(("? " + o + " | " + n + "\n").encode("ascii"))
    sys.stdout.buffer.write(out)


if __name__ == "__main__":
    main()
