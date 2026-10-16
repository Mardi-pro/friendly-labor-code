"""Refresh the local cache from the PGDLisboa consolidated labor-code page."""

from labor_code import DATA_PATH, fetch_labor_code, save_labor_code


if __name__ == "__main__":
    snapshot = fetch_labor_code()
    save_labor_code(snapshot)
    print(
        f"Saved {len(snapshot['articles'])} articles from "
        f"{snapshot['source_title']} to {DATA_PATH}"
    )
