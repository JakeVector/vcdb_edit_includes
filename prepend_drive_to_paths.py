#!/usr/bin/env python3

"""
Filter script for vcshell database commands.

This script reads command lines from a vcshell getallcmdlines output and
prepends a drive prefix (for example `X:/`) to each include path passed with
`-I`. By default it reads `commands.txt` from the same directory and writes
`commands_filtered.txt`.

Usage examples:
    # default: read commands.txt, write commands_filtered.txt, use X drive
    python filter_db.py

    # specify input, output, and use drive Z
    python filter_db.py commands.txt commands_filtered.txt -d Z

    # only change the drive (use default files)
    python filter_db.py -d Z

Notes:
    - The `-d/--drive` option accepts a single letter and defaults to `X`.
    - The script handles both `-I path` and `-Ipath` forms and preserves
      quoted paths.
"""

import sys
import os
import re
import argparse


def prepend_drive_to_includes(cmd: str, drive: str) -> str:
    """Prepend `<drive>:/` to each `-I` include path in a command line.

    Handles both `-I path` and `-Ipath` forms, preserves quotes if present.
    Avoids touching other multi-letter options like `-imultilib` by only
    modifying when it looks like an include path.
    """
    drive_letter = drive.upper().rstrip(':/')
    if not drive_letter:
        drive_letter = 'X'
    prefix = f"{drive_letter}:/"

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
            return f'{flag}{sep}"{prefix}{inner}"'
        else:
            return f'{flag}{sep}{prefix}{path}'

    return pattern.sub(_repl, cmd)


def process_lines(input_lines, drive: str):
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
            filtered_cmd = prepend_drive_to_includes(cmd_payload, drive)
            output_lines.append(f"cmd::{filtered_cmd}")
            filtered_count += 1
            continue

        # Pass through unknown/unprefixed lines unchanged.
        output_lines.append(line)

    return output_lines, filtered_count


def main():
    parser = argparse.ArgumentParser(description='Prepend drive letter to -I include paths in vcshell command dumps')
    parser.add_argument('input_file', nargs='?', help='Input file (default: commands.txt in script dir)')
    parser.add_argument('output_file', nargs='?', help='Output file (default: <input>_filtered or commands_filtered.txt)')
    parser.add_argument('-d', '--drive', default='X', help='Drive letter to prepend (default: X)')
    args = parser.parse_args()

    if args.input_file:
        input_file = args.input_file
    else:
        base_dir = os.path.dirname(__file__)
        input_file = os.path.join(base_dir, 'commands.txt')

    if args.output_file:
        output_file = args.output_file
    else:
        name, ext = os.path.splitext(input_file)
        if input_file.endswith('commands.txt') and not args.input_file:
            base_dir = os.path.dirname(__file__)
            output_file = os.path.join(base_dir, 'commands_filtered.txt')
        else:
            output_file = f"{name}_filtered{ext}"

    drive = args.drive

    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            input_lines = f.readlines()
    except IOError as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)

    output_lines, filtered_count = process_lines(input_lines, drive)

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