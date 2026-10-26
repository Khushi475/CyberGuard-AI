"""CSV log-file parsing for the Log Analyzer module.

Responsibilities
----------------
1. Decode the uploaded bytes safely (UTF-8 with BOM tolerance, latin-1 fallback).
2. Confirm the header contains the mandatory columns.
3. Normalise each row into the canonical security-event dictionary.
4. Report per-row validation errors instead of aborting the whole upload.
"""
import csv
import io

from .errors import ValidationError
from .validators import validate_event_payload

REQUIRED_COLUMNS = {"source_ip"}

KNOWN_COLUMNS = [
    "timestamp",
    "source_ip",
    "destination_ip",
    "source_port",
    "destination_port",
    "protocol",
    "bytes",
    "bytes_transferred",
    "packets",
    "packet_count",
    "failed_logins",
    "failed_login_attempts",
    "request_count",
    "duration",
    "connection_duration",
    "event_type",
    "user_agent",
]

# Accept both the short CSV column names and the canonical model field names.
COLUMN_ALIASES = {
    "bytes": "bytes_transferred",
    "byte_count": "bytes_transferred",
    "packets": "packet_count",
    "failed_logins": "failed_login_attempts",
    "failed_login": "failed_login_attempts",
    "duration": "connection_duration",
    "src_ip": "source_ip",
    "dst_ip": "destination_ip",
    "src_port": "source_port",
    "dst_port": "destination_port",
    "requests": "request_count",
    "time": "timestamp",
    "date": "timestamp",
}


def decode_file(file_storage) -> str:
    raw = file_storage.read()
    if not raw:
        raise ValidationError("The uploaded file is empty.", details={"field": "file"})
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValidationError(
        "The uploaded file could not be decoded as text. Please upload a UTF-8 CSV file.",
        details={"field": "file"},
    )


def _normalise_header(name: str) -> str:
    key = (name or "").strip().lower().replace(" ", "_").replace("-", "_")
    return COLUMN_ALIASES.get(key, key)


def parse_csv(text: str, max_rows: int = 5000):
    """Parse CSV text into ``(valid_rows, row_errors)``.

    ``valid_rows`` contains normalised event dictionaries; ``row_errors`` contains
    ``{"row": <line number>, "error": <message>}`` entries for rejected rows.
    """
    stream = io.StringIO(text)
    try:
        sample = text[:4096]
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(stream, dialect=dialect)

    if not reader.fieldnames:
        raise ValidationError(
            "The CSV file has no header row. Expected columns such as: "
            + ", ".join(KNOWN_COLUMNS[:8]),
            details={"field": "file"},
        )

    headers = [_normalise_header(name) for name in reader.fieldnames]
    missing = REQUIRED_COLUMNS - set(headers)
    if missing:
        raise ValidationError(
            f"The CSV file is missing required column(s): {', '.join(sorted(missing))}.",
            details={"field": "file", "required": sorted(REQUIRED_COLUMNS),
                     "found": [h for h in headers if h]},
        )

    valid_rows = []
    row_errors = []

    for index, raw_row in enumerate(reader, start=2):  # row 1 is the header
        if len(valid_rows) >= max_rows:
            row_errors.append(
                {"row": index, "error": f"Row skipped: upload limit of {max_rows} rows reached."}
            )
            break
        if raw_row is None:
            continue
        normalised = {}
        for key, value in raw_row.items():
            if key is None:
                continue
            field = _normalise_header(key)
            if isinstance(value, list):
                value = value[0] if value else ""
            normalised[field] = (value or "").strip() if isinstance(value, str) else value
        if not any(normalised.values()):
            continue  # blank line
        try:
            valid_rows.append(validate_event_payload(normalised))
        except ValidationError as exc:
            row_errors.append({"row": index, "error": exc.message})

    if not valid_rows and not row_errors:
        raise ValidationError(
            "The CSV file contains a header but no data rows.", details={"field": "file"}
        )

    return valid_rows, row_errors


def validate_upload(file_storage):
    """Guard-rails applied before a file is read into memory."""
    if file_storage is None or not getattr(file_storage, "filename", ""):
        raise ValidationError(
            "No file was supplied. Attach a CSV file using the 'file' form field.",
            details={"field": "file"},
        )
    filename = file_storage.filename.lower()
    if not filename.endswith((".csv", ".txt", ".log")):
        raise ValidationError(
            "Only .csv, .txt or .log files are accepted by the Log Analyzer.",
            details={"field": "file", "filename": file_storage.filename},
        )
    return file_storage
