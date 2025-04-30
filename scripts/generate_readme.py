# SPDX-License-Identifier: MIT
# Copyright (c) 2025 HEG Geneva / Deep Mining Lab / FairOnChain / EtherFAIR
import os
from datetime import datetime, timezone
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = os.path.dirname(__file__)
TEMPLATE_NAME = "README.tpl.md"
OUTPUT_PATH   = os.path.join(TEMPLATE_DIR, "..", "README.md")

def get_modification_date(path, fmt="%Y-%m-%d %H:%M:%S UTC"):
    ts = os.path.getmtime(path)
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime(fmt)

data_info = {
    "chainlink": {
        "path": "../data/chainlink_eth_usd.csv",
    },
    # Uniswap ici
}

context = {}
for name, info in data_info.items():
    csv_path = os.path.normpath(os.path.join(TEMPLATE_DIR, info["path"]))
    context[name] = { "extraction": get_modification_date(csv_path) }

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), keep_trailing_newline=True)
template = env.get_template(TEMPLATE_NAME)
rendered = template.render(**context)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(rendered)
print(f"✅ README generated at {OUTPUT_PATH}")
