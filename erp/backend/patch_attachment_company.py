"""One-shot patcher: insert the Attachment.company FK (Q-055) into models.py.

Used during a concurrent-edit race where editor buffers kept reverting the
file; kept in the repo for provenance of how the field was introduced.
"""

from __future__ import annotations

import io
import os

TARGET = os.path.join(os.path.dirname(__file__), "apps", "documents", "models.py")

ANCHOR = (
    "    entity_id = models.CharField(max_length=64, db_index=True)\n"
    "    original_filename"
)
BLOCK = "\n".join(
    [
        "    entity_id = models.CharField(max_length=64, db_index=True)",
        "    # Resolved from the referenced entity at upload time (Q-055 company",
        "    # isolation); unresolvable targets are rejected at upload.",
        '    company = models.ForeignKey(',
        '        "organization.Company",',
        "        null=True,",
        "        blank=True,",
        "        on_delete=models.PROTECT,",
        '        related_name="attachments",',
        "    )",
        "    original_filename",
    ]
)

source = io.open(TARGET, encoding="utf-8").read()
if 'related_name="attachments"' in source:
    print("ALREADY-PATCHED")
elif ANCHOR not in source:
    raise SystemExit("ANCHOR-NOT-FOUND")
else:
    io.open(TARGET, "w", encoding="utf-8", newline="").write(source.replace(ANCHOR, BLOCK))
    print("PATCHED")
