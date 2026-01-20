from __future__ import annotations

# Add the current directory to sys.path so we can import the plugin modules
# This assumes you run calibre-debug from the root of the plugin source
import os
import sys
from typing import Any

from calibre.gui2.store import StorePlugin
from calibre.gui2.store.search_result import SearchResult

# Add parent directory to path so we can import the plugin modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from annas_archive import AnnasArchiveStore
from constants import DEFAULT_MIRRORS


def main():
    # Mock GUI object (can be None for basic testing)
    gui = None

    # Initialize the plugin
    store = AnnasArchiveStore(gui, "Anna's Archive")

    # Configure the plugin (optional, set mirrors if needed)
    current_mirrors = store.config.get("mirrors", DEFAULT_MIRRORS)
    if current_mirrors == ["https://this.mirror.does.not.exist.at.all"]:
        print("WARNING: Corrupted mirror config detected. Resetting to defaults.")
        store.config["mirrors"] = DEFAULT_MIRRORS

    print(f"Current Mirrors: {store.config.get('mirrors', DEFAULT_MIRRORS)}")

    # Ensure circuit breaker is disabled for debugging
    store.config["circuit_breaker"] = False

    print("Searching for 'Python'...")
    try:
        # Run a search
        # Note: _search yield results, so we iterate over it
        # We use a simple query like "Python" or "test"
        query = "Python"
        max_results = 5
        timeout = 60

        results = store.search(query, max_results, timeout)

        count = 0
        for result in results:
            count += 1
            print(f"[{count}] {result.title} by {result.author}")
            print(f"    Format: {result.formats}")
            print(f"    Mirror Link: {result.detail_item}")
            # print(f"    Cover: {result.cover_url}")

            # Test get_details on the first result to verify download link parsing
            if count == 1:
                print("    Testing get_details() on this result...")
                try:
                    store.get_details(result, timeout)
                    print("    get_details() success!")
                    print(f"    Downloads found: {result.downloads}")
                except Exception as e:
                    print(f"    get_details() FAILED: {e}")

            print("-" * 40)

        if count == 0:
            print("No results found.")
        else:
            print(f"Found {count} results.")

    except Exception as e:
        print(f"Error during search: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
