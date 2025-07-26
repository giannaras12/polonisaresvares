from config import RANK_EMOJIS

# Define premium rank emojis (1 to 31)
PREMIUM_RANK_EMOJIS = {
    1: '<:rank_1_premremovebgpreview:1398614740778876968>',
    2: '<:rank_2_premremovebgpreview:1398617165271142471>',
    3: '<:rank_3_premremovebgpreview:1398617207654842388>',
    4: '<:rank_4_premremovebgpreview:1398617238516400239>',
    5: '<:rank_5_premremovebgpreview:1398617287522521210>',
    6: '<:rank_6_premremovebgpreview:1398617350563168386>',
    7: '<:rank_7_premremovebgpreview:1398617417805987881>',
    8: '<:rank_8_premremovebgpreview:1398617455877816400>',
    9: '<:rank_9_premremovebgpreview:1398617481567928371>',
    10: '<:rank_10_premremovebgpreview:1398617517978681384>',
    11: '<:rank_11_premremovebgpreview:1398617560056074342>',
    12: '<:rank_12_premremovebgpreview:1398617588040339506>',
    13: '<:rank_13_premremovebgpreview:1398617631845519416>',
    14: '<:rank_14_premremovebgpreview:1398617663512645683>',
    15: '<:rank_15_premremovebgpreview:1398617704621019239>',
    16: '<:rank_16_premremovebgpreview:1398617750028550214>',
    17: '<:rank_17_premremovebgpreview:1398617777002123385>',
    18: '<:rank_18_premremovebgpreview:1398617803363455131>',
    19: '<:rank_19_premremovebgpreview:1398617830588420247>',
    20: '<:rank_20_premremovebgpreview:1398617868777820232>',
    21: '<:rank_21_premremovebgpreview:1398617898209120267>',
    22: '<:rank_22_premremovebgpreview:1398617941750190091>',
    23: '<:rank_23_premremovebgpreview:1398617971303251998>',
    24: '<:rank_24_premremovebgpreview:1398618000877289523>',
    25: '<:rank_25_premremovebgpreview:1398618029587173417>',
    26: '<:rank_26_premremovebgpreview:1398618061141053501>',
    27: '<:rank_27_premremovebgpreview:1398618111615172690>',
    28: '<:rank_28_premremovebgpreview:1398618146092482590>',
    29: '<:rank_29_premremovebgpreview:1398618174072684645>',
    30: '<:rank_30_premremovebgpreview:1398618203894317127>',
    31: '<:rank_31_premremovebgpreview:1398618237519925340>',
}

from utils import get_rank_emoji as original_get_rank_emoji

def get_rank_emoji(rank_name, premium=False):
    """Return the appropriate emoji for a given rank, considering premium status."""
    if rank_name.startswith('Legend'):
        return PREMIUM_RANK_EMOJIS[31] if premium else RANK_EMOJIS[31]

    rank_name = rank_name.lower().replace(' ', '_')
    rank_mapping = {
        'recruit': 1, 'private': 2, 'gefreiter': 3, 'corporal': 4, 'master_corporal': 5,
        'sergeant': 6, 'staff_sergeant': 7, 'master_sergeant': 8, 'first_sergeant': 9, 'sergeant_major': 10,
        'warrant_officer_1': 11, 'warrant_officer_2': 12, 'warrant_officer_3': 13, 'warrant_officer_4': 14, 'warrant_officer_5': 15,
        'third_lieutenant': 16, 'second_lieutenant': 17, 'first_lieutenant': 18, 'captain': 19, 'major': 20,
        'lieutenant_colonel': 21, 'colonel': 22, 'brigadier': 23, 'major_general': 24, 'lieutenant_general': 25,
        'general': 26, 'marshal': 27, 'field_marshal': 28, 'commander': 29, 'generalissimo': 30,
        'colonel_commander': 30, 'brigadier_commander': 30, 'legend': 31
    }

    rank_index = rank_mapping.get(rank_name, 31)
    return PREMIUM_RANK_EMOJIS.get(rank_index) if premium else RANK_EMOJIS.get(rank_index)

# Monkey patch into the bot
import bot
bot.get_rank_emoji = get_rank_emoji
