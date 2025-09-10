import requests
import parsel
import json
import time
import os
import re
from urllib.parse import urljoin
from typing import List, Dict, Any
import unicodedata


class RabindraPoetryParser:
    """Parser for handling poem content with proper formatting"""

    @staticmethod
    def remove_bengali_digits(text: str) -> str:
        """Remove Bengali digits from text"""
        bengali_digits = "০১২৩৪৫৬৭৮৯"
        english_digits = "0123456789"

        # Create translation table to remove Bengali and English digits
        translation_table = str.maketrans("", "", bengali_digits + english_digits)
        return text.translate(translation_table)

    @staticmethod
    def process_line(line: str) -> str:
        """Apply common processing to a line: remove digits, normalize, add punctuation spacing"""
        # Remove Bengali and English digits
        line = RabindraPoetryParser.remove_bengali_digits(line)
        # Check if line is empty after digit removal
        if not line.strip():
            return None
        # Unicode normalization
        line = unicodedata.normalize("NFC", line)
        # Add spacing around punctuation
        line = re.sub(r"([।?!,—])", r" \1 ", line)
        return line

    @staticmethod
    def extract_text_with_spacing(element: parsel.Selector) -> str:
        """
        Extract text from an element while preserving spaces represented
        by <font>&nbsp;</font> or inline &nbsp;, but without introducing
        artificial line breaks inside a <p>.
        """
        pieces = []
        for node in element.xpath("./node()"):
            tag = node.root.tag if hasattr(node.root, "tag") else None

            if tag is None:  # text node
                text_val = node.get()
                if text_val:
                    pieces.append(
                        text_val.replace("\xa0", " ")
                        .replace("&nbsp;", " ")
                        .replace("\n", " ")
                    )

            elif tag.lower() == "font":
                inner_text = "".join(node.xpath(".//text()").getall())
                nbsp_count = inner_text.count("\xa0") + inner_text.count("&nbsp;")
                if nbsp_count > 0:
                    pieces.append(" " * nbsp_count)

            elif tag.lower() == "br":
                pieces.append("<line>\n")

            else:
                sub_text = RabindraPoetryParser.extract_text_with_spacing(node)
                if sub_text:
                    pieces.append(sub_text)

        line = "".join(pieces)
        line = re.sub(r"\n+", "\n", line)
        line = line.rstrip()
        processed_line = RabindraPoetryParser.process_line(line)

        # If line becomes empty after processing, return None
        if processed_line is None:
            return None

        return processed_line + "<line>"

    @staticmethod
    def parse_poem_content(selector: parsel.Selector) -> str:
        """Parse poem content handling both scenarios (p tags, br tags, or combination)"""
        kobita_divs = selector.xpath('//div[contains(@id, "kobita")]')
        if not kobita_divs:
            return ""
        kobita_div = kobita_divs[0]

        p_tags = kobita_div.xpath(".//p")
        br_tags = kobita_div.xpath(".//br")

        # Check if we have a combination of p tags and br tags
        if p_tags and br_tags:
            return RabindraPoetryParser.parse_combined_content(kobita_div)
        elif p_tags:
            # Pure p tag scenario
            lines = []
            for p_tag in p_tags:
                line_content = RabindraPoetryParser.extract_text_with_spacing(p_tag)

                if line_content:
                    clean_line = line_content.replace("\n", "").rstrip()
                    if clean_line.strip():
                        lines.append(clean_line)
                    elif clean_line.strip() == "":
                        lines.append("")

            return "\n".join(lines)
        else:
            # Handle br tag scenario - split content by br tags
            return RabindraPoetryParser.parse_br_content(kobita_div)

    @staticmethod
    def parse_combined_content(kobita_div: parsel.Selector) -> str:
        """Parse poem content that contains both p tags and br tags"""
        lines = []
        current_line_parts = []

        # Process all direct children of the kobita div
        for child in kobita_div.xpath("./node()"):
            tag = child.root.tag if hasattr(child.root, "tag") else None

            if tag is None:  # text node
                text_val = child.get()
                if text_val:
                    clean_text = text_val.replace("\n", "").replace("\r", "")
                    clean_text = clean_text.replace("\xa0", " ").replace("&nbsp;", " ")
                    if clean_text:  # Keep all text including whitespace
                        current_line_parts.append(clean_text)

            elif tag.lower() == "p":
                # First, finalize any pending line parts from before this p tag
                if current_line_parts:
                    line = "".join(current_line_parts).rstrip()
                    if line.strip():
                        processed_line = RabindraPoetryParser.process_line(line)
                        if processed_line is not None:
                            lines.append(processed_line + "<line>")
                    current_line_parts = []

                # Check if this is an empty p tag (stanza break) or contains content
                p_text = "".join(child.xpath(".//text()").getall()).strip()
                p_text = p_text.replace("\xa0", "").replace("&nbsp;", "")

                if not p_text:  # Empty p tag - indicates stanza break
                    # Add stanza break - use a placeholder that will be recognized
                    lines.append("<stanza_break>")
                else:
                    # P tag with content - may contain br tags for line breaks
                    # Need to parse the content within the p tag for br tags
                    current_p_line = []

                    # Process all nodes within the p tag
                    for p_node in child.xpath("./node()"):
                        p_tag = p_node.root.tag if hasattr(p_node.root, "tag") else None

                        if p_tag is None:  # text node within p
                            text_val = p_node.get()
                            if text_val:
                                clean_text = text_val.replace("\n", "").replace(
                                    "\r", ""
                                )
                                clean_text = clean_text.replace("\xa0", " ").replace(
                                    "&nbsp;", " "
                                )
                                if clean_text:
                                    current_p_line.append(clean_text)

                        elif p_tag.lower() == "font":
                            # Handle font tags within p
                            inner_text = "".join(p_node.xpath(".//text()").getall())
                            inner_text = inner_text.replace("\n", "").replace("\r", "")
                            nbsp_count = inner_text.count("\xa0") + inner_text.count(
                                "&nbsp;"
                            )
                            if nbsp_count > 0:
                                current_p_line.append(" " * nbsp_count)
                            elif inner_text.strip():
                                clean_text = inner_text.replace("\xa0", " ").replace(
                                    "&nbsp;", " "
                                )
                                if clean_text.strip():
                                    current_p_line.append(clean_text)

                        elif p_tag.lower() == "br":
                            # BR within p tag - finalize current line
                            if current_p_line:
                                line = "".join(current_p_line).rstrip()
                                if line.strip():
                                    processed_line = RabindraPoetryParser.process_line(
                                        line
                                    )
                                    if processed_line is not None:
                                        lines.append(processed_line + "<line>")
                                current_p_line = []

                    # Add any remaining content in the p tag
                    if current_p_line:
                        line = "".join(current_p_line).rstrip()
                        if line.strip():
                            processed_line = RabindraPoetryParser.process_line(line)
                            if processed_line is not None:
                                lines.append(processed_line + "<line>")

            elif tag.lower() == "br":
                # BR tag represents line break - finalize current line
                if current_line_parts:
                    line = "".join(
                        current_line_parts
                    ).rstrip()  # Only strip right side to preserve leading spaces
                    if (
                        line.strip()
                    ):  # Check if there's actual content after stripping both sides
                        processed_line = RabindraPoetryParser.process_line(line)
                        if processed_line is not None:
                            lines.append(processed_line + "<line>")
                    current_line_parts = []

            elif tag.lower() == "font":
                # Handle font tags that might contain spacing or text
                inner_text = "".join(child.xpath(".//text()").getall())
                inner_text = inner_text.replace("\n", "").replace("\r", "")
                nbsp_count = inner_text.count("\xa0") + inner_text.count("&nbsp;")
                if nbsp_count > 0:
                    current_line_parts.append(" " * nbsp_count)
                elif inner_text.strip():
                    clean_text = inner_text.replace("\xa0", " ").replace("&nbsp;", " ")
                    if clean_text.strip():
                        current_line_parts.append(clean_text)

        # Add any remaining content as the last line
        if current_line_parts:
            line = "".join(current_line_parts).rstrip()
            if line.strip():
                processed_line = RabindraPoetryParser.process_line(line)
                if processed_line is not None:
                    lines.append(processed_line + "<line>")

        # Post-process to handle stanza breaks properly
        final_lines = []
        for line in lines:
            if line == "<stanza_break>":
                final_lines.append("<line>")  # Add <line> tag for stanza break
            else:
                final_lines.append(line)

        return "\n".join(final_lines)

    @staticmethod
    def parse_br_content(kobita_div: parsel.Selector) -> str:
        """Parse poem content that uses br tags as line separators"""
        lines = []
        current_line_parts = []

        # Get all child nodes (text and elements)
        for node in kobita_div.xpath("./node()"):
            tag = node.root.tag if hasattr(node.root, "tag") else None

            if tag is None:  # text node
                text_val = node.get()
                if text_val:
                    # Strip native newlines but preserve other spacing
                    clean_text = text_val.replace("\n", "").replace("\r", "")
                    clean_text = clean_text.replace("\xa0", " ").replace("&nbsp;", " ")
                    if clean_text:  # Only add if there's actual content after cleaning
                        current_line_parts.append(clean_text)

            elif tag.lower() == "font":
                # Handle font tags that might contain nbsp - preserve spacing exactly
                inner_text = "".join(node.xpath(".//text()").getall())
                # Strip native newlines from font content too
                inner_text = inner_text.replace("\n", "").replace("\r", "")
                nbsp_count = inner_text.count("\xa0") + inner_text.count("&nbsp;")
                if nbsp_count > 0:
                    current_line_parts.append(" " * nbsp_count)
                else:
                    # Regular text in font tag
                    if inner_text:
                        clean_text = inner_text.replace("\xa0", " ").replace(
                            "&nbsp;", " "
                        )
                        if clean_text:
                            current_line_parts.append(clean_text)

            elif tag.lower() == "br":
                # End current line and start new one - only add line break here
                if current_line_parts:
                    line = "".join(current_line_parts).rstrip()
                    if line:  # Only add non-empty lines
                        # Apply processing to the line before adding to array
                        processed_line = RabindraPoetryParser.process_line(line)
                        if processed_line is not None:
                            lines.append(processed_line + "<line>")
                    current_line_parts = []

        # Add any remaining content as the last line
        if current_line_parts:
            line = "".join(current_line_parts).rstrip()
            if line:
                # Apply processing to the line before adding to array
                processed_line = RabindraPoetryParser.process_line(line)
                if processed_line is not None:
                    lines.append(processed_line + "<line>")

        return "\n".join(lines)


class RabindraPoetryaScraper:
    def __init__(self, base_url: str = "https://rabindra-rachanabali.nltr.org"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )
        self.parser = RabindraPoetryParser()

    def process_stanzas(self, content: str) -> str:
        """
        Process poem content to insert stanza markers where there are consecutive newlines.
        Replaces multiple consecutive newlines with stanza markers.
        """
        import re

        # Find sequences of 2 or more consecutive newlines
        # Replace them with stanza markers
        stanza_count = 1

        def replace_with_stanza(match):
            nonlocal stanza_count
            newlines = match.group(0)
            # Keep first and last newline, insert stanza marker in between
            if len(newlines) >= 2:
                result = newlines[0] + f"<stanza{stanza_count}>" + newlines[-1]
                stanza_count += 1
                return result
            return newlines

        # Pattern to match 2 or more consecutive newlines
        processed_content = re.sub(r"\n{2,}", replace_with_stanza, content)

        return processed_content

    def get_page(self, url: str) -> parsel.Selector:
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return parsel.Selector(text=response.text)
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def get_collection_poems(
        self, subcatid: int, catid: int = 7
    ) -> List[Dict[str, str]]:
        url = f"{self.base_url}/node/4?subcatid={subcatid}&catId={catid}"
        print(f"Fetching collection {subcatid}...")

        selector = self.get_page(url)
        if not selector:
            return []

        poem_links = []
        list_table = selector.xpath('//table[@class="list"]')

        if list_table:
            anchors = list_table.xpath(".//a[@href]")
        else:
            anchors = selector.xpath('//div[contains(@class, "content")]//a[@href]')

        for anchor in anchors:
            href = anchor.xpath("./@href").get()
            title = anchor.xpath(".//text()").get()

            if href and title and "/node/" in href:
                full_url = urljoin(self.base_url, href)
                poem_links.append(
                    {"title": title.strip(), "url": full_url, "collection_id": subcatid}
                )

        print(f"Found {len(poem_links)} poems in collection {subcatid}")
        return poem_links

    def get_next_page_url(self, selector: parsel.Selector) -> str:
        """Find the next page URL by looking for the 'পরবর্তী' link"""
        # Look for anchor tag containing "পরবর্তী" text
        next_links = selector.xpath('//a[contains(.//text(), "পরবর্তী")]/@href').getall()
        if next_links:
            # Return the first next link found, making it absolute
            next_url = next_links[0]
            if next_url.startswith("/"):
                return urljoin(self.base_url, next_url)
            return next_url
        return None

    def scrape_poem(self, poem_info: Dict[str, str]) -> Dict[str, Any]:
        print(f"Scraping: {poem_info['title']}")

        all_content = []
        current_url = poem_info["url"]
        page_count = 1

        while current_url:
            print(f"  Scraping page {page_count}: {current_url}")

            selector = self.get_page(current_url)
            if not selector:
                print(f"  Warning: Could not fetch page {page_count}")
                break

            page_content = self.parser.parse_poem_content(selector)
            if page_content:
                all_content.append(page_content)

            next_url = self.get_next_page_url(selector)

            if next_url and next_url != current_url:
                current_url = next_url
                page_count += 1
                time.sleep(0.5)
            else:
                break

        print(f"  Completed scraping {page_count} page(s)")

        # Combine all pages with page breaks
        combined_content = (
            "\n".join(all_content)
            if len(all_content) > 1
            else (all_content[0] if all_content else "")
        )

        # Process the combined content to add stanza markers
        # processed_content = self.process_stanzas(combined_content)

        return {
            "title": poem_info["title"],
            "url": poem_info["url"],
            "collection_id": poem_info["collection_id"],
            "content": combined_content,
            "total_pages": page_count,
        }

    def scrape_collection(self, subcatid: int) -> List[Dict[str, Any]]:
        poem_links = self.get_collection_poems(subcatid)
        poems = []

        for poem_info in poem_links:
            try:
                poem_data = self.scrape_poem(poem_info)
                if poem_data and poem_data["content"]:
                    poems.append(poem_data)
                time.sleep(1)
            except Exception as e:
                print(f"Error scraping poem {poem_info['title']}: {e}")
                continue

        return poems

    def scrape_all_collections(
        self,
        start_subcatid: int = 1,
        end_subcatid: int = 53,
        json_filename: str = "output/rabindra_poems.json",
        txt_filename: str = "output/rabindra_poems.txt",
    ) -> int:
        """
        Scrape all collections and write poems to files one by one.
        Returns the total number of poems scraped.
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(json_filename), exist_ok=True)
        os.makedirs(os.path.dirname(txt_filename), exist_ok=True)

        total_poems = 0

        # Initialize JSON file with opening bracket
        with open(json_filename, "w", encoding="utf-8") as json_file:
            json_file.write("[\n")

        # Initialize text file (empty)
        with open(txt_filename, "w", encoding="utf-8") as txt_file:
            pass

        for subcatid in range(start_subcatid, end_subcatid + 1):
            try:
                print(f"\n--- Processing Collection {subcatid} ---")
                collection_poems = self.scrape_collection(subcatid)

                # Write each poem immediately to both files
                for i, poem in enumerate(collection_poems):
                    self._append_poem_to_files(
                        poem, json_filename, txt_filename, total_poems > 0
                    )
                    total_poems += 1

                print(
                    f"Scraped {len(collection_poems)} poems from collection {subcatid}"
                )
                time.sleep(2)
            except Exception as e:
                print(f"Error processing collection {subcatid}: {e}")
                continue

        # Close JSON array
        with open(json_filename, "a", encoding="utf-8") as json_file:
            json_file.write("\n]")

        print(f"\nTotal poems scraped: {total_poems}")
        return total_poems

    def save_poems(
        self, poems: List[Dict[str, Any]], filename: str = "output/rabindra_poems.json"
    ):
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(poems, f, ensure_ascii=False, indent=2)

        print(f"\nSaved {len(poems)} poems to {filename}")

    def save_poems_text(
        self, poems: List[Dict[str, Any]], filename: str = "output/rabindra_poems.txt"
    ):
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            for poem in poems:
                # f.write(f"Title: {poem['title']}\n")
                # f.write(f"Collection ID: {poem['collection_id']}\n")
                # f.write(f"URL: {poem['url']}\n")
                # f.write("-" * 50 + "\n")
                f.write("<start_poem>\n")
                # Replace consecutive <line> patterns with <stanza>
                content = poem["content"]
                content = re.sub(r"(\n<line>)+\n", "\n<stanza>\n", content)
                f.write(content)
                f.write("\n<stanza>\n")
                f.write("<end_poem>\n")
                # f.write("\n" + "=" * 80 + "\n\n")

        print(f"Saved {len(poems)} poems to {filename}")

    def _append_poem_to_files(
        self,
        poem: Dict[str, Any],
        json_filename: str,
        txt_filename: str,
        need_comma: bool,
    ):
        """Helper method to append a single poem to both JSON and text files"""
        # Append to JSON file
        with open(json_filename, "a", encoding="utf-8") as json_file:
            if need_comma:
                json_file.write(",\n")
            json.dump(poem, json_file, ensure_ascii=False, indent=2)

        # Append to text file
        with open(txt_filename, "a", encoding="utf-8") as txt_file:
            txt_file.write("<start_poem>\n")
            # Replace consecutive <line> patterns with <stanza>
            content = poem["content"]
            content = re.sub(r"(\n<line>)+\n", "\n<stanza>\n", content)
            txt_file.write(content)
            txt_file.write("\n<stanza>\n")
            txt_file.write("<end_poem>\n")
