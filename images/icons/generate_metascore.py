import colorsys
import json

from PIL import Image, ImageColor, ImageDraw, ImageFont

ICON_SIZE = 128
ICON_RADIUS = 0.1 * ICON_SIZE
ICON_STROKE = 1

FONT_SIZE = ICON_SIZE // 2
BADGE_PARAMETERS = [
    {
        'score_start': 0,
        'score_end': 19,
        'color': '#f00',  # RED
        'comment': 'Overwhelming dislike',
    },
    {
        'score_start': 20,
        'score_end': 39,
        'color': '#f00',  # RED
        'comment': 'Generally unfavorable reviews',
    },
    {
        'score_start': 40,
        'score_end': 60,
        'color': '#fc3',  # YELLOW
        'comment': 'Mixed or average reviews',
    },
    {
        'score_start': 61,
        'score_end': 80,
        'color': '#6c3',  # GREEN
        'comment': 'Generally favorable reviews',
    },
    {
        'score_start': 81,
        'score_end': 100,
        'color': '#6c3',  # GREEN
        'comment': 'Universal acclaim',
    },
]


def darker_color(color, rel_ratio=0.9):
    rgb = ImageColor.getrgb(color)
    h, l, s = colorsys.rgb_to_hls(*map(lambda x: x / 255, rgb))
    l = min(1, l * rel_ratio)  # noqa: E741
    rgb = colorsys.hls_to_rgb(h, l, s)
    return tuple(map(lambda x: int(x * 255), rgb))


def get_badge_color(score):
    for badge in BADGE_PARAMETERS:
        if badge['score_start'] <= score <= badge['score_end']:
            return badge['color']


def create_badge(score, color):
    img = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), (255, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(((0, 0), (ICON_SIZE, ICON_SIZE)),
                           fill=color, radius=ICON_RADIUS)

    font = ImageFont.truetype('Arial_Bold.ttf', FONT_SIZE)
    draw.text((ICON_SIZE/2, ICON_SIZE/2), str(score),
              font=font, fill='white', anchor='mm',
              stroke_fill=darker_color(color, 0.95), stroke_width=ICON_STROKE)

    img.save(f'metascore/{score}.png', 'PNG')


if __name__ == '__main__':
    meta_data = {}
    for score in range(0, 100 + 1):
        create_badge(score, get_badge_color(score))

        meta_data[score] = {
            'path': f'metascore/{score}.png',
            'width': ICON_SIZE,
            'height': ICON_SIZE,
        }

    with open('metascore.json', 'w') as f:
        json.dump(meta_data, f, indent=4)
