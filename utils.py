"""
Utility functions for the RTanks Discord Bot.
"""

import math
import re
from config import RANK_EMOJIS

def format_number(num):
    """Format a number with appropriate suffixes (K, M, B)."""
    if num == 0:
        return "0"
    
    if num < 1000:
        return str(num)
    elif num < 1000000:
        return f"{num/1000:.1f}K"
    elif num < 1000000000:
        return f"{num/1000000:.1f}M"
    else:
        return f"{num/1000000000:.1f}B"

def format_exact_number(num):
    """Format a number with comma separators for exact display."""
    return f"{num:,}"

def get_rank_emoji(rank_name):
    """Get the appropriate emoji for a rank."""
    # Handle dynamic Legend ranks (Legend 1, Legend 2, etc.)
    if rank_name.startswith('Legend'):
        return RANK_EMOJIS.get(31, '🏆')  # All Legend ranks use emoji 31
    
    rank_name = rank_name.lower().replace(' ', '_')
    
    # Map rank names to emoji indices based on the new rank chart
    rank_mapping = {
        'recruit': 1,
        'private': 2,
        'gefreiter': 3,
        'corporal': 4,
        'master_corporal': 5,
        'sergeant': 6,
        'staff_sergeant': 7,
        'master_sergeant': 8,
        'first_sergeant': 9,
        'sergeant_major': 10,
        'warrant_officer_1': 11,
        'warrant_officer_2': 12,
        'warrant_officer_3': 13,
        'warrant_officer_4': 14,
        'warrant_officer_5': 15,
        'third_lieutenant': 16,
        'second_lieutenant': 17,
        'first_lieutenant': 18,
        'captain': 19,
        'major': 20,
        'lieutenant_colonel': 21,
        'colonel': 22,
        'brigadier': 23,
        'major_general': 24,
        'lieutenant_general': 25,
        'general': 26,
        'marshal': 27,
        'field_marshal': 28,
        'commander': 29,
        'generalissimo': 30,
        'legend': 31,
        'legend_premium': 31
    }
    
    emoji_index = rank_mapping.get(rank_name, 31)  # Default to legend
    return RANK_EMOJIS.get(emoji_index, '🏆')

def format_duration(seconds):
    """Format duration in seconds to a readable string."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
    else:
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        return f"{days}d {hours}h"

def calculate_kd_ratio(kills, deaths):
    """Calculate K/D ratio safely."""
    if deaths == 0:
        return str(kills) if kills > 0 else "0.00"
    return f"{kills/deaths:.2f}"

def extract_numbers(text):
    """Extract all numbers from a text string."""
    import re
    return [int(match) for match in re.findall(r'\d+', text)]

def sanitize_username(username):
    """Sanitize username for safe URL usage."""
    import re
    return re.sub(r'[^a-zA-Z0-9_-]', '', username)

def get_max_experience_for_rank(rank):
    """Get the maximum experience for a given rank based on the progression chart."""
    rank_experience_map = {
        'Recruit': 400,
        'Private': 1000, 
        'Gefreiter': 2200,
        'Corporal': 4400,
        'Master Corporal': 7700,
        'Sergeant': 12300,
        'Staff Sergeant': 20000,
        'Master Sergeant': 29000,
        'First Sergeant': 41000,
        'Sergeant Major': 57000,
        'Warrant Officer 1': 76000,
        'Warrant Officer 2': 98000,
        'Warrant Officer 3': 125000,
        'Warrant Officer 4': 156000,
        'Warrant Officer 5': 192000,
        'Third Lieutenant': 233000,
        'Second Lieutenant': 280000,
        'First Lieutenant': 332000,
        'Captain': 390000,
        'Major': 455000,
        'Lieutenant Colonel': 527000,
        'Colonel': 606000,
        'Brigadier': 695000,
        'Major General': 787000,
        'Lieutenant General': 889000,
        'General': 1000000,
        'Marshal': 1122000,
        'Field Marshal': 1255000,
        'Commander': 1400000,
        'Generalissimo': 1600000,
        'Legend': 1800000  # Base for Legend 1, increases by 200k each level
    }
    
    # Handle Legend ranks with levels
    if rank.startswith('Legend'):
        if rank == 'Legend':
            return 1800000  # Legend 1 max
        else:
            # Extract level from "Legend X" format
            try:
                level = int(rank.split(' ')[1])
                return 1600000 + (level * 200000)  # Base + level * 200k
            except (IndexError, ValueError):
                return 1800000
    
    return rank_experience_map.get(rank, 0)

def extract_modification_level(equipment_name):
    """Extract modification level (M0, M1, M2, M3) from equipment name."""
    # Look for M followed by a number
    match = re.search(r'M(\d+)', equipment_name, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 0  # Default to M0 if no modification found

def get_equipment_quality_score(equipment_list):
    """Calculate equipment quality score based on M3 priority."""
    if not equipment_list:
        return 0, []
    
    m3_count = 0
    highest_m_level = 0
    equipment_details = []
    
    for equipment in equipment_list:
        mod_level = extract_modification_level(equipment)
        equipment_details.append((equipment, mod_level))
        
        if mod_level == 3:
            m3_count += 1
        
        if mod_level > highest_m_level:
            highest_m_level = mod_level
    
    # Score calculation: M3s are worth 1000 points each, other Ms are worth their level * 10
    score = m3_count * 1000
    for equipment, mod_level in equipment_details:
        if mod_level != 3:  # Don't double count M3s
            score += mod_level * 10
    
    return score, equipment_details

def compare_equipment_quality(player1_equipment, player2_equipment):
    """Compare equipment quality between two players based on M3 priority."""
    # Combine all equipment for each player
    p1_all_equipment = []
    p2_all_equipment = []
    
    if player1_equipment:
        p1_all_equipment.extend(player1_equipment.get('turrets', []))
        p1_all_equipment.extend(player1_equipment.get('hulls', []))
    
    if player2_equipment:
        p2_all_equipment.extend(player2_equipment.get('turrets', []))
        p2_all_equipment.extend(player2_equipment.get('hulls', []))
    
    # Get quality scores and details
    p1_score, p1_details = get_equipment_quality_score(p1_all_equipment)
    p2_score, p2_details = get_equipment_quality_score(p2_all_equipment)
    
    # Count M3s for each player
    p1_m3_count = sum(1 for _, mod_level in p1_details if mod_level == 3)
    p2_m3_count = sum(1 for _, mod_level in p2_details if mod_level == 3)
    
    # Determine winner and reason
    if p1_m3_count > p2_m3_count:
        return {
            'winner': 'player1',
            'reason': f'{p1_m3_count} M3 equipment vs {p2_m3_count} M3 equipment'
        }
    elif p2_m3_count > p1_m3_count:
        return {
            'winner': 'player2',
            'reason': f'{p2_m3_count} M3 equipment vs {p1_m3_count} M3 equipment'
        }
    else:
        # Same M3 count, compare by highest M level or total score
        p1_highest = max([mod_level for _, mod_level in p1_details], default=0)
        p2_highest = max([mod_level for _, mod_level in p2_details], default=0)
        
        if p1_highest > p2_highest:
            return {
                'winner': 'player1',
                'reason': f'Highest equipment: M{p1_highest} vs M{p2_highest}'
            }
        elif p2_highest > p1_highest:
            return {
                'winner': 'player2',
                'reason': f'Highest equipment: M{p2_highest} vs M{p1_highest}'
            }
        elif p1_score > p2_score:
            return {
                'winner': 'player1',
                'reason': f'Better overall equipment quality'
            }
        elif p2_score > p1_score:
            return {
                'winner': 'player2',
                'reason': f'Better overall equipment quality'
            }
        else:
            return {
                'winner': 'tie',
                'reason': f'Equal equipment quality ({p1_m3_count} M3s each)'
            }
