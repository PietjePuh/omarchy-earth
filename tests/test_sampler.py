import json
import glob
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

class TestEarthMonitorKeyless(unittest.TestCase):

    def test_json_files_valid(self):
        """Verify manifest.json and all data/*.json files are valid JSON."""
        manifest_path = REPO_ROOT / "manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        self.assertIn("id", manifest)
        self.assertEqual(manifest["id"], "io.github.pietjepuh.earth")

        data_json_files = glob.glob(str(REPO_ROOT / "data" / "*.json"))
        self.assertGreater(len(data_json_files), 10, "Should find data JSON files")
        for filepath in data_json_files:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.assertIsNotNone(data)

    def test_earth_sampler_once(self):
        """Run earth-sampler.py --once and verify output structure without error."""
        cmd = [
            "python3",
            str(REPO_ROOT / "bin" / "earth-sampler.py"),
            "--lat", "52.37",
            "--lon", "4.90",
            "--span", "4",
            "--radius", "50",
            "--once"
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Sampler failed: {proc.stderr}")

        data = json.loads(proc.stdout)
        self.assertIn("summary", data)
        self.assertIn("weather", data)
        self.assertIn("aircraft", data)
        self.assertIn("vessels", data)

    def test_build_map(self):
        """Run build-map.py and verify generated HTML map contains embedded payload."""
        out_path = REPO_ROOT / "test_output_map.html"
        cmd = [
            "python3",
            str(REPO_ROOT / "bin" / "build-map.py"),
            "--lat", "52.37",
            "--lon", "4.90",
            "--span", "4",
            "--out", str(out_path)
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"build-map failed: {proc.stderr}")
        self.assertTrue(out_path.exists())

        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("<script>", content)
        self.assertIn("L.map", content)

        if out_path.exists():
            out_path.unlink()

if __name__ == "__main__":
    unittest.main()
