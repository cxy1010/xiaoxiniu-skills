---
name: weight-loss-daily-report
description: >
  Generate a beautiful "receipt-style" daily weight loss report (减重日报) from user chat logs or meal data.
  Trigger this skill whenever the user uploads weight loss coaching chat logs, diet tracking conversations,
  or meal records and asks to "generate a daily report", "make a daily summary", "create a 日报", or
  "生成日报/减重日报". Also trigger when the user says things like "summarize today's meals",
  "how did I eat today", or provides food intake data and wants a visual report.
  The output is a receipt/ticket-style HTML long image (PNG) using ZCOOL KuaiLe handwriting font for
  Chinese text and monospace font for numbers, optimized for sharing on WeChat.
---

# Weight Loss Daily Report (减重日报)

## Overview

This skill generates a visually polished "receipt ticket" style daily report for weight loss coaching users. It parses meal data from chat logs, calculates calories, generates personalized review and action items, and outputs a shareable HTML + PNG image.

## Design Specifications

- **Style**: Receipt/ticket with torn-edge zigzag top border, dashed separators, barcode footer
- **Fonts**: ZCOOL KuaiLe (站酷快乐体) for Chinese text, Noto Sans Mono CJK SC for numbers/data
- **Colors**: Warm paper background (#FEFCF7), dark text (#2A2A2A), red for over-target (#C0392B), green for on-target (#27AE60)
- **Width**: 750px (optimized for mobile/WeChat sharing)
- **Output**: HTML file with embedded fonts (base64 woff2) + PNG screenshot via Playwright

## Workflow

### Step 1: Parse the Input

Read the user's uploaded chat log or meal data. Extract for the target date:
- **Meals**: breakfast, lunch, dinner (time, food items, estimated calories)
- **Calorie target**: default 1500 kcal if not specified
- **Streak**: consecutive check-in days
- **Date**: the report date

If the input is a raw chat log (e.g., WeChat export), parse timestamps and food descriptions. Use nutritional knowledge to estimate calories for Chinese dishes.

### Step 2: Analyze and Generate Content

For each meal, determine:
- Calorie estimate
- Whether it's over or under the per-meal target (breakfast ~350, lunch ~550, dinner ~450, with ~150 buffer)
- Total daily intake vs target

Generate:
- **Today's review** (今日点评): 2-3 sentences. Highlight what was done well, identify the main problem, suggest a specific swap. Use warm encouraging tone.
- **Tomorrow's focus** (明天重点): 1-2 concrete actionable items as checkbox tasks.

### Step 3: Install Font

The skill requires ZCOOL KuaiLe font. Install it via npm:

```bash
npm install @fontsource/zcool-kuaile
```

Then prepare the embedded font CSS. See `scripts/build_font_css.py` for the helper that:
1. Reads the fontsource CSS
2. Identifies which woff2 subsets are needed for the Chinese characters in the report
3. Base64-encodes only the required subsets
4. Outputs a single CSS string for embedding in HTML

### Step 4: Generate HTML

Use the template structure in `assets/template.html`. Fill in the data placeholders:

```
{{FONT_CSS}}        - Base64-embedded @font-face CSS
{{DATE}}            - e.g., 2026-02-27
{{WEEKDAY}}         - e.g., FRI
{{WEEKDAY_CN}}      - e.g., 星期五  (not used in current template but available)
{{STREAK_DAYS}}     - consecutive check-in days number
{{TOTAL_KCAL}}      - total daily calorie intake
{{TARGET_KCAL}}     - calorie target (default 1500)
{{OVER_UNDER}}      - "超出 XXX kcal"（红色）或 "目标达成"（绿色）
{{OVER_CLASS}}      - "over" or "ok" (CSS class for coloring)
{{BREAKFAST_TIME}}  - e.g., 07:47
{{BREAKFAST_KCAL}}  - calorie number
{{BREAKFAST_CLASS}} - "over" or "ok"
{{BREAKFAST_FOOD}}  - food description string
{{LUNCH_TIME}}      - e.g., 11:32
{{LUNCH_KCAL}}      - calorie number
{{LUNCH_CLASS}}     - "over" or "ok"
{{LUNCH_FOOD}}      - food description string
{{DINNER_TIME}}     - e.g., 20:00
{{DINNER_KCAL}}     - calorie number
{{DINNER_CLASS}}    - "over" or "ok"
{{DINNER_FOOD}}     - food description string
{{REVIEW_TEXT}}     - HTML string with <strong> tags for emphasis
{{TOMORROW_ITEM_1}} - first action item HTML with <strong> tags
{{TOMORROW_ITEM_2}} - second action item HTML with <strong> tags
{{BRAND_NAME}}      - default "小犀牛"
```

### Step 5: Screenshot to PNG

Use Playwright to screenshot the HTML as a full-page PNG:

```python
import asyncio
from playwright.async_api import async_playwright

async def screenshot(html_path, png_path):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 750, "height": 800})
        await page.goto(f"file://{html_path}")
        await page.evaluate("() => document.fonts.ready")
        await page.wait_for_timeout(4000)
        await page.screenshot(path=png_path, full_page=True)
        await page.close()
        await browser.close()

asyncio.run(screenshot("/path/to/report.html", "/path/to/report.png"))
```

Ensure Playwright and Chromium are installed:
```bash
playwright install chromium
playwright install-deps chromium
```

### Step 6: Output

Save both files:
- `减重日报_YYYY-MM-DD.html` — self-contained HTML with embedded fonts, viewable in any browser
- `减重日报_YYYY-MM-DD.png` — 750px wide long image for WeChat sharing

Copy to `/mnt/user-data/outputs/` and present to user using `present_files`.

## Key Design Rules

1. **Font separation**: Chinese text uses `.hw` class (ZCOOL KuaiLe), ALL numbers/times/percentages/kcal use `.mono` class (monospace). Never mix.
2. **Color restraint**: Only two semantic colors — red (#C0392B) for over-target, default dark (#2A2A2A) for on-target. No orange, no yellow.
3. **Calorie status**: Over target → red "超出 XXX kcal"; on/under target → green "目标达成". No emoji in the report image (server lacks emoji fonts).
4. **Warm tone**: Review text should feel like a supportive friend, not a clinical report. Use ZCOOL KuaiLe's round character shapes to reinforce this.
5. **Font embedding**: Always embed font subsets as base64 in HTML so it renders correctly on any device without installing fonts.
