#!/usr/bin/env python3
"""
Generate a weight loss daily report (减重日报) as HTML + PNG.

Usage:
    python generate_report.py --html output.html --png output.png

This script is meant to be called by Claude after it has:
1. Parsed the user's chat log / meal data
2. Prepared a JSON data file with the report content

It reads report_data.json, fills the template, embeds fonts, and screenshots to PNG.
"""

import asyncio
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
TEMPLATE_PATH = os.path.join(SKILL_DIR, "assets", "template.html")


def load_template():
    with open(TEMPLATE_PATH, "r") as f:
        return f.read()


def build_font_css(text_content):
    """Import and use the font builder."""
    sys.path.insert(0, SCRIPT_DIR)
    from build_font_css import build_embedded_css
    return build_embedded_css(text_content)


def fill_template(template, data, font_css):
    """Replace placeholders in the template with actual data."""
    replacements = {
        "ZCOOL_FONT_PLACEHOLDER": font_css,
    }
    
    html = template
    for key, value in replacements.items():
        html = html.replace(key, str(value))
    
    return html


async def screenshot_html(html_path, png_path):
    """Use Playwright to screenshot HTML as PNG."""
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 750, "height": 800})
        await page.goto(f"file://{os.path.abspath(html_path)}")
        await page.evaluate("() => document.fonts.ready")
        await page.wait_for_timeout(4000)
        await page.screenshot(path=png_path, full_page=True)
        await page.close()
        await browser.close()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="report_data.json", help="JSON data file")
    parser.add_argument("--html", default="report.html", help="Output HTML path")
    parser.add_argument("--png", default="report.png", help="Output PNG path")
    args = parser.parse_args()
    
    # Load data
    with open(args.data, "r") as f:
        data = json.load(f)
    
    # Load template
    template = load_template()
    
    # Collect all Chinese text for font subsetting
    all_text = json.dumps(data, ensure_ascii=False)
    font_css = build_font_css(all_text)
    
    # Fill template
    html = fill_template(template, data, font_css)
    
    # Write HTML
    with open(args.html, "w") as f:
        f.write(html)
    print(f"HTML written to {args.html}")
    
    # Screenshot
    asyncio.run(screenshot_html(args.html, args.png))
    print(f"PNG written to {args.png}")


if __name__ == "__main__":
    main()
