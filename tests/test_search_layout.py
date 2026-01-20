from lxml import html


def test_new_layout_parsing():
    # Sample HTML snippet mimicking the new Anna's Archive layout (Div-based)
    # Based on findings from debugging
    html_content = """
    <html>
    <body>
        <div class="mb-4">
            <div class="flex items-center">
                <!-- Cover -->
                <a href="/md5/12345" class="custom-a">
                    <img src="https://example.com/cover.jpg" />
                </a>

                <!-- Info Div -->
                <div class="flex-col">
                    <!-- Title -->
                    <a href="/md5/12345" class="js-vim-focus font-bold">
                        Test Book Title
                    </a>

                    <!-- Author (First link with /search?q=) -->
                    <a href="/search?q=Jane+Doe" class="italic">Jane Doe</a>

                    <!-- Metadata Div -->
                    <div class="text-gray-500">
                        ✅ English [en] · PDF · 2.5MB · 2023
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    doc = html.fromstring(html_content)

    # 1. Find books using the new strategy
    books = doc.xpath('//a[contains(@class, "js-vim-focus")]')
    assert len(books) == 1, "Should find 1 book entry"

    book = books[0]

    # 2. Extract Title
    title = "".join(book.xpath(".//text()")).strip()
    print(f"Title: {title}")
    assert title == "Test Book Title"

    # 3. Extract MD5
    href = book.get("href")
    md5 = href.split("/")[-1]
    print(f"MD5: {md5}")
    assert md5 == "12345"

    # 4. Extract Author
    info_div = book.getparent()
    authors = info_div.xpath('./a[contains(@href, "/search?q=")]/text()')
    author = authors[0] if authors else "Unknown"
    print(f"Author: {author}")
    assert author == "Jane Doe"

    # 5. Extract Details (Format)
    meta_text = "".join(info_div.xpath('.//div[contains(@class, "text-gray-500")]//text()'))
    print(f"Meta: {meta_text}")
    assert "PDF" in meta_text

    # 6. Extract Cover
    wrapper = info_div.getparent()
    cover_src = wrapper.xpath(".//img/@src")
    cover_url = cover_src[0] if cover_src else ""
    print(f"Cover: {cover_url}")
    assert cover_url == "https://example.com/cover.jpg"

    print("\nSUCCESS: New layout parsing logic verified!")


if __name__ == "__main__":
    test_new_layout_parsing()
