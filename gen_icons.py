#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_icons.py
------------
產生「府城尋味」PWA 所需的圖示（icons）檔案。

用法：
    pip install Pillow
    python3 gen_icons.py

會在 ./icons 資料夾內產生下列檔案：
    icon-72x72.png
    icon-96x96.png
    icon-128x128.png
    icon-144x144.png
    icon-152x152.png
    icon-192x192.png
    icon-384x384.png
    icon-512x512.png
    icon-maskable-192x192.png   (Android Adaptive Icon 用，含安全邊界)
    icon-maskable-512x512.png
    apple-touch-icon.png        (180x180，給 iOS 使用)
    favicon-32x32.png
    favicon-16x16.png
"""

import os
import math
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# 基本設定
# ---------------------------------------------------------------------------
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")

# 標準 icon 尺寸 (PWA manifest 常用)
STANDARD_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]
# Maskable icon 尺寸 (Android adaptive icon)
MASKABLE_SIZES = [192, 512]
# Apple touch icon
APPLE_TOUCH_SIZE = 180
# Favicon
FAVICON_SIZES = [16, 32]

# 品牌色彩（與網站主題橘色系一致）
COLOR_BG_TOP = (249, 115, 22)     # orange-500
COLOR_BG_BOTTOM = (194, 65, 12)   # orange-700
COLOR_WHITE = (255, 255, 255)
COLOR_BOWL_SHADOW = (0, 0, 0, 40)


def _lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_gradient_background(size):
    """畫出由上到下的橘色漸層背景，回傳 RGBA Image。"""
    img = Image.new("RGBA", (size, size), COLOR_WHITE + (255,))
    draw = ImageDraw.Draw(img)
    for y in range(size):
        t = y / max(size - 1, 1)
        color = _lerp_color(COLOR_BG_TOP, COLOR_BG_BOTTOM, t)
        draw.line([(0, y), (size, y)], fill=color + (255,))
    return img


def draw_bowl_icon(draw, cx, cy, r):
    """
    在指定圓心 (cx, cy)、半徑 r 的區域內，畫出簡化的「湯碗 + 熱氣 + 筷子」
    圖案，代表台南美食（牛肉湯 / 擔仔麵）意象。
    """
    # 碗身（梯形＋弧形底）
    bowl_top_w = r * 1.6
    bowl_bottom_w = r * 1.05
    bowl_h = r * 0.85

    top_left = (cx - bowl_top_w / 2, cy - bowl_h * 0.15)
    top_right = (cx + bowl_top_w / 2, cy - bowl_h * 0.15)
    bottom_left = (cx - bowl_bottom_w / 2, cy + bowl_h * 0.7)
    bottom_right = (cx + bowl_bottom_w / 2, cy + bowl_h * 0.7)

    # 碗身主體（白色，帶一點陰影效果用兩層畫）
    bowl_bbox = [
        top_left[0], top_left[1] - r * 0.1,
        top_right[0], bottom_left[1] + r * 0.35,
    ]
    draw.pieslice(
        [cx - bowl_top_w / 2, cy - bowl_h * 0.15, cx + bowl_top_w / 2, cy + bowl_h * 1.05],
        0, 180, fill=COLOR_WHITE
    )
    draw.rectangle(
        [cx - bowl_top_w / 2, cy - bowl_h * 0.15, cx + bowl_top_w / 2, cy + bowl_h * 0.3],
        fill=COLOR_WHITE
    )
    draw.polygon(
        [top_left, top_right, bottom_right, bottom_left],
        fill=COLOR_WHITE
    )
    draw.pieslice(
        [cx - bowl_bottom_w / 2, cy + bowl_h * 0.05, cx + bowl_bottom_w / 2, cy + bowl_h * 1.05],
        0, 180, fill=COLOR_WHITE
    )

    # 碗口橢圓（湯的邊緣，用主題橘色畫細邊）
    rim_h = r * 0.22
    draw.ellipse(
        [cx - bowl_top_w / 2, cy - bowl_h * 0.15 - rim_h / 2,
         cx + bowl_top_w / 2, cy - bowl_h * 0.15 + rim_h / 2],
        fill=COLOR_BG_TOP
    )
    inner_margin = bowl_top_w * 0.12
    draw.ellipse(
        [cx - bowl_top_w / 2 + inner_margin, cy - bowl_h * 0.15 - rim_h / 2 + rim_h * 0.25,
         cx + bowl_top_w / 2 - inner_margin, cy - bowl_h * 0.15 + rim_h / 2 - rim_h * 0.1],
        fill=(255, 237, 213)  # orange-100 湯色
    )

    # 熱氣（三條簡單波浪線）
    steam_color = (255, 255, 255, 230)
    for i, dx in enumerate([-r * 0.45, 0, r * 0.45]):
        sx = cx + dx
        top_y = cy - bowl_h * 0.55
        pts = []
        wave_h = r * 0.5
        segments = 10
        for s in range(segments + 1):
            t = s / segments
            y = top_y - t * wave_h
            x = sx + math.sin(t * math.pi * 2) * r * 0.08
            pts.append((x, y))
        if len(pts) > 1:
            draw.line(pts, fill=steam_color, width=max(2, int(r * 0.05)))


def build_icon(size, maskable=False):
    """建立單一尺寸的圖示，回傳 PIL Image。"""
    canvas_size = size
    img = draw_gradient_background(canvas_size)
    draw = ImageDraw.Draw(img)

    if maskable:
        # Maskable icon 需要保留安全邊界（約 40% 內縮），避免被系統裁切遮罩切到重要內容
        safe_r = size * 0.30
        cx, cy = size / 2, size / 2 + size * 0.02
    else:
        safe_r = size * 0.34
        cx, cy = size / 2, size / 2 + size * 0.03

    draw_bowl_icon(draw, cx, cy, safe_r)

    # 底部加上「府城」字樣（尺寸夠大才畫，避免小圖示糊成一團）
    if size >= 96:
        try:
            font_size = int(size * 0.16)
            font = ImageFont.load_default(font_size) if hasattr(ImageFont, "load_default") else None
        except Exception:
            font = None

        text = "府城"
        if font:
            bbox = draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            tx = (size - tw) / 2 - bbox[0]
            ty = size * 0.78 - th / 2 - bbox[1]
            draw.text((tx, ty), text, font=font, fill=COLOR_WHITE)

    return img


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"輸出資料夾: {OUTPUT_DIR}")

    for size in STANDARD_SIZES:
        img = build_icon(size, maskable=False)
        path = os.path.join(OUTPUT_DIR, f"icon-{size}x{size}.png")
        img.save(path, "PNG")
        print(f"  已產生 {path}")

    for size in MASKABLE_SIZES:
        img = build_icon(size, maskable=True)
        path = os.path.join(OUTPUT_DIR, f"icon-maskable-{size}x{size}.png")
        img.save(path, "PNG")
        print(f"  已產生 {path}")

    apple_img = build_icon(APPLE_TOUCH_SIZE, maskable=False)
    apple_path = os.path.join(OUTPUT_DIR, "apple-touch-icon.png")
    apple_img.save(apple_path, "PNG")
    print(f"  已產生 {apple_path}")

    for size in FAVICON_SIZES:
        fav_img = build_icon(size, maskable=False)
        fav_path = os.path.join(OUTPUT_DIR, f"favicon-{size}x{size}.png")
        fav_img.save(fav_path, "PNG")
        print(f"  已產生 {fav_path}")

    print("全部圖示產生完成！")


if __name__ == "__main__":
    main()
