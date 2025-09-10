#!/usr/bin/env python3
"""
Rabindra Poetry Scraper
Scrapes poems from rabindra-rachanabali.nltr.org

Usage:
    uv run main.py
"""

from poem_scraper import RabindraPoetryaScraper


def main():
    scraper = RabindraPoetryaScraper()

    # Test with first collection
    # print("Testing with collection 1...")
    # test_poems = scraper.scrape_collection(53)
    # if test_poems:
    #     print(f"Test successful! Found {len(test_poems)} poems")
    #     scraper.save_poems(test_poems, "output/rabindra_poems_test.json")
    #     scraper.save_poems_text(test_poems, "output/rabindra_poems_test.txt")
    # else:
    #     print("Test failed. Please check the website structure.")

    # Scrape all collections
    print("Starting full scrape of all collections...")
    all_poems = scraper.scrape_all_collections()
    if all_poems:
        print(f"Scrape completed! Found {all_poems} poems in total.")
    else:
        print("No poems found. Please check the website structure.")


if __name__ == "__main__":
    main()
