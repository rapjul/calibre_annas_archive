import urllib.request

from lxml import html

# Test URL provided by user
url = "https://annas-archive.li/md5/d64efd386ed7227592499460aca2044b"


def test_fast_filter_logic():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    print(f"Fetching {url}...")

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            content = resp.read()

        doc = html.fromstring(content)

        # XPath from the plugin
        links = doc.xpath(
            '//div[@id="md5-panel-downloads"]/ul[contains(@class, "list-inside")]/li/a[contains(@class, "js-download-link")]'
        )

        print(f"Found {len(links)} download links.")

        found_fast_partner = False

        for link in links:
            link_text = "".join(link.itertext()).strip()

            # Simulate Filtering Logic
            if "Fast Partner Server" in link_text:
                found_fast_partner = True
                print(f"MATCH: '{link_text}' (Target for filtering)")

        if found_fast_partner:
            print("\nSUCCESS: Found 'Fast Partner Server' links to test filtering against.")
        else:
            print("\nWARNING: No 'Fast Partner Server' links found on this page. Test might be invalid/outdated.")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_fast_filter_logic()
