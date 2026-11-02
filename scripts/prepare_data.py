"""Rebuild supplied tables and publish an auditable validation report."""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.data import dataset

if __name__ == '__main__':
    subprocess.run([sys.executable, str(ROOT / 'tools/prepare_mc3.py'),
                    str(ROOT / 'data/raw/MC3_release.zip'), str(ROOT / 'data/processed')], check=True,
                   capture_output=True, text=True)
    path = ROOT / 'data/processed/data_validation_report.json'
    path.write_text(json.dumps(dataset.quality, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Validated {len(dataset.nodes)} nodes, {len(dataset.edges)} edges, {len(dataset.messages)} messages.')
    print(path)
