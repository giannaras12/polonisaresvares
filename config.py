"""
Configuration file for the RTanks Discord Bot.
Contains emojis, constants, and other configuration values.
"""

# Custom rank emojis (emoji1 to emoji31)
RANK_EMOJIS = {
    1: '<:emoji_1:1394987021415743588>',   # Recruit
    2: '<:emoji_2:1394987069088206929>',   # Private
    3: '<:emoji_3:1394987101941923930>',   # Gefreiter
    4: '<:emoji_4:1394987134980587630>',   # Corporal
    5: '<:emoji_5:1394987177284468767>',   # Master Corporal
    6: '<:emoji_6:1394987207583989830>',   # Sergeant
    7: '<:emoji_7:1394987243629969581>',   # Staff Sergeant
    8: '<:emoji_8:1394987270146097202>',   # Master Sergeant
    9: '<:emoji_9:1394987302379458591>',   # First Sergeant
    10: '<:emoji_10:1394987333488480256>', # Sergeant Major
    11: '<:emoji_11:1394987701048049726>', # Warrant Officer
    12: '<:emoji_12:1394987730722754641>', # Master Warrant Officer
    13: '<:emoji_13:1394987756412866632>', # Second Lieutenant
    14: '<:emoji_14:1394987853104156823>', # First Lieutenant
    15: '<:emoji_15:1394987883760324631>', # Captain
    16: '<:emoji_16:1394988524285198356>', # Major
    17: '<:emoji_17:1394988592517873775>', # Lieutenant Colonel
    18: '<:emoji_18:1394988631609049169>', # Colonel
    19: '<:emoji_19:1394988655252078743>', # Brigadier
    20: '<:emoji_20:1394988771665248286>', # Major General
    21: '<:emoji_21:1394988797569142845>', # Lieutenant General
    22: '<:emoji_22:1394988842557112331>', # General
    23: '<:emoji_23:1394988970110222387>', # Marshal
    24: '<:emoji_24:1394989066667425842>', # Field Marshal
    25: '<:emoji_25:1394989098200207410>', # Commander
    26: '<:emoji_26:1394989131364565053>', # Lieutenant Commander
    27: '<:emoji_27:1394989164709019708>', # Captain Commander
    28: '<:emoji_28:1394989205662339082>', # Major Commander
    29: '<:emoji_29:1394989245978116217>', # Lieutenant Colonel Commander
    30: '<:emoji_30:1394989278005559378>', # Colonel Commander/Brigadier Commander/Generalissimo
    31: '<:emoji_31:1394989379642064948>', # Legend/Legend Premium
}

# Special emojis
GOLD_BOX_EMOJI = '<:emoji_32:1395002503472484352>'  # Gold boxes emoji
PREMIUM_EMOJI = '<:emoji_33:1395399425102184609>'   # Premium emoji

# RTanks website configuration
RTANKS_BASE_URL = "https://ratings.ranked-rtanks.online"
RTANKS_TIMEOUT = 30  # seconds

# Bot configuration
BOT_PREFIX = "!"
DEFAULT_EMBED_COLOR = 0x00ff00  # Green
ERROR_EMBED_COLOR = 0xff0000    # Red
WARNING_EMBED_COLOR = 0xffa500  # Orange

# Rate limiting
REQUEST_DELAY_MIN = 0.5  # minimum delay between requests (seconds)
REQUEST_DELAY_MAX = 1.5  # maximum delay between requests (seconds)

# Equipment lists for parsing
TURRET_NAMES = [
    'Smoky', 'Rail', 'Hunter', 'Wasp', 'Dictator', 'Thunder', 'Freeze', 
    'Isida', 'Twins', 'Ricochet', 'Scorpion', 'Vulcan', 'Shaft', 
    'Magnum', 'Hammer', 'Firebird', 'Striker', 'Gauss'
]

HULL_NAMES = [
    'Hornet', 'Wasp', 'Hunter', 'Viking', 'Dictator', 'Titan', 
    'Mammoth', 'Smoky', 'Crusader'
]

# Known rank names for parsing
RANK_NAMES = [
    'Recruit', 'Private', 'Gefreiter', 'Corporal', 'Master Corporal',
    'Sergeant', 'Staff Sergeant', 'Master Sergeant', 'First Sergeant',
    'Sergeant Major', 'Warrant Officer', 'Master Warrant Officer',
    'Second Lieutenant', 'First Lieutenant', 'Captain', 'Major',
    'Lieutenant Colonel', 'Colonel', 'Brigadier', 'Major General',
    'Lieutenant General', 'General', 'Marshal', 'Field Marshal',
    'Commander', 'Lieutenant Commander', 'Captain Commander',
    'Major Commander', 'Lieutenant Colonel Commander', 'Colonel Commander',
    'Brigadier Commander', 'Generalissimo', 'Legend', 'Legend Premium'
]

# User agents for web scraping
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
]
