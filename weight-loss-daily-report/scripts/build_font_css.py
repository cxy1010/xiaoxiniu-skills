#!/usr/bin/env python3
"""
Build embedded font CSS for the weight loss daily report.

Given the text content of a report, this script:
1. Finds the ZCOOL KuaiLe fontsource package
2. Identifies which woff2 subsets cover the characters used
3. Base64-encodes only those subsets
4. Outputs a CSS string with @font-face rules ready to embed in HTML

Usage:
    python build_font_css.py --text "减重日报今天吃了..." --output font.css
    python build_font_css.py --html report.html --output font.css
"""

import argparse
import base64
import os
import re
import sys


def find_fontsource_css():
    """Find the ZCOOL KuaiLe index.css from node_modules."""
    candidates = [
        os.path.join(os.getcwd(), "node_modules/@fontsource/zcool-kuaile/index.css"),
        os.path.expanduser("~/.npm-global/lib/node_modules/@fontsource/zcool-kuaile/index.css"),
        os.path.join(os.path.dirname(__file__), "../node_modules/@fontsource/zcool-kuaile/index.css"),
    ]
    # Also search upward from cwd
    d = os.getcwd()
    for _ in range(5):
        p = os.path.join(d, "node_modules/@fontsource/zcool-kuaile/index.css")
        if os.path.exists(p):
            return p
        d = os.path.dirname(d)
    
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def extract_chinese_chars(text):
    """Extract unique CJK characters from text."""
    codepoints = set()
    for ch in text:
        cp = ord(ch)
        if cp > 0x2000:  # CJK and beyond
            codepoints.add(cp)
    return sorted(codepoints)


def build_embedded_css(text_content):
    """Build base64-embedded @font-face CSS for the given text content."""
    css_path = find_fontsource_css()
    if not css_path:
        print("ERROR: ZCOOL KuaiLe font not found. Run: npm install @fontsource/zcool-kuaile", file=sys.stderr)
        sys.exit(1)
    
    font_dir = os.path.dirname(css_path)
    
    with open(css_path, "r") as f:
        css = f.read()
    
    codepoints = extract_chinese_chars(text_content)
    if not codepoints:
        print("WARNING: No CJK characters found in text", file=sys.stderr)
        return ""
    
    # Parse @font-face blocks and find needed ones
    needed_css = ""
    for block in css.split("@font-face"):
        if "unicode-range" not in block:
            continue
        
        range_match = re.search(r"unicode-range:\s*([^;]+);", block)
        file_match = re.search(r"url\(\./files/([^)]+\.woff2)\)", block)
        if not range_match or not file_match:
            continue
        
        ranges_str = range_match.group(1)
        filename = file_match.group(1)
        filepath = os.path.join(font_dir, "files", filename)
        
        if not os.path.exists(filepath):
            continue
        
        # Check if any of our characters fall in this range
        needed = False
        for r in ranges_str.split(","):
            r = r.strip()
            if "-" in r and r.startswith("U+"):
                parts = r.replace("U+", "").split("-")
                start = int(parts[0], 16)
                end = int(parts[1], 16)
                for cp in codepoints:
                    if start <= cp <= end:
                        needed = True
                        break
            elif r.startswith("U+"):
                val = int(r.replace("U+", ""), 16)
                if val in codepoints:
                    needed = True
            if needed:
                break
        
        if not needed:
            continue
        
        # Base64 encode the woff2 file
        with open(filepath, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        
        # Replace url with data URI and remove woff fallback
        new_block = block.replace(
            f"url(./files/{filename}) format('woff2')",
            f"url(data:font/woff2;base64,{b64}) format('woff2')"
        )
        new_block = re.sub(r",\s*url\([^)]+\.woff\)\s*format\('woff'\)", "", new_block)
        
        needed_css += "@font-face" + new_block
    
    return needed_css


def main():
    parser = argparse.ArgumentParser(description="Build embedded font CSS")
    parser.add_argument("--text", help="Text content to subset fonts for")
    parser.add_argument("--html", help="HTML file to extract text from")
    parser.add_argument("--output", "-o", default="-", help="Output CSS file (default: stdout)")
    args = parser.parse_args()
    
    if args.html:
        with open(args.html, "r") as f:
            # Strip HTML tags to get text content
            content = re.sub(r"<[^>]+>", "", f.read())
    elif args.text:
        content = args.text
    else:
        # Default: all common Chinese chars used in weight loss reports
        content = (
            "减重日报今天吃了千卡目标超出低于三餐明细早餐午餐晚餐达标"
            "今日点评明天重点连续打卡避开蒸煮蛋白质食只选一种或不叠加"
            "执行力很好全在晚餐换成清炒蔬菜瘦肉就是完美的天油炸类和腐竹"
            "热量太高占鸡蛋牛奶玉米核桃包胡萝卜豆芽菜花半碗米饭茄子角"
            "本豆腐丸笋丝肉听建议把减主动犀小牛"
            "红薯土丝饭烧钵条拌汤面线粉粥馒头饼干果蔬水煮番茄白黄瓜"
            "西葫芦青椒洋葱胡椒盐糖酱油醋辣椒花椒姜蒜葱香菜芹菜生菜"
            "紫薯南瓜冬瓜苦瓜丝瓜豌豆毛豆黑豆红豆绿豆腰果杏仁核桃"
            "猪牛羊鸡鸭鱼虾蟹贝螺蚌鲍参燕窝银耳木耳海带紫菜"
            "超棒不错加油继续保持努力坚持突破进步提升改善注意控制"
            "星期一二三四五六日周末工作休息运动散步跑步游泳瑜伽"
        )
    
    css = build_embedded_css(content)
    
    if args.output == "-":
        print(css)
    else:
        with open(args.output, "w") as f:
            f.write(css)
        print(f"Font CSS written to {args.output} ({len(css) // 1024} KB)", file=sys.stderr)


if __name__ == "__main__":
    main()
