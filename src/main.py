import sys


def read_lines(path):
    with open(path, "rb") as f:
        data = f.read()
    parts = data.split(b"\n")
    while parts and parts[-1] == b"":
        parts.pop()
    return parts


def myers(a, b):
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
    suba = a[p:qn]
    subb = b[p:qm]
    ops.extend(_myers_core(suba, subb))
    ops.extend(("=", x) for x in a[qn:])
    return ops


def _myers_core(a, b):
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
    rev.reverse()
    return rev


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
        op, val = ops[i]
        if op == "=":
            out.write(b" " + val + b"\n")
            i += 1
            continue
        dels = []
        inss = []
        while i < len(ops) and ops[i][0] != "=":
            tag, val = ops[i]
            if tag == "-":
                dels.append(val)
            else:
                inss.append(val)
            i += 1
        for d in dels:
            out.write(b"-" + d + b"\n")
        for idx, ins in enumerate(inss):
            out.write(b"+" + ins + b"\n")
            if mode == "highlight" and idx < len(dels):
                old = dels[idx].decode("utf-8")
                new = ins.decode("utf-8")
                o, n = highlight(old, new)
                out.write(("? " + o + " | " + n + "\n").encode("ascii"))


if __name__ == "__main__":
    main()
