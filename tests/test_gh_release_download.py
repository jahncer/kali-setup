from __future__ import annotations

import importlib.util
import io
import stat
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path


HELPER = (
    Path(__file__).parents[1]
    / "roles"
    / "jahncer.kali_ctf"
    / "files"
    / "gh_release_download.py"
)
SPEC = importlib.util.spec_from_file_location("gh_release_download", HELPER)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ArchiveSafetyTests(unittest.TestCase):
    def test_zip_path_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            archive = Path(temp_name) / "bad.zip"
            destination = Path(temp_name) / "output"
            destination.mkdir()
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr("../escape", "bad")
            with zipfile.ZipFile(archive) as handle:
                with self.assertRaises(RuntimeError):
                    MODULE.safe_extract_zip(handle, destination)

    def test_zip_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            archive = Path(temp_name) / "link.zip"
            destination = Path(temp_name) / "output"
            destination.mkdir()
            info = zipfile.ZipInfo("link")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr(info, "/tmp/target")
            with zipfile.ZipFile(archive) as handle:
                with self.assertRaises(RuntimeError):
                    MODULE.safe_extract_zip(handle, destination)

    def test_tar_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            archive = Path(temp_name) / "link.tar.gz"
            destination = Path(temp_name) / "output"
            destination.mkdir()
            with tarfile.open(archive, "w:gz") as handle:
                link = tarfile.TarInfo("link")
                link.type = tarfile.SYMTYPE
                link.linkname = "/tmp/target"
                handle.addfile(link)
            with tarfile.open(archive, "r:gz") as handle:
                with self.assertRaises(RuntimeError):
                    MODULE.safe_extract_tar(handle, destination)

    def test_normal_tar_is_extracted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            archive = Path(temp_name) / "good.tar.gz"
            destination = Path(temp_name) / "output"
            destination.mkdir()
            payload = b"hello"
            with tarfile.open(archive, "w:gz") as handle:
                member = tarfile.TarInfo("tool")
                member.size = len(payload)
                handle.addfile(member, io.BytesIO(payload))
            with tarfile.open(archive, "r:gz") as handle:
                MODULE.safe_extract_tar(handle, destination)
            self.assertEqual((destination / "tool").read_bytes(), payload)


if __name__ == "__main__":
    unittest.main()
