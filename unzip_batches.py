from pathlib import Path
import zipfile
import shutil

ROOT = Path(r"ST_ROOT_LOCATION")  # <-- change to your top folder that contains Patient files.
ZIP_PREFIX = "processed_"       # we will match: processed_<number>_images_batch*.zip
OUTER_NAME_MATCH = "processed_"  # kept for readability

for patient_dir in ROOT.iterdir():
    if not patient_dir.is_dir():
        continue

    # ignore Mac artifact at patient level
    if patient_dir.name == ".DS_Store":
        continue

    # Find all matching zip files in this patient directory:
    # (Based on your screenshot, there is a file named like processed_1627_images_batch with Type "Compressed (zip)")
    zip_candidates = []
    for p in patient_dir.iterdir():
        if p.name == ".DS_Store":
            continue

        name = p.name
        # Match things that look like: processed_<digits>_images_batch (zip-compressed file)
        # Your zip may not explicitly end with .zip, so we detect by file header when needed.
        if name.startswith("processed_") and "images_batch" in name:
            zip_candidates.append(p)

    for candidate in zip_candidates:
        # If it is already an extracted folder, leave it alone.
        if candidate.is_dir():
            continue

        # If it's a zip file (even if extension-less), unzip it into a folder next to it.
        # Determine output folder: if you have "processed_1627_images_batch" as zip file,
        # create "processed_1627_images_batch" folder (or overwrite safely if you want).
        out_folder = candidate.with_name(candidate.stem)  # for extension-less, stem == name

        # Detect zip by attempting to open
        is_zip = False
        try:
            with zipfile.ZipFile(candidate, "r") as z:
                is_zip = True
                # If already extracted (folder exists and not empty), skip
                if out_folder.exists() and any(out_folder.iterdir()):
                    continue
                out_folder.mkdir(parents=True, exist_ok=True)
                z.extractall(out_folder)
        except zipfile.BadZipFile:
            # Not a zip, leave it alone
            continue

print("Done.")
