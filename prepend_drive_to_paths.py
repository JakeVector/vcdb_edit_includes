#!/usr/bin/env python3

"""
Filter script for vcshell database commands.

This script reads command lines from a vcshell getallcmdlines output and,
when both a `--drive` and a `--base` substring are provided, replaces the
portion of each `-I` include path up to and including that base substring
with the specified drive prefix (for example `X:/`). By default it reads
`commands.txt` from the same directory and writes `commands_filtered.txt`.

Usage examples:
    # default: read commands.txt, write commands_filtered.txt, do nothing
    python prepend_drive_to_paths.py

    # specify input, output, and use drive/base replacement
    python prepend_drive_to_paths.py commands.txt commands_filtered.txt -d Z -b "../../SIP/CBD2401322_D01"

Notes:
    - The script is a no-op by default and will not modify include paths.
    - Modifications occur only when BOTH `-d/--drive` and `-b/--base` are provided.
      In that case the script replaces the portion of an `-I` include path up to
      and including the provided base substring with `<DRIVE>:/` and preserves the
      remainder of the path (leading separators removed).
    - The script handles both `-I path` and `-Ipath` forms and preserves quoted paths.
"""

import sys
import os
import re
import argparse


def prepend_drive_to_includes(cmd: str, drive: str, base: str | None = None) -> str:
    """Modify `-I` include paths in a command line.

    If `base` is provided and `drive` is provided and the base substring is
    found inside an include path, the portion of the path up to/including
    the base is replaced with `<DRIVE>:/` and the remainder is preserved.
    The function performs no modifications unless BOTH `drive` and `base`
    are supplied. Handles both `-I path` and `-Ipath` forms, preserves
    quotes if present, and avoids touching other multi-letter options like
    `-imultilib`.
    """
    drive_letter = str(drive).upper().rstrip(':/') if drive is not None else None
    prefix = f"{drive_letter}:/" if drive_letter else None

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

        # Work with the raw inner path (without quotes) for matching.
        quoted = path.startswith('"') and path.endswith('"')
        inner = path[1:-1] if quoted else path

        # Only perform replacements when BOTH a drive and a base substring are
        # provided. If either is missing, leave the include unchanged.
        if not (base and drive_letter):
            return m.group(0)

        # If base provided and drive provided, replace up to base with drive prefix.
        idx = inner.find(base)
        if idx != -1:
            # take the suffix after the matched base
            suffix = inner[idx + len(base):]
            # remove leading separators from suffix
            suffix = suffix.lstrip('/\\')
            new_inner = f"{drive_letter}:/{suffix}" if suffix else f"{drive_letter}:/"
            return f"{flag}{sep}\"{new_inner}\"" if quoted else f"{flag}{sep}{new_inner}"

        # If base not found, leave unchanged
        return m.group(0)

    return pattern.sub(_repl, cmd)


def process_lines(input_lines, drive: str, base: str | None = None):
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
            filtered_cmd = prepend_drive_to_includes(cmd_payload, drive, base)
            output_lines.append(f"cmd::{filtered_cmd}")
            filtered_count += 1
            continue

        # Pass through unknown/unprefixed lines unchanged.
        output_lines.append(line)

    return output_lines, filtered_count


def main():
    parser = argparse.ArgumentParser(description='Replace base substrings in -I include paths with a drive prefix (requires --drive and --base)')
    parser.add_argument('input_file', nargs='?', help='Input file (default: commands.txt in script dir)')
    parser.add_argument('output_file', nargs='?', help='Output file (default: <input>_filtered or commands_filtered.txt)')
    parser.add_argument('-d', '--drive', default=None, help='Drive letter to use when replacing the provided base substring')
    parser.add_argument('-b', '--base', default=None, help='Base directory substring to replace with the drive (required together with --drive)')
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
    base = args.base

    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            input_lines = f.readlines()
    except IOError as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)

    output_lines, filtered_count = process_lines(input_lines, drive, base)

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