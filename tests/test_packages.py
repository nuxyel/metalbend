"""scripts/packages.py on a fake BendHub store: the packages the corpus imports and the ones they import, each with its
store id and a hash of its files, which moves when a file of the package changes under the same version."""
import tempfile
import unittest
from pathlib import Path

import packages


class Packages(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.root, self.lib = d / "mb", d / "lib"
        (self.root / "workloads" / "w").mkdir(parents=True)
        (self.root / "lib").mkdir()
        (self.root / "workloads" / "w" / "main.bend").write_text("import Base\nimport top@1.0.0.0/main.bend as T\n")
        (self.root / "lib" / "x.bend").write_text("import gone@0.1.0.0/main.bend as G\n")
        (self.lib / "names").mkdir(parents=True)
        for name, sid, src in (("top@1.0.0.0", "0xaa", "import dep@0.2.0.0/main.bend as D\n"), ("dep@0.2.0.0", "0xbb", "")):
            (self.lib / "names" / name).write_text(sid + "\n")
            (self.lib / sid).mkdir()
            (self.lib / sid / "main.bend").write_text(src)

    def tearDown(self):
        self.tmp.cleanup()

    def test_imports_are_followed_into_the_packages(self):
        got = packages.packages(self.root, self.lib)
        self.assertEqual(list(got), ["dep@0.2.0.0", "gone@0.1.0.0", "top@1.0.0.0"])
        self.assertEqual(got["gone@0.1.0.0"], "missing")
        self.assertRegex(got["top@1.0.0.0"], r"^0xaa [0-9a-f]{16}$")

    def test_a_changed_file_moves_the_hash(self):
        before = packages.packages(self.root, self.lib)["dep@0.2.0.0"]
        (self.lib / "0xbb" / "LICENSE").write_text("x")
        self.assertNotEqual(packages.packages(self.root, self.lib)["dep@0.2.0.0"], before)


if __name__ == "__main__":
    unittest.main()
