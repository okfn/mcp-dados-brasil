"""Load Emendas dataset.

Downloads the dataset from the data portal, unzips it and creates an SQLite dataset.
"""

import sqlite3
import requests
import pandas as pd
import re
import unicodedata

from pathlib import Path
from zipfile import ZipFile
from io import BytesIO

from platformdirs import user_data_path

APP_DIR = "mcp-ckan-dados-brasil"
ZIP_FILE_URL = (
    "https://portaldatransparencia.gov.br/download-de-dados/emendas-parlamentares/UNICO"
)
EMENDAS_FILENAME = "EmendasParlamentares_PorFavorecido.csv"


def get_data_dir() -> Path:
    """Return a writable data directory for the SQLite and CSV files."""
    data_path = user_data_path(APP_DIR)
    data_path.mkdir(parents=True, exist_ok=True)
    return data_path


def get_db_path() -> Path:
    """Return the full path to the SQLite database file."""
    return get_data_dir() / "db.sqlite3"


def _slugify_column(name: str) -> str:
    """Convert a string to SQLite-safe column name: lowercase, underscores, no special chars."""
    # Normalize unicode (e.g., ç -> c, é -> e)
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    # Replace spaces and slashes with underscores
    name = re.sub(r"[ /]+", "_", name)
    # Remove any remaining non-alphanumeric characters except underscore
    name = re.sub(r"[^a-z0-9_]", "", name.lower())
    # Ensure it doesn't start with a digit (SQLite allows but not recommended)
    if name and name[0].isdigit():
        name = "col_" + name
    return name


def _make_sqlite_safe(columns: pd.Index) -> pd.Index:
    """Rename pandas column index to SQLite-safe names, handling duplicates."""
    safe = [_slugify_column(col) for col in columns]
    # Deal with duplicates: add _1, _2 etc.
    seen = {}
    for i, name in enumerate(safe):
        if name in seen:
            seen[name] += 1
            safe[i] = f"{name}_{seen[name]}"
        else:
            seen[name] = 0
    return pd.Index(safe)


def main():
    response = requests.get(ZIP_FILE_URL)
    response.raise_for_status()

    data_path = get_data_dir()

    with ZipFile(BytesIO(response.content)) as zip_file:
        zip_file.extract(EMENDAS_FILENAME, data_path)

    print(f"Extracted {EMENDAS_FILENAME} in {data_path}...")

    df = pd.read_csv(data_path / EMENDAS_FILENAME, sep=";", encoding="iso-8859-1")
    df.columns = _make_sqlite_safe(df.columns)

    conn = sqlite3.connect(get_db_path())
    df.to_sql("emendas_por_favorecido", conn, if_exists="replace", index=False)
    conn.close()

    print(f"Database {get_db_path()} created successfully.")


if __name__ == "__main__":
    main()
