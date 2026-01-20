from __future__ import annotations

import os
import sys
import time

# Add parent directory to path so we can import the plugin modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from annas_archive import AnnasArchiveStore

# Mock GUI (not needed for this test)
gui = None


def main():
    print("Initializing plugin...")
    store = AnnasArchiveStore(gui, "Anna's Archive")

    # Backup original config
    original_mirrors = store.config.get("mirrors")
    original_cb = store.config.get("circuit_breaker")

    try:
        # Configure to fail
        store.config["mirrors"] = ["https://this.mirror.does.not.exist.at.all"]
        # Enable circuit breaker
        store.config["circuit_breaker"] = True

        print("\n[1] First search (expecting 'All mirrors unreachable')...")
        try:
            # Must consume the generator to trigger the code!
            list(store.search("test", 1, 5))
        except Exception as e:
            print(f"Caught expected exception: {e}")

        print("\n[2] Second search immediately (expecting 'Circuit breaker active')...")
        start_time = time.time()
        try:
            list(store.search("test", 1, 5))
        except Exception as e:
            print(f"Caught expected exception: {e}")
            if "Circuit breaker active" in str(e):
                print("SUCCESS: Circuit breaker triggered correctly.")
            else:
                print("FAILURE: Did not get circuit breaker message.")

        print("\n[3] Disabling circuit breaker and searching (expecting 'All mirrors unreachable')...")
        store.config["circuit_breaker"] = False
        try:
            list(store.search("test", 1, 5))
        except Exception as e:
            print(f"Caught expected exception: {e}")
            if "Circuit breaker active" not in str(e):
                print("SUCCESS: Circuit breaker bypassed when disabled.")

    finally:
        print("\n[4] Restoring original configuration...")
        if original_mirrors is not None:
            store.config["mirrors"] = original_mirrors
        if original_cb is not None:
            store.config["circuit_breaker"] = original_cb
        print("Configuration restored.")


if __name__ == "__main__":
    main()
