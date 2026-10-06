import sys


def read_lines(path):
    with open(path, "rb") as f:
        data = f.read()
    parts = data.split(b"\n")
    while parts and parts[-1] == b"":
        parts.pop()
    return parts


def myers(a, b):
    return _solve(a, b)


def _solve(a, b):
    n = len(a)
    m = len(b)
    if n == 0:
        return [("+", x) for x in b]
    if m == 0:
        return [("-", x) for x in a]
    p = 0
    while p < n and p < m and a[p] == b[p]:
        p += 1
    qn = n
    qm = m
    while qn > p and qm > p and a[qn - 1] == b[qm - 1]:
        qn -= 1
        qm -= 1
    ops = [("=", x) for x in a[:p]]
    ops.extend(_solve_mid(a[p:qn], b[p:qm]))
    ops.extend(("=", x) for x in a[qn:])
    return ops


def _solve_mid(a, b):
    n = len(a)
    m = len(b)
    if n == 0:
        return [("+", x) for x in b]
    if m == 0:
        return [("-", x) for x in a]
    D = _distance(a, b)
    if D == 0:
        return [("=", x) for x in a]
    if D == 1:
        if n == m + 1:
            for i in range(n):
                if a[:i] + a[i + 1:] == b:
                    return [("=", x) for x in a[:i]] + [("-", a[i])] + [("=", x) for x in a[i + 1:]]
        if m == n + 1:
            for i in range(m):
                if b[:i] + b[i + 1:] == a:
                    return [("=", x) for x in a[:i]] + [("+", b[i])] + [("=", x) for x in a[i:]]
    d = D // 2
    e = D - d
    vf = _row(a, b, d)
    vr = _row(a[::-1], b[::-1], e)
    off = n + m
    delta = n - m
    for k in range(-d, d + 1, 2):
        x = vf[k + off]
        K = delta - k
        if -e <= K <= e:
            xb = n - vr[K + off]
            yb = xb - k
            if 0 <= xb <= x and 0 <= yb <= m and yb <= x - k:
                return _solve(a[:xb], b[:yb]) + _solve(a[xb:], b[yb:])
    return _solve_mid_fallback(a, b)


def _solve_mid_fallback(a, b):
    n = len(a)
    m = len(b)
    if n == 0:
        return [("+", x) for x in b]
    if m == 0:
        return [("-", x) for x in a]
    D = _distance(a, b)
    d = D // 2
    e = D - d
    vf = _row(a, b, d)
    vr = _row(a[::-1], b[::-1], e)
    off = n + m
    delta = n - m
    for k in range(-d, d + 1, 2):
        x = vf[k + off]
        K = delta - k
        if -e <= K <= e:
            xb = n - vr[K + off]
            yb = xb - k
            if 0 <= xb <= x and 0 <= yb <= m:
                return _solve(a[:xb], b[:yb]) + _solve(a[xb:], b[yb:])
    return []


def _distance(a, b):
    n = len(a)
    m = len(b)
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
            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1
            V[k + off] = x
        if V[target + off] >= n:
            return D


def _row(a, b, d):
    n = len(a)
    m = len(b)
    maxd = n + m
    off = maxd
    V = [0] * (2 * maxd + 1)
    for D in range(d + 1):
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
    out = sys.stdout.buffer
    i = 0
    while i < len(ops):
        if ops[i][0] == "=":
            out.write(b" " + ops[i][1] + b"\n")
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
            out.write(b"-" + d0 + b"\n")
        for idx, ins in enumerate(inss):
            out.write(b"+" + ins + b"\n")
            if mode == "highlight" and idx < len(dels):
                old = dels[idx].decode("utf-8")
                new = ins.decode("utf-8")
                o, n = highlight(old, new)
                out.write(("? " + o + " | " + n + "\n").encode("ascii"))


if __name__ == "__main__":
    main()
