# SPDX-License-Identifier: CC-BY-4.0
# © 2025 HES-SO / HEG Geneva / Deep Mining Lab / FairOnChain / Open Price ETH

import csv
import logging
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateError

# Fonction pour extraire le dernier timestamp du CSV
def get_last_csv_timestamp(
    path: Path,
    col_name: str,
    datetime_format: str | None = None,
    tz_aware: bool = False
) -> datetime | str | None:
    """
    Extrait la valeur de la colonne `col_name` à la dernière ligne du CSV.
    - Si `datetime_format` fourni, retourne un datetime (aware ou naive).
    - Sinon, retourne la chaîne brute.
    """
    try:
        with path.open(newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            try:
                last_row = deque(reader, maxlen=1)[0]
            except IndexError:
                logging.warning("CSV vide ou sans en-têtes : %s", path)
                return None
            last_value = last_row.get(col_name)
            if last_value is None:
                logging.warning("Colonne '%s' introuvable dans %s", col_name, path)
                return None
    except FileNotFoundError:
        logging.error("Fichier non trouvé : %s", path)
        return None
    except csv.Error as e:
        logging.error("Erreur CSV pour %s : %s", path, e)
        return None

    if datetime_format:
        try:
            dt = datetime.strptime(last_value, datetime_format)
        except ValueError as e:
            logging.error(
                "Impossible de parser '%s' avec le format '%s' : %s",
                last_value, datetime_format, e
            )
            return None
        return dt if tz_aware else dt.replace(tzinfo=None)

    return last_value

# Configuration Jinja2
TEMPLATE_DIR = Path(__file__).parent
TEMPLATE_NAME = "README.tpl.md"
OUTPUT_PATH = TEMPLATE_DIR.parent / "README.md"

# Informations sur les datasets
data_info = {
    "chainlink": {
        "path": TEMPLATE_DIR.parent / "data" / "chainlink_eth_usd.csv",
        "col_name": "datetime_utc",
        "fmt": "%Y-%m-%d %H:%M:%S",
        "tz_aware": False,  # on récupère un datetime UTC naïf
    },
    "uniswap": {
        "path": TEMPLATE_DIR.parent / "data" / "uniswap_eth_usd.csv",
        "col_name": "timestamp",
        "fmt": "%Y-%m-%d %H:%M:%S%z",
        "tz_aware": True,
    },
}

# Construction du contexte pour le template
context: dict[str, dict[str, str]] = {}
for name, info in data_info.items():
    last_ts = get_last_csv_timestamp(
        info["path"],
        col_name=info["col_name"],
        datetime_format=info.get("fmt"),
        tz_aware=info.get("tz_aware", False)
    )

    if isinstance(last_ts, datetime):
        if name == "chainlink":
            # Affichage en UTC fixe
            display_ts = last_ts.strftime("%Y-%m-%d %H:%M:%S") + " UTC"
        else:
            # Pour uniswap déjà aware, on convertit en UTC et on affiche l'abréviation
            display_ts = last_ts.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    else:
        display_ts = last_ts or "N/A"

    context[name] = {"extraction": display_ts}

# Génération du README via Jinja2
try:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        keep_trailing_newline=True
    )
    template = env.get_template(TEMPLATE_NAME)
    rendered = template.render(**context)
    OUTPUT_PATH.write_text(rendered, encoding='utf-8')
    logging.info("✅ README généré à %s", OUTPUT_PATH)
except (TemplateError, OSError) as e:
    logging.exception("Échec de génération du README : %s", e)