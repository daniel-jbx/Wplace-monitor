import os, sys, requests
from PIL import Image, ImageChops
from io import BytesIO

TILE_SIZE = 1000

X = int(os.environ['PIXEL_X'])
Y = int(os.environ['PIXEL_Y'])
W = int(os.environ['WIDTH'])
H = int(os.environ['HEIGHT'])
BASE_URL = os.environ['TILE_BASE_URL']
SNAPSHOT_FILE = os.environ.get('SNAPSHOT_FILE', 'snapshot.png')

start_tx = X // TILE_SIZE
start_ty = Y // TILE_SIZE
end_tx   = (X + W - 1) // TILE_SIZE
end_ty   = (Y + H - 1) // TILE_SIZE

region = Image.new('RGB', (W, H))

for ty in range(start_ty, end_ty + 1):
    for tx in range(start_tx, end_tx + 1):
        url = BASE_URL.format(x=tx, y=ty)
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            tile = Image.open(BytesIO(resp.content)).convert('RGB')
        except Exception as e:
            print(f"ERROR downloading tile ({tx},{ty}): {e}", file=sys.stderr)
            sys.exit(1)

        tile_global_x = tx * TILE_SIZE
        tile_global_y = ty * TILE_SIZE

        left   = max(0, X - tile_global_x)
        top    = max(0, Y - tile_global_y)
        right  = min(TILE_SIZE, X + W - tile_global_x)
        bottom = min(TILE_SIZE, Y + H - tile_global_y)

        cropped = tile.crop((left, top, right, bottom))
        paste_x = (tile_global_x + left) - X
        paste_y = (tile_global_y + top)  - Y
        region.paste(cropped, (paste_x, paste_y))

changed = False
commit_needed = False

if os.path.exists(SNAPSHOT_FILE):
    previous = Image.open(SNAPSHOT_FILE).convert('RGB')
    diff = ImageChops.difference(region, previous)
    if diff.getbbox() is not None:
        changed = True
        region.save(SNAPSHOT_FILE)
        commit_needed = True
        print("Change detected – snapshot updated.")
    else:
        print("No pixel changes.")
else:
    region.save(SNAPSHOT_FILE)
    commit_needed = True
    print("No previous snapshot – created baseline.")

with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
    f.write(f"changed={'true' if changed else 'false'}\n")
    f.write(f"commit_needed={'true' if commit_needed else 'false'}\n")
