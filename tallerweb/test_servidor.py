"""Pruebas de configuración de servidor y backup (no usan db.sqlite3 ni media/ reales)."""
import importlib.util
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase

REPO = Path(__file__).resolve().parent.parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SettingsEnvironmentTests(SimpleTestCase):
    """Carga una copia de settings.py en una carpeta sin .env para aislar los valores por defecto."""

    def load_settings(self, **env):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "taller").mkdir()
        shutil.copy(REPO / "taller" / "settings.py", tmp / "taller" / "settings.py")
        base = {"DJANGO_SECRET_KEY": "clave-de-prueba"}
        base.update(env)
        with mock.patch.dict(os.environ, base, clear=True):
            return load_module("settings_copy", tmp / "taller" / "settings.py")

    def test_defaults_keep_local_only_behaviour(self):
        s = self.load_settings()
        self.assertEqual(s.ALLOWED_HOSTS, ["127.0.0.1", "localhost"])
        self.assertEqual(s.CSRF_TRUSTED_ORIGINS, [])
        self.assertFalse(s.DEBUG)
        self.assertFalse(getattr(s, "SESSION_COOKIE_SECURE", False))
        self.assertFalse(getattr(s, "CSRF_COOKIE_SECURE", False))
        self.assertFalse(s.OPENAI_ENABLED)

    def test_hosts_and_origins_come_from_environment(self):
        s = self.load_settings(
            DJANGO_ALLOWED_HOSTS="127.0.0.1, equipo.tailnet.ts.net ,",
            DJANGO_CSRF_TRUSTED_ORIGINS="https://equipo.tailnet.ts.net",
        )
        self.assertEqual(s.ALLOWED_HOSTS, ["127.0.0.1", "equipo.tailnet.ts.net"])
        self.assertEqual(s.CSRF_TRUSTED_ORIGINS, ["https://equipo.tailnet.ts.net"])

    def test_https_flag_enables_secure_cookies(self):
        s = self.load_settings(DJANGO_HTTPS="true")
        self.assertTrue(s.SESSION_COOKIE_SECURE)
        self.assertTrue(s.CSRF_COOKIE_SECURE)
        self.assertEqual(s.SECURE_PROXY_SSL_HEADER, ("HTTP_X_FORWARDED_PROTO", "https"))
        self.assertEqual(s.SECURE_HSTS_SECONDS, 0)

    def test_whitenoise_follows_security_middleware(self):
        s = self.load_settings()
        index = s.MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
        self.assertEqual(s.MIDDLEWARE[index + 1], "whitenoise.middleware.WhiteNoiseMiddleware")


class BackupTests(SimpleTestCase):
    def setUp(self):
        self.backup = load_module("backup_script", REPO / "scripts" / "backup.py")
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.db = self.tmp / "src" / "db.sqlite3"
        self.db.parent.mkdir()
        conn = sqlite3.connect(self.db)
        conn.execute("CREATE TABLE t (v TEXT)")
        conn.execute("INSERT INTO t VALUES ('dato')")
        conn.commit()
        conn.close()
        self.media = self.tmp / "src" / "media"
        (self.media / "presupuestos").mkdir(parents=True)
        (self.media / "presupuestos" / "P-1.pdf").write_bytes(b"%PDF-demo")
        self.dest = self.tmp / "dest"
        self.key = self.tmp / "keys" / "clave.key"
        self.backup.generate_key(self.key)

    def test_encrypted_backup_restores_with_data_and_media(self):
        before = self.db.read_bytes()
        archive = self.backup.run_backup(self.db, self.media, self.dest, key_file=self.key)
        self.assertTrue(archive.name.endswith(".zip.enc"))
        self.assertEqual(archive.parent.name, self.backup.SUBFOLDER)
        self.assertNotIn(b"PK", archive.read_bytes()[:2])  # cifrado, no es un zip legible
        target = self.tmp / "restore"
        self.backup.restore(archive, target, self.key)
        row = sqlite3.connect(target / "db.sqlite3").execute("SELECT v FROM t").fetchone()
        self.assertEqual(row, ("dato",))
        self.assertEqual((target / "media" / "presupuestos" / "P-1.pdf").read_bytes(), b"%PDF-demo")
        self.assertEqual(self.db.read_bytes(), before)  # el origen no se modifica

    def test_key_inside_destination_is_refused(self):
        key_in_dest = self.dest / "clave.key"
        self.backup.generate_key(key_in_dest)
        with self.assertRaises(self.backup.BackupError):
            self.backup.run_backup(self.db, self.media, self.dest, key_file=key_in_dest)

    def test_unencrypted_backup_is_refused_for_cloud_paths(self):
        with self.assertRaises(self.backup.BackupError):
            self.backup.run_backup(self.db, self.media, self.tmp / "OneDrive" / "b", encrypt=False)

    def test_retention_keeps_only_requested_copies(self):
        from datetime import datetime

        for day in range(1, 6):
            self.backup.run_backup(self.db, self.media, self.dest, keep=3, key_file=self.key, now=datetime(2026, 1, day, 3, 30))
        names = sorted(p.name for p in (self.dest / self.backup.SUBFOLDER).iterdir())
        self.assertEqual(len(names), 3)
        self.assertTrue(names[0].startswith("taller-20260103"))

    def test_wrong_key_cannot_restore(self):
        archive = self.backup.run_backup(self.db, self.media, self.dest, key_file=self.key)
        other = self.tmp / "keys" / "otra.key"
        self.backup.generate_key(other)
        with self.assertRaises(self.backup.BackupError):
            self.backup.restore(archive, self.tmp / "restore2", other)

    def test_missing_destination_is_an_error(self):
        with self.assertRaises(self.backup.BackupError):
            self.backup.run_backup(self.db, self.media, "", key_file=self.key)
