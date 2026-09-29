import os
import requests
import zipfile
from pathlib import Path
from tqdm import tqdm

DATA_DIR = Path(__file__).parent.parent / 'data'
DATA_DIR.mkdir(exist_ok=True)

MONTHS = [
    'JC-202301-citibike-tripdata.csv.zip',
    'JC-202302-citibike-tripdata.csv.zip',
    'JC-202303-citibike-tripdata.csv.zip',
    'JC-202304-citibike-tripdata.csv.zip',
    'JC-202305-citibike-tripdata.csv.zip',
    'JC-202306-citibike-tripdata.csv.zip',
]

BASE_URL = 'https://s3.amazonaws.com/tripdata/'

def download_file(filename):
    url      = BASE_URL + filename
    out_path = DATA_DIR / filename

    if out_path.exists():
        print(f"Already downloaded: {filename}")
        return

    print(f"Downloading {filename}...")
    r = requests.get(url, stream=True, timeout=60)
    
    if r.status_code == 404:
        print(f"Not found at {url} — skipping")
        return
    
    r.raise_for_status()

    total = int(r.headers.get('content-length', 0))
    with open(out_path, 'wb') as f, tqdm(total=total, unit='B',
                                          unit_scale=True) as bar:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
            bar.update(len(chunk))

    print(f"Extracting {filename}...")
    with zipfile.ZipFile(out_path, 'r') as z:
        z.extractall(DATA_DIR)

    out_path.unlink()
    print(f"Done: {filename}")

if __name__ == '__main__':
    for month in MONTHS:
        download_file(month)

    csvs = list(DATA_DIR.glob('*.csv'))
    print(f"\nDownloaded {len(csvs)} CSV files")
    if csvs:
        total_size = sum(f.stat().st_size for f in csvs) / (1024**2)
        print(f"Total size: {total_size:.1f} MB")