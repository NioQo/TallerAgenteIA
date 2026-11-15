"""Backup de db.sqlite3 (API de backup de SQLite) y media/ a una ubicación externa.

Uso:
    python scripts/backup.py                       # backup con TALLER_BACKUP_DIR
    python scripts/backup.py --generate-key RUTA   # crea una clave nueva (no se imprime)
    python scripts/backup.py --restore ARCHIVO --to CARPETA_NUEVA

Nunca modifica db.sqlite3 ni media/: la base se abre en solo lectura y media/ solo se lee.
El destino siempre usa una subcarpeta propia y la retención solo borra archivos propios.
"""
import argparse
import hashlib
import logging
import os
import sqlite3
import sys
import tempfile
import zipfile
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SUBFOLDER = "TallerAgenteIA-backups"
PREFIX = "taller-"
CLOUD_HINTS = ("onedrive", "google drive", "googledrive", "mi unidad", "my drive", "dropbox", "icloud", "mega", "\\box")
log = logging.getLogger("taller.backup")


class BackupError(Exception):
    pass


def read_env_value(name):
    """Lee solo una variable de entorno o de .env; nunca recorre ni imprime el resto del archivo."""
    if os.environ.get(name):
        return os.environ[name]
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip().strip("\"'")
    return ""


def is_inside(child, parent):
    child, parent = Path(child).resolve(), Path(parent).resolve()
    return child == parent or parent in child.parents


def looks_like_cloud(path):
    lowered = str(path).lower()
    return any(hint in lowered for hint in CLOUD_HINTS)


def setup_logging():
    base = Path(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()) / "TallerAgenteIA"
    base.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(base / "backup.log", maxBytes=1_000_000, backupCount=5, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(handler)
    log.addHandler(logging.StreamHandler(sys.stdout))
    log.setLevel(logging.INFO)


def snapshot_database(db_path, target):
    """Copia consistente con la API de backup de SQLite y la verifica."""
    if not Path(db_path).exists():
        raise BackupError("No existe la base de datos de origen.")
    source = sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True)
    destination = sqlite3.connect(target)
    try:
        source.backup(destination)
        result = destination.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        destination.close()
        source.close()
    if result != "ok":
        raise BackupError(f"La copia de la base no pasó integrity_check: {result}")


def build_archive(db_path, media_path, archive_path):
    with tempfile.TemporaryDirectory(prefix="taller-snap-") as tmp:
        snap = Path(tmp) / "db.sqlite3"
        snapshot_database(db_path, snap)
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.write(snap, "db.sqlite3")
            media = Path(media_path)
            if media.is_dir():
                for file in sorted(media.rglob("*")):
                    if file.is_file():
                        archive.write(file, Path("media") / file.relative_to(media))
    with zipfile.ZipFile(archive_path) as archive:
        if archive.testzip() is not None:
            raise BackupError("El archivo comprimido está dañado.")


def load_key(key_file):
    from cryptography.fernet import Fernet

    try:
        return Fernet(Path(key_file).read_bytes().strip())
    except (OSError, ValueError) as exc:
        raise BackupError("No se pudo leer una clave válida en el archivo de clave.") from exc


def generate_key(path):
    from cryptography.fernet import Fernet

    path = Path(path)
    if path.exists():
        raise BackupError("El archivo de clave ya existe; no se sobrescribe.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(Fernet.generate_key())
    log.info("Clave creada en %s (no se imprime). Guárdala fuera del destino de backups.", path)


def prune(folder, keep):
    files = sorted(
        (f for f in Path(folder).iterdir() if f.is_file() and f.name.startswith(PREFIX) and f.name.endswith((".zip", ".zip.enc"))),
        key=lambda f: f.name,
        reverse=True,
    )
    for old in files[keep:]:
        old.unlink()
        log.info("Eliminado backup antiguo %s", old.name)


def run_backup(db_path, media_path, dest, keep=14, key_file=None, encrypt=True, now=None):
    if not dest:
        raise BackupError("Define TALLER_BACKUP_DIR (o --dest) con el destino de los backups.")
    dest = Path(dest)
    if is_inside(dest, BASE_DIR) and not os.environ.get("TALLER_BACKUP_ALLOW_REPO"):
        raise BackupError("El destino no puede estar dentro del repositorio.")
    if encrypt:
        if not key_file:
            raise BackupError("Falta TALLER_BACKUP_KEY_FILE: los backups se cifran por defecto.")
        if is_inside(key_file, dest):
            raise BackupError("El archivo de clave no puede estar en el mismo destino que los backups.")
        fernet = load_key(key_file)
    elif looks_like_cloud(dest):
        raise BackupError("El destino parece una nube; el backup sin cifrar no está permitido.")
    folder = dest / SUBFOLDER
    folder.mkdir(parents=True, exist_ok=True)
    stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    final = folder / (f"{PREFIX}{stamp}.zip" + (".enc" if encrypt else ""))
    partial = folder / (final.name + ".partial")
    with tempfile.TemporaryDirectory(prefix="taller-zip-") as tmp:
        archive = Path(tmp) / "backup.zip"
        build_archive(db_path, media_path, archive)
        data = archive.read_bytes()
    partial.write_bytes(fernet.encrypt(data) if encrypt else data)
    os.replace(partial, final)
    digest = hashlib.sha256(final.read_bytes()).hexdigest()[:12]
    log.info("Backup creado: %s (sha256 %s…, %d bytes)", final.name, digest, final.stat().st_size)
    prune(folder, keep)
    return final


def restore(archive_path, target_dir, key_file=None):
    archive_path, target = Path(archive_path), Path(target_dir)
    if target.exists() and any(target.iterdir()):
        raise BackupError("La carpeta de restauración debe estar vacía o no existir.")
    if is_inside(target, BASE_DIR / "media") or target.resolve() == BASE_DIR.resolve():
        raise BackupError("No se restaura sobre el repositorio ni sobre media/.")
    data = archive_path.read_bytes()
    if archive_path.name.endswith(".enc"):
        if not key_file:
            raise BackupError("Indica --key-file para descifrar.")
        from cryptography.fernet import InvalidToken

        try:
            data = load_key(key_file).decrypt(data)
        except InvalidToken as exc:
            raise BackupError("La clave no corresponde a este backup.") from exc
    target.mkdir(parents=True, exist_ok=True)
    zip_path = target / "_backup.zip"
    zip_path.write_bytes(data)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(target)
    zip_path.unlink()
    check = sqlite3.connect(target / "db.sqlite3")
    try:
        result = check.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        check.close()
    if result != "ok":
        raise BackupError(f"La base restaurada no pasó integrity_check: {result}")
    log.info("Restauración de prueba correcta en %s", target)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dest", default=None)
    parser.add_argument("--keep", type=int, default=14)
    parser.add_argument("--key-file", default=None)
    parser.add_argument("--no-encrypt", action="store_true", help="Solo para discos locales; se rechaza en nubes.")
    parser.add_argument("--generate-key", metavar="RUTA")
    parser.add_argument("--restore", metavar="ARCHIVO")
    parser.add_argument("--to", metavar="CARPETA")
    args = parser.parse_args(argv)
    setup_logging()
    try:
        key_file = args.key_file or read_env_value("TALLER_BACKUP_KEY_FILE")
        if args.generate_key:
            generate_key(args.generate_key)
        elif args.restore:
            if not args.to:
                raise BackupError("--restore requiere --to.")
            restore(args.restore, args.to, key_file)
        else:
            run_backup(
                BASE_DIR / "db.sqlite3",
                BASE_DIR / "media",
                args.dest or read_env_value("TALLER_BACKUP_DIR"),
                keep=args.keep,
                key_file=key_file,
                encrypt=not args.no_encrypt,
            )
    except BackupError as exc:
        log.error("%s", exc)
        return 1
    except Exception:
        log.exception("Error inesperado en el backup")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
