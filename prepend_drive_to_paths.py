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

def replace_base_anywhere(s: str, drive: str, base: str | None) -> str:
    """Replace occurrences of the provided base substring anywhere in `s`.

    Matches both forward- and back-slash separators in the provided base
    and removes any separator characters that immediately follow the base
    so the resulting replacement becomes `<DRIVE>:/<suffix>`.
    """
    if not (drive and base):
        return s

    drive_letter = str(drive).upper().rstrip(':/')
    # Normalize the base for building a regex that matches either slash type
    base_norm = base.replace('\\', '/').rstrip('/')
    # Escape then allow either slash as separator between path segments
    pattern_str = re.escape(base_norm).replace('/', r'[\\/]') + r'[\\/]*'
    pattern = re.compile(pattern_str, flags=re.IGNORECASE)

    replacement = f"{drive_letter}:" + chr(92)
    # Use a function replacement so that backslashes in `replacement` are
    # inserted literally and do not get interpreted as escape sequences
    # in the replacement template.
    return pattern.sub(lambda m: replacement, s)


def process_lines(input_lines, drive: str, base: str | None = None):
    output_lines = []
    filtered_count = 0
    # When both drive and base are provided, perform a global replacement of
    # the base substring anywhere in each line. Otherwise, preserve the
    # previous behavior of only attempting to update `-I` include tokens.
    do_global = bool(drive and base)

    for raw in input_lines:
        line = raw.rstrip('\n')
        if not line.strip():
            continue

        if line.startswith("dir::"):
            out_line = line
            if do_global:
                out_line = replace_base_anywhere(out_line, drive, base)
            output_lines.append(out_line)
            continue

        if line.startswith("cmd::"):
            cmd_payload = line[len("cmd::"):]
            if do_global:
                # Replace base occurrences anywhere in the command payload.
                filtered_cmd = replace_base_anywhere(cmd_payload, drive, base)
            else:
                # No global replacement requested — leave the command payload
                # unchanged (previous include-only helper removed).
                filtered_cmd = cmd_payload

            output_lines.append(f"cmd::{filtered_cmd}")
            filtered_count += 1
            continue

        # Other lines: apply global replacement when requested, otherwise pass
        # them through unchanged.
        out_line = line
        if do_global:
            out_line = replace_base_anywhere(out_line, drive, base)
        output_lines.append(out_line)

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