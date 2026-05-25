import json
from pathlib import Path


def find_latest_batch(batch_root: Path) -> Path:
    batches = [d for d in batch_root.iterdir() if d.is_dir()]
    if not batches:
        raise RuntimeError("Brak batchy w katalogu.")

    return sorted(batches)[-1]


def load_batch_manifest(batch_dir: Path) -> dict:
    manifest_path = batch_dir / "manifest.json"

    if not manifest_path.exists():
        raise RuntimeError(f"Brak manifest.json w {batch_dir}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_invoices_dir(batch_root: Path) -> Path:
    batch_dir = find_latest_batch(batch_root)
    manifest = load_batch_manifest(batch_dir)

    invoices_rel = manifest["storage"]["invoices_dir"]
    return batch_dir / invoices_rel
