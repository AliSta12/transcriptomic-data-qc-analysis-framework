# Invalid local scan example

This folder is intentionally prepared without valid transcriptomic input files.

It does not contain:
- a valid expression matrix,
- a valid metadata file,
- required metadata columns: sample_id and group.

Expected behavior:
The local folder scanner should report that no suitable files were found for analysis.
