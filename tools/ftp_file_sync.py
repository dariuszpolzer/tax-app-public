import argparse
import ftplib  # nosec B402
import json
import os
from pathlib import Path, PurePosixPath


def load_config(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Brak pliku konfiguracji FTP: {path}")
    with path.open(encoding="utf-8") as f:
        config = json.load(f)

    config["host"] = os.getenv("TAX_APP_FTP_HOST", config.get("host", ""))
    config["username"] = os.getenv("TAX_APP_FTP_USER", config.get("username", ""))
    config["password"] = os.getenv("TAX_APP_FTP_PASSWORD", config.get("password", ""))

    missing = [key for key in ("host", "username", "password") if not config.get(key)]
    if missing:
        raise ValueError("Brak danych FTP: " + ", ".join(missing))

    return config


def connect(config: dict):
    ftp_cls = ftplib.FTP_TLS if config.get("tls") else ftplib.FTP
    ftp = ftp_cls(config["host"], timeout=30)
    try:
        ftp.login(config["username"], config["password"])
    except ftplib.error_perm as ex:
        raise RuntimeError(
            "FTP odrzucil logowanie. Sprawdz username/password w ftp-sync.json "
            "albo zmienne TAX_APP_FTP_USER i TAX_APP_FTP_PASSWORD."
        ) from ex
    if isinstance(ftp, ftplib.FTP_TLS):
        ftp.prot_p()
    ftp.set_pasv(bool(config.get("passive", True)))
    return ftp


def find_file_config(config: dict, name: str) -> dict:
    for item in config.get("files", []):
        if item.get("name") == name:
            return item
    raise KeyError(f"Brak pliku '{name}' w sekcji files")


def ensure_remote_dirs(ftp, remote_path: str) -> None:
    parent = PurePosixPath(remote_path).parent
    if str(parent) in ("", "."):
        return

    current = ""
    for part in parent.parts:
        if part == "/":
            ftp.cwd("/")
            current = "/"
            continue
        current = str(PurePosixPath(current) / part)
        try:
            ftp.mkd(current)
        except ftplib.error_perm as ex:
            if not str(ex).startswith("550"):
                raise


def upload(ftp, local_path: Path, remote_path: str) -> None:
    if not local_path.exists():
        raise FileNotFoundError(f"Brak pliku lokalnego: {local_path}")
    ensure_remote_dirs(ftp, remote_path)
    with local_path.open("rb") as f:
        ftp.storbinary(f"STOR {remote_path}", f)


def download(ftp, remote_path: str, local_path: Path) -> None:
    local_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = local_path.with_suffix(local_path.suffix + ".tmp")
    with temp_path.open("wb") as f:
        ftp.retrbinary(f"RETR {remote_path}", f.write)
    temp_path.replace(local_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronizuje pojedyncze pliki przez FTP.")
    parser.add_argument("direction", choices=["upload", "download"])
    parser.add_argument("--config", default="ftp-sync.json")
    parser.add_argument("--file", default="delegations_xml")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    file_config = find_file_config(config, args.file)
    local_path = Path(file_config["local_path"])
    remote_path = file_config["remote_path"]

    with connect(config) as ftp:
        if args.direction == "upload":
            upload(ftp, local_path, remote_path)
            print(f"Wyslano: {local_path} -> {remote_path}")
        else:
            download(ftp, remote_path, local_path)
            print(f"Pobrano: {remote_path} -> {local_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
