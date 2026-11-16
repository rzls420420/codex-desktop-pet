from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
font = ImageFont.truetype(FONT, 23)
small = ImageFont.truetype(FONT, 16)
scenes = [
    ('waving', 4, ['哼，本小姐来帮你了。']),
    ('running', 6, ['任务开始，还是要看本小姐的！']),
    ('jumping', 5, ['本小姐已经完成任务啦。']),
    ('idle', 6, ['额度查询（模拟）', '五小时剩余 75%  ·  每周剩余 60%']),
    ('sleep', 8, ['暂时没有任务，本小姐先休息一下。']),
]
frames = []
for state, count, lines in scenes:
    for repeat in range(2):
        for index in range(count):
            sprite = Image.open(ROOT / 'assets/transparent-v2' / state / f'{index:02}.png').convert('RGBA')
            sprite.thumbnail((300, 280), Image.Resampling.LANCZOS)
            frame = Image.new('RGBA', (760, 340), '#f5f7fb')
            frame.alpha_composite(sprite, (20 + (300 - sprite.width) // 2, 330 - sprite.height))
            draw = ImageDraw.Draw(frame)
            draw.rounded_rectangle((320, 72, 730, 220), radius=16, fill='white', outline='#c8c5d9', width=2)
            for line_no, line in enumerate(lines):
                draw.text((340, 103 + line_no * 42), line, font=font if line_no == 0 else small, fill='#29263b')
            draw.text((342, 238), '演示画面  ·  额度为模拟数据', font=small, fill='#696779')
            frames.append(frame.convert('RGB'))
frames[0].save(ROOT / 'docs/demo.gif', save_all=True, append_images=frames[1:], duration=170, loop=0, optimize=True)
