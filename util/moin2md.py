#!usr/bin/env python3

# Script that converts a subset of moinmoin syntax to github readme markdown.
# Usage: $ python3 ./moin2md.py [input file] > [output file]

import re
import sys

filename = sys.argv[1]

with open(filename, "r") as file_:
    for line in file_:
        # Remove empty lines:
        if re.match(r"^$", line):
            continue
        # Remove comments at the top
        if re.match(r".*format.*|.*language.*|.*pragma.*", line):
            continue
        line = re.sub(r"", "", line)
        # Table of contents
        line = re.sub("<<TableOfContents>>", "", line)
        # Bold
        line = re.sub("'''", "**", line)
        # Italic
        line = re.sub("''", "*", line)
        # Remove numbering enforcers
        line = re.sub(r"\d+\.#\d+", "", line)
        # Heading 1
        line = re.sub(r"^\s*=\s(.*)\s=\s*", r"# \1", line)
        # Heading 2
        line = re.sub(r"^\s*==\s(.*)\s==\s*", r"## \1", line)
        # Heading 3
        line = re.sub(r"^\s*===\s(.*)\s===\s*", r"### \1", line)
        # Code section
        line = re.sub(r"\{\{\{|\}\}\}", "~~~~", line)
        # Line break
        line = re.sub(r"<<BR>>", "<BR>", line)
        # Images and other attachments
        line = re.sub(r"\{\{attachment:(.*)(\.\w+)\|*.*\}\}", r"![\1]("
                                                              r"./res/\1\2)",
                                                              line)
        # Links
        line = re.sub(r"\[\[\s*(.*)\s*\|\s*(.*)\s*\]\]", r"[\2](\1)", line)

        print(line)
