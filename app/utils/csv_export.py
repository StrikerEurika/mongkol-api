import csv
from io import StringIO

def rows_to_csv(rows: list[dict]) -> str:
    if not rows:
        return ""

    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()