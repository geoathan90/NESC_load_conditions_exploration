from pathlib import Path
import gdown

# Small public test file: 2013 mean-rate ERA5 NetCDF (~245 kB)
FILE_ID = "1XOMae1hBNMS65SkD_7aum7RF4A5haKQT"
URL = f"https://drive.google.com/uc?id={FILE_ID}"

out_dir = Path("data/_gdown_test")
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / "2013_stepType_avg.nc"

print(f"Downloading test file to {out_file} ...")
result = gdown.download(URL, str(out_file), quiet=False)

if result is None or not out_file.exists() or out_file.stat().st_size == 0:
    raise SystemExit("Google Drive access test FAILED")

print(f"Google Drive access test PASSED ({out_file.stat().st_size:,} bytes)")

# Keep the repository/workspace clean after the connectivity test.
out_file.unlink()
try:
    out_dir.rmdir()
    out_dir.parent.rmdir()
except OSError:
    pass
