#!/usr/bin/env python3
"""
Hashcat-AutoSplitter
Identifies, sorts, and extracts various hash formats from raw input files,
saving them into dedicated files and generating the exact Hashcat commands.
"""

import argparse
from collections import defaultdict
import os
from pathlib import Path
import re
import sys

# Define hash identification signatures, file naming prefixes, and Hashcat modes
HASH_DEFINITIONS = {
    "krb5tgs": {
        "name": "Kerberos 5 TGS-REP (Kerberoasting)",
        "mode": "13100",
        "pattern": re.compile(
            r"^\$krb5tgs\$\d+\$[^\$]+\$[^\$]+\$\*?[^\$]*\$[a-fA-F0-9]+.*$"
        ),
        "filename": "krb5tgs_13100.txt",
    },
    "krb5asrep": {
        "name": "Kerberos 5 AS-REP (AS-REP Roasting)",
        "mode": "18200",
        "pattern": re.compile(
            r"^\$krb5asrep\$\d+\$[^\$]+@[^\$]+:[a-fA-F0-9]+.*$"
        ),
        "filename": "krb5asrep_18200.txt",
    },
    "netntlmv2": {
        "name": "NetNTLMv2 / NTLMv2 (Responder/Inveigh)",
        "mode": "5600",
        "pattern": re.compile(
            r"^[^:]+::[^:]*:[a-fA-F0-9]{16}:[a-fA-F0-9]{32}:[a-fA-F0-9]+$"
        ),
        "filename": "netntlmv2_5600.txt",
    },
    "netntlmv1": {
        "name": "NetNTLMv1 / NTLMv1",
        "mode": "5500",
        "pattern": re.compile(
            r"^[^:]+::[^:]*:[a-fA-F0-9]{48}:[a-fA-F0-9]{48}:[a-fA-F0-9]{16}$"
        ),
        "filename": "netntlmv1_5500.txt",
    },
    "sha512crypt": {
        "name": "Linux SHA512-Crypt ($6$ shadow)",
        "mode": "1800",
        "pattern": re.compile(
            r"^(\w+:)?\$6\$[a-zA-Z0-9.\/]{1,16}\$[a-zA-Z0-9.\/]{86}(:.*)?$"
        ),
        "filename": "sha512crypt_1800.txt",
    },
    "sha256crypt": {
        "name": "Linux SHA256-Crypt ($5$ shadow)",
        "mode": "7400",
        "pattern": re.compile(
            r"^(\w+:)?\$5\$[a-zA-Z0-9.\/]{1,16}\$[a-zA-Z0-9.\/]{43}(:.*)?$"
        ),
        "filename": "sha256crypt_7400.txt",
    },
    "ntlm": {
        "name": "NTLM / MD4 (32 Hex Characters)",
        "mode": "1000",
        "pattern": re.compile(r"^[a-fA-F0-9]{32}$"),
        "filename": "ntlm_1000.txt",
    },
    "bcrypt": {
        "name": "Bcrypt / Blowfish ($2a$, $2b$, $2y$)",
        "mode": "3200",
        "pattern": re.compile(
            r"^(\w+:)?\$2[abxy]\$\d{2}\$[a-zA-Z0-9.\/]{53}(:.*)?$"
        ),
        "filename": "bcrypt_3200.txt",
    },
}


def identify_hash(line: str) -> str | None:
  """Matches a stripped input line against known regex signatures."""
  for key, data in HASH_DEFINITIONS.items():
    if data["pattern"].match(line):
      return key
  return None


def parse_and_sort(
    input_file: Path, output_dir: Path, wordlist_path: str
) -> None:
  """Reads the raw file, sorts entries, writes output files, and displays summary."""
  if not input_file.is_file():
    print(f"[!] Error: Input file '{input_file}' not found.")
    sys.exit(1)

  output_dir.mkdir(parents=True, exist_ok=True)

  sorted_hashes = defaultdict(set)
  unrecognized = set()
  total_lines = 0

  print(f"[*] Reading: {input_file}")
  with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
      clean_line = line.strip()
      if not clean_line or clean_line.startswith("#"):
        continue

      total_lines += 1
      hash_type = identify_hash(clean_line)

      if hash_type:
        sorted_hashes[hash_type].add(clean_line)
      else:
        unrecognized.add(clean_line)

  print(f"[+] Processed {total_lines} lines.\n")

  # Write identified hashes to individual files
  commands = []

  for hash_type, items in sorted_hashes.items():
    info = HASH_DEFINITIONS[hash_type]
    out_file = output_dir / info["filename"]

    with open(out_file, "w", encoding="utf-8") as f:
      for item in items:
        f.write(f"{item}\n")

    print(
        f"  [>] {info['name']}: {len(items)} unique hash(es) -> {out_file.name}"
    )

    # Build ready-to-run Hashcat command string
    cmd = (
        f"hashcat -m {info['mode']} {out_file} {wordlist_path} -O -w 3"
        " --status"
    )
    commands.append((info["name"], cmd))

  # Write unrecognized entries to a separate review file
  if unrecognized:
    unknown_file = output_dir / "unrecognized.txt"
    with open(unknown_file, "w", encoding="utf-8") as f:
      for item in unrecognized:
        f.write(f"{item}\n")
    print(
        f"  [?] Unrecognized items: {len(unrecognized)} line(s) ->"
        f" {unknown_file.name}"
    )

  # Output suggested execution commands
  if commands:
    print("\n" + "=" * 70)
    print("Generated Hashcat Commands:")
    print("=" * 70)
    for name, cmd in commands:
      print(f"# {name}\n{cmd}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Hashcat-AutoSplitter: Classify, extract, and sort password hashes into dedicated files."
    )
    # Changed required=True to required=False
    parser.add_argument(
        "-i", "--input",
        required=False,
        type=Path,
        help="Path to the raw dump file containing hashes."
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("sorted_hashes"),
        help="Directory to save sorted hash files (default: ./sorted_hashes)."
    )
    parser.add_argument(
        "-w", "--wordlist",
        type=str,
        default="/usr/share/wordlists/rockyou.txt",
        help="Wordlist path for generated commands (default: /usr/share/wordlists/rockyou.txt)."
    )

    args = parser.parse_args()

    # If you didn't pass -i in the terminal, it asks you here instead of crashing:
    input_path = args.input
    if not input_path:
        try:
            user_input = input("[?] Enter the path to your raw hash file: ").strip()
            if not user_input:
                print("[!] Error: No input file entered.")
                sys.exit(1)
            input_path = Path(user_input)
        except (KeyboardInterrupt, EOFError):
            print("\n[!] Exiting.")
            sys.exit(0)

    parse_and_sort(input_path, args.output_dir, args.wordlist)


if __name__ == "__main__":
  main()