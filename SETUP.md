# Setup checklist

This repo is built and script-tested, but three things need to happen on
your machine / your GitHub account (I couldn't reach github.com or push
from the sandbox I built this in):

## 1. Push this repo as your profile repo

```bash
gh repo create Dmg0920 --public --source=. --push
# or, without gh:
git init
git add -A
git commit -m "Initial profile README setup"
git branch -M main
git remote add origin https://github.com/Dmg0920/Dmg0920.git
git push -u origin main
```

## 2. Add your portrait

The README references `avi-ascii.svg`, which isn't in this package yet —
it needs a real photo to convert. Once you have one:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r scripts/requirements.txt
python scripts/prep_photo.py source-photo.jpg
python scripts/make_ascii_svg.py          # writes avi-ascii.svg
git add avi-ascii.svg
git commit -m "Add ASCII portrait"
git push
```

(`rembg` downloads a small background-removal model on first run — that's
normal and only happens once.)

## 3. Generate the first heatmap + trigger the workflow

The heatmap needs to be generated once locally (or just let the workflow
do it):

```bash
pip install requests beautifulsoup4
python scripts/fetch_contributions.py Dmg0920
python scripts/render_heatmap_svg.py
git add data/contributions.json contrib-heatmap.svg
git commit -m "Add initial contribution heatmap"
git push
```

Then go to the **Actions** tab on the repo and manually run
**"Update profile art"** once (`workflow_dispatch`) to confirm it commits
successfully. After that it refreshes daily on its own at ~06:17 UTC.

## Notes / things I adjusted from the original plan

- The workflow calls `fetch_contributions.py ${{ github.repository_owner }}`
  explicitly rather than relying on the script's hardcoded default
  username, so it stays correct if you ever rename or fork the repo.
- `info-card.svg` in this package is real — edit the `CONTENT` list at the
  top of `scripts/make_info_card.py` to change what it says, then rerun
  `python scripts/make_info_card.py`.
- `contrib-heatmap.svg` and `data/contributions.json` are **not** included
  here — I tested the renderer against synthetic sample data (this sandbox
  couldn't reach `github.com` to scrape your real calendar), so shipping
  those would have committed fake numbers under your name. Generate them
  for real with step 3 above.
- Everything else (README layout, ASCII pipeline, info card, workflow
  YAML) is exactly as specified in the blog post, syntax-validated and,
  where testable without live GitHub access, run end-to-end.
