"""Myers' O(ND) diff: line diff (Part A) and changed-character ranges (Part B).

The diff core operates on arbitrary hashable sequences. The CLI uses it for
line-level diffs over raw bytes and character-level diffs over strings.
"""

import sys


def read_lines(file_path):
    """Read a file as raw bytes and split it into logical lines."""
    with open(file_path, "rb") as file_handle:
        lines = file_handle.read().split(b"\n")

    # A trailing newline does not represent an additional logical line.
    if lines and not lines[-1]:
        lines.pop()

    return lines


def middle_snake(seq_a, seq_b, seq_a_reversed, seq_b_reversed, len_a, len_b):
    """Find the middle snake in the Myers edit graph.

    Returns:
        (snake_start_x, snake_start_y, snake_end_x, snake_end_y)

    representing the snake from (snake_start_x, snake_start_y) to (snake_end_x, snake_end_y).

    seq_a/seq_b and seq_a_reversed/seq_b_reversed contain one sentinel element beyond their logical bounds.
    """
    delta = len_a - len_b
    is_delta_odd = delta & 1

    max_edit_distance = (len_a + len_b + 1) // 2
    diagonal_offset = max_edit_distance + 1
    vector_size = 2 * max_edit_distance + 3

    # Furthest x reached on each diagonal.
    forward_vector = [-1] * vector_size
    backward_vector = [-1] * vector_size

    forward_vector[diagonal_offset + 1] = 0
    backward_vector[diagonal_offset + 1] = 0

    # Active diagonal boundaries.
    forward_start = forward_end = backward_start = backward_end = 0

    for current_d in range(max_edit_distance + 1):
        # ---------------------------------------------------------------
        # Forward search
        # ---------------------------------------------------------------
        d_start = -current_d + forward_start
        d_end = current_d - forward_end

        for diagonal_k in range(d_start, d_end + 1, 2):
            vector_idx = diagonal_offset + diagonal_k

            if diagonal_k == -current_d or (diagonal_k != current_d and forward_vector[vector_idx - 1] < forward_vector[vector_idx + 1]):
                # Insertion: move down.
                current_x = forward_vector[vector_idx + 1]
            else:
                # Deletion: move right.
                current_x = forward_vector[vector_idx - 1] + 1

            current_y = current_x - diagonal_k
            initial_x = current_x
            initial_y = current_y

            # Follow the snake.
            while current_x < len_a and current_y < len_b and seq_a[current_x] == seq_b[current_y]:
                current_x += 1
                current_y += 1

            forward_vector[vector_idx] = current_x

            # Remove diagonals that have left the edit graph.
            if current_x > len_a:
                forward_end += 2
                continue

            if current_y > len_b:
                forward_start += 2
                continue

            # For odd delta, the forward and backward searches can overlap.
            if is_delta_odd:
                backward_k = delta - diagonal_k
                if -current_d < backward_k < current_d:
                    backward_x = backward_vector[diagonal_offset + backward_k]
                    if backward_x != -1 and current_x + backward_x >= len_a:
                        return initial_x, initial_y, current_x, current_y

        # ---------------------------------------------------------------
        # Backward search
        # ---------------------------------------------------------------
        d_start = -current_d + backward_start
        d_end = current_d - backward_end

        for diagonal_k in range(d_start, d_end + 1, 2):
            vector_idx = diagonal_offset + diagonal_k

            if diagonal_k == -current_d or (diagonal_k != current_d and backward_vector[vector_idx - 1] < backward_vector[vector_idx + 1]):
                current_x = backward_vector[vector_idx + 1]
            else:
                current_x = backward_vector[vector_idx - 1] + 1

            current_y = current_x - diagonal_k
            initial_x = current_x
            initial_y = current_y

            # Follow the reverse snake.
            while current_x < len_a and current_y < len_b and seq_a_reversed[current_x] == seq_b_reversed[current_y]:
                current_x += 1
                current_y += 1

            backward_vector[vector_idx] = current_x

            if current_x > len_a:
                backward_end += 2
                continue

            if current_y > len_b:
                backward_start += 2
                continue

            # For even delta, check overlap with the forward search.
            if not is_delta_odd:
                forward_k = delta - diagonal_k

                if -current_d <= forward_k <= current_d:
                    forward_x = forward_vector[diagonal_offset + forward_k]
                    if forward_x != -1 and forward_x + current_x >= len_a:
                        return len_a - current_x, len_b - current_y, len_a - initial_x, len_b - initial_y

    raise RuntimeError("middle snake not found")


def diff_marks(seq_a, seq_b):
    """Compute a minimal Myers diff.

    Returns:
        deleted_marks_a:
            bytearray marking elements deleted from ``seq_a``.

        inserted_marks_b:
            bytearray marking elements inserted into ``seq_b``.

    A value of 1 means the element participates in an edit.
    A value of 0 means it is matched.
    """
    total_len_a = len(seq_a)
    total_len_b = len(seq_b)

    # Assign a compact integer ID to every distinct item.
    item_to_id = {}
    ids_sequence_a = []
    ids_sequence_b = []

    for item in seq_a:
        assigned_id = item_to_id.get(item)
        if assigned_id is None:
            assigned_id = len(item_to_id)
            item_to_id[item] = assigned_id
        ids_sequence_a.append(assigned_id)

    for item in seq_b:
        assigned_id = item_to_id.get(item)
        if assigned_id is None:
            assigned_id = len(item_to_id)
            item_to_id[item] = assigned_id
        ids_sequence_b.append(assigned_id)

    # Items occurring in only one sequence can never be part of a match.
    unique_ids_in_a = set(ids_sequence_a)
    unique_ids_in_b = set(ids_sequence_b)

    matched_indices_a = [i for i, assigned_id in enumerate(ids_sequence_a) if assigned_id in unique_ids_in_b]
    matched_indices_b = [j for j, assigned_id in enumerate(ids_sequence_b) if assigned_id in unique_ids_in_a]

    filtered_ids_a = [ids_sequence_a[i] for i in matched_indices_a]
    filtered_ids_b = [ids_sequence_b[j] for j in matched_indices_b]

    filtered_deleted_marks = bytearray(len(filtered_ids_a))
    filtered_inserted_marks = bytearray(len(filtered_ids_b))

    # Each tuple represents:
    #   [start_a:end_a] -> [start_b:end_b]
    execution_stack = [(0, len(filtered_ids_a), 0, len(filtered_ids_b))]

    while execution_stack:
        start_a, end_a, start_b, end_b = execution_stack.pop()

        # ---------------------------------------------------------------
        # Strip common prefix.
        # ---------------------------------------------------------------
        while start_a < end_a and start_b < end_b and filtered_ids_a[start_a] == filtered_ids_b[start_b]:
            start_a += 1
            start_b += 1

        # ---------------------------------------------------------------
        # Strip common suffix.
        # ---------------------------------------------------------------
        while start_a < end_a and start_b < end_b and filtered_ids_a[end_a - 1] == filtered_ids_b[end_b - 1]:
            end_a -= 1
            end_b -= 1

        # Everything on B is an insertion.
        if start_a == end_a:
            if start_b < end_b:
                filtered_inserted_marks[start_b:end_b] = b"\x01" * (end_b - start_b)
            continue

        # Everything on A is a deletion.
        if start_b == end_b:
            filtered_deleted_marks[start_a:end_a] = b"\x01" * (end_a - start_a)
            continue

        # ---------------------------------------------------------------
        # Solve the remaining problem using the middle snake.
        # ---------------------------------------------------------------
        sub_seq_a = filtered_ids_a[start_a:end_a]
        sub_seq_b = filtered_ids_b[start_b:end_b]

        sub_len_a = end_a - start_a
        sub_len_b = end_b - start_b

        sub_seq_a_rev = sub_seq_a[::-1]
        sub_seq_b_rev = sub_seq_b[::-1]

        # Sentinel values allow the middle-snake implementation to safely
        # perform comparisons at the logical boundary.
        sub_seq_a.append(-1)
        sub_seq_b.append(-2)
        sub_seq_a_rev.append(-1)
        sub_seq_b_rev.append(-2)

        snake_start_x, snake_start_y, snake_end_x, snake_end_y = middle_snake(
            sub_seq_a, sub_seq_b, sub_seq_a_rev, sub_seq_b_rev, sub_len_a, sub_len_b
        )

        # Push right side first so that the left side is processed next.
        execution_stack.append(
            (
                start_a + snake_end_x,
                end_a,
                start_b + snake_end_y,
                end_b,
            )
        )
        execution_stack.append(
            (
                start_a,
                start_a + snake_start_x,
                start_b,
                start_b + snake_start_y,
            )
        )

    # Start with everything marked as changed. Only elements that survived
    # the filtered Myers search are then replaced with their actual status.
    deleted_marks_a = bytearray(b"\x01") * total_len_a
    inserted_marks_b = bytearray(b"\x01") * total_len_b

    for filtered_index, original_index in enumerate(matched_indices_a):
        deleted_marks_a[original_index] = filtered_deleted_marks[filtered_index]

    for filtered_index, original_index in enumerate(matched_indices_b):
        inserted_marks_b[original_index] = filtered_inserted_marks[filtered_index]

    return deleted_marks_a, inserted_marks_b


def format_ranges(marks):
    """Convert a 0/1 bytearray into ``start-end,...`` ranges.

    Returns ``.`` when no elements are marked.
    """
    total_elements = len(marks)
    range_parts = []

    range_start = marks.find(1)

    while range_start != -1:
        range_end = marks.find(0, range_start)

        if range_end == -1:
            range_end = total_elements

        range_parts.append(f"{range_start}-{range_end}")

        if range_end >= total_elements:
            break

        range_start = marks.find(1, range_end)

    return ",".join(range_parts) if range_parts else "."


def build_output(sequence_a, sequence_b, deleted_marks_a, inserted_marks_b, enable_highlighting):
    """Build the textual diff output.

    Deletes are emitted before inserts, matching the original behavior.
    """
    total_len_a = len(sequence_a)
    total_len_b = len(sequence_b)

    output_buffer = []
    idx_a = idx_b = 0

    while True:
        next_delete = deleted_marks_a.find(1, idx_a)
        next_insert = inserted_marks_b.find(1, idx_b)

        if next_delete == -1 and next_insert == -1:
            break

        # Number of unchanged lines before the next edit.
        unchanged_count = total_len_a - idx_a

        if next_delete != -1:
            unchanged_count = min(unchanged_count, next_delete - idx_a)

        if next_insert != -1:
            unchanged_count = min(unchanged_count, next_insert - idx_b)

        if unchanged_count:
            output_buffer.extend(
                b" " + line
                for line in sequence_a[idx_a:idx_a + unchanged_count]
            )
            idx_a += unchanged_count
            idx_b += unchanged_count

        # ---------------------------------------------------------------
        # Consume one contiguous edit block.
        # ---------------------------------------------------------------
        delete_end = deleted_marks_a.find(0, idx_a)
        if delete_end == -1:
            delete_end = total_len_a

        insert_end = inserted_marks_b.find(0, idx_b)
        if insert_end == -1:
            insert_end = total_len_b

        deleted_lines = sequence_a[idx_a:delete_end]
        inserted_lines = sequence_b[idx_b:insert_end]

        output_buffer.extend(b"-" + line for line in deleted_lines)

        if not enable_highlighting:
            output_buffer.extend(b"+" + line for line in inserted_lines)
        else:
            paired_count = min(len(deleted_lines), len(inserted_lines))

            for index, line in enumerate(inserted_lines):
                output_buffer.append(b"+" + line)

                if index < paired_count:
                    old_str = deleted_lines[index].decode(
                        "utf-8",
                        "surrogateescape",
                    )
                    new_str = line.decode(
                        "utf-8",
                        "surrogateescape",
                    )

                    sub_deleted_marks, sub_inserted_marks = diff_marks(old_str, new_str)

                    marker_line = (
                        f"? {format_ranges(sub_deleted_marks)} | "
                        f"{format_ranges(sub_inserted_marks)}"
                    ).encode("utf-8")

                    output_buffer.append(marker_line)

        idx_a = delete_end
        idx_b = insert_end

    # Remaining unchanged tail.
    if idx_a < total_len_a:
        output_buffer.extend(b" " + line for line in sequence_a[idx_a:])

    return output_buffer


def main():
    """CLI entry point."""
    if len(sys.argv) != 4:
        print(
            "usage: main.py lines|highlight A_PATH B_PATH",
            file=sys.stderr,
        )
        return 2

    command = sys.argv[1]

    if command not in ("lines", "highlight"):
        print(
            "usage: main.py lines|highlight A_PATH B_PATH",
            file=sys.stderr,
        )
        return 2

    try:
        sequence_a = read_lines(sys.argv[2])
        sequence_b = read_lines(sys.argv[3])
    except OSError as exc:
        print(
            f"error: cannot read file: {exc}",
            file=sys.stderr,
        )
        return 2

    deleted_marks_a, inserted_marks_b = diff_marks(sequence_a, sequence_b)

    output_lines = build_output(
        sequence_a,
        sequence_b,
        deleted_marks_a,
        inserted_marks_b,
        command == "highlight",
    )

    if output_lines:
        sys.stdout.buffer.write(b"\n".join(output_lines) + b"\n")
        sys.stdout.buffer.flush()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
