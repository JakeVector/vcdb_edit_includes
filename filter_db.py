#!/usr/bin/env python3

"""
Filter script for vcshell database commands.

This script reads command lines from a vcshell getallcmdlines output and
prepends an X:/ prefix to each include path passed with -I. By default it
reads `commands.txt` from the same directory and writes `commands_filtered.txt`.

Usage:
    filter_db.py [<input_file> [<output_file>]]

If no arguments are provided the script uses `commands.txt` and
`commands_filtered.txt` in the script directory.
"""

import sys
import os
import re


def prepend_X_to_includes(cmd: str) -> str:
    """Prepend `X:/` to each `-I` include path in a command line.

    Handles both `-I path` and `-Ipath` forms, preserves quotes if present.
    Avoids touching other multi-letter options like `-imultilib` (lowercase i
    variants) by only modifying when it looks like an include path.
    """
    pattern = re.compile(r'(-I)(\s*)(".*?"|\S+)')

    def _repl(m: re.Match) -> str:
        flag = m.group(1)
        sep = m.group(2)
        path = m.group(3)

        # If there is no separating space and the following token doesn't look
        # like a path (e.g. it's a multi-letter option), skip replacing.
        if sep == "":
            if not (path.startswith('.') or path.startswith('/') or path.startswith('..') or (len(path) > 1 and path[1] == ':') or path.startswith('~')):
                return m.group(0)

        if path.startswith('"') and path.endswith('"'):
            inner = path[1:-1]
            return f'{flag}{sep}"X:/{inner}"'
        else:
            return f'{flag}{sep}X:/{path}'

    return pattern.sub(_repl, cmd)


def process_lines(input_lines):
    output_lines = []
    filtered_count = 0

    for raw in input_lines:
        line = raw.rstrip('\n')
        if not line.strip():
            continue

        if line.startswith("dir::"):
            output_lines.append(line)
            continue

        if line.startswith("cmd::"):
            cmd_payload = line[len("cmd::"):]
            filtered_cmd = prepend_X_to_includes(cmd_payload)
            output_lines.append(f"cmd::{filtered_cmd}")
            filtered_count += 1
            continue

        # Pass through unknown/unprefixed lines unchanged.
        output_lines.append(line)

    return output_lines, filtered_count


def main():
    # Accept 0,1 or 2 args. Default to commands.txt in the script directory.
    if len(sys.argv) == 1:
        base_dir = os.path.dirname(__file__)
        input_file = os.path.join(base_dir, 'commands.txt')
        output_file = os.path.join(base_dir, 'commands_filtered.txt')
    elif len(sys.argv) == 2:
        input_file = sys.argv[1]
        name, ext = os.path.splitext(input_file)
        output_file = f"{name}_filtered{ext}"
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]

    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            input_lines = f.readlines()
    except IOError as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)

    output_lines, filtered_count = process_lines(input_lines)

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            if output_lines:
                f.write('\n'.join(output_lines))
                f.write('\n')
    except IOError as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Filtered {filtered_count} commands")
    print(f"Output written to: {output_file}")


if __name__ == '__main__':
    main()