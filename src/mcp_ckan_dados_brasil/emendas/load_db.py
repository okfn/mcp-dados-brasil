"""Load Emendas dataset.

Downloads the dataset from the data portal, unzips it and creates an SQLite dataset.
"""

import sqlite3
import pandas as pd
import re
import unicodedata

from importlib import resources
from pathlib import Path
from zipfile import ZipFile

from platformdirs import user_data_path

APP_DIR = "mcp-ckan-dados-brasil"
ZIP_FILE_URL = (
    "https://portaldatransparencia.gov.br/download-de-dados/emendas-parlamentares/UNICO"
)
EMENDAS_CSV_FILES = {
    "EmendasParlamentares_PorFavorecido.csv": "emendas_por_favorecido",
    "EmendasParlamentares.csv": "emendas",
    "EmendasParlamentares_Convenios.csv": "emendas_convenios",
}


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
    data_path = get_data_dir()

    # Here __package__ references: mcp_ckan_dados_brasil.emendas
    with ZipFile(resources.open_binary(__package__, 'data/EmendasParlamentares.zip')) as zip_file:
        for filename in EMENDAS_CSV_FILES:
            zip_file.extract(filename, data_path)
            print(f"Extracted {filename} in {data_path}...")

    conn = sqlite3.connect(get_db_path())
    for filename, table_name in EMENDAS_CSV_FILES.items():
        df = pd.read_csv(
            data_path / filename,
            sep=";",
            decimal=",",
            low_memory=False,
            encoding="iso-8859-1",
        )
        df.columns = _make_sqlite_safe(df.columns)
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"Table '{table_name}' loaded ({len(df)} rows).")
    conn.close()

    print(f"Database {get_db_path()} created successfully.")


if __name__ == "__main__":
    main()
