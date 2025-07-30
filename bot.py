"""
RTanks Online Discord Bot
Core bot functionality with slash commands.
"""

import discord
from discord.ext import commands
import aiohttp
import asyncio
import time
import psutil
import os
from datetime import datetime, timedelta
import logging
import re

from scraper import RTanksScraper
from utils import format_number, format_exact_number, get_rank_emoji, format_duration, compare_equipment_quality
from config import RANK_EMOJIS, PREMIUM_EMOJI, GOLD_BOX_EMOJI, RTANKS_BASE_URL

logger = logging.getLogger(__name__)

class PlayerEquipmentView(discord.ui.View):
    def __init__(self, username: str, user_id: int, player_data: dict, language: str = 'en', expanded: bool = False):
        super().__init__(timeout=None)  # No timeout since we handle expiration manually
        self.username = username
        self.user_id = user_id
        self.player_data = player_data
        self.language = language
        self.expanded = expanded
        self.created_at = datetime.now()
        
        # Add appropriate button based on language and state
        if expanded:
            if language == 'ru':
                self.equipment_button.label = "-"
                self.equipment_button.emoji = None
            else:
                self.equipment_button.label = "-"
                self.equipment_button.emoji = None
        else:
            if language == 'ru':
                self.equipment_button.label = "+"
                self.equipment_button.emoji = None
            else:
                self.equipment_button.label = "+"
                self.equipment_button.emoji = None
    
    def is_expired(self):
        """Check if the button has expired (24 hours)."""
        return datetime.now() - self.created_at > timedelta(days=1)
    
    @discord.ui.button(label="+", style=discord.ButtonStyle.secondary)
    async def equipment_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if button has expired
        if self.is_expired():
            if self.language == 'ru':
                error_msg = "⏰ Кнопка истекла (24 часа). Пожалуйста, используйте команду снова."
            else:
                error_msg = "⏰ Button has expired (24 hours). Please use the command again."
            
            await interaction.response.send_message(error_msg, ephemeral=True)
            return
        
        # Check if the user is authorized
        if interaction.user.id != self.user_id:
            if self.language == 'ru':
                error_msg = "❌ Только пользователь, который использовал команду, может нажать эту кнопку."
            else:
                error_msg = "❌ Only the user who used the command can press this button."
            
            await interaction.response.send_message(error_msg, ephemeral=True)
            return
        
        # Defer the response
        await interaction.response.defer()
        
        try:
            # Get the bot instance
            bot = interaction.client
            
            # Toggle expanded state
            new_expanded = not self.expanded
            
            # Create updated embed based on language and expansion state
            if self.language == 'ru':
                embed = await bot._create_player_embed_russian(self.player_data, expanded=new_expanded)
            else:
                embed = await bot._create_player_embed(self.player_data, expanded=new_expanded)
            
            # Create new view with toggled state
            new_view = PlayerEquipmentView(
                self.username, 
                self.user_id, 
                self.player_data, 
                self.language, 
                expanded=new_expanded
            )
            
            # Update the original message
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=new_view)
            
        except Exception as e:
            logger.error(f"Error processing equipment expansion: {e}")
            
            if self.language == 'ru':
                error_msg = "⚠️ Произошла ошибка при обновлении снаряжения."
            else:
                error_msg = "⚠️ An error occurred while updating equipment display."
            
            await interaction.followup.send(error_msg, ephemeral=True)

class RTanksBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        # Bot statistics
        self.start_time = datetime.now()
        self.commands_processed = 0
        self.scraping_successes = 0
        self.scraping_failures = 0
        self.total_scraping_time = 0.0
        
        # Initialize scraper
        self.scraper = RTanksScraper()
    
    async def setup_hook(self):
        self.loop.create_task(self._update_online_status_task())
        """Setup hook called when bot is starting up."""
        # Register commands with the command tree
        self.tree.command(name="player", description="Get RTanks player statistics")(self.player_command_handler)
        self.tree.command(name="игрок", description="Получить статистику игрока RTanks")(self.player_command_handler_russian)
        self.tree.command(name="botstats", description="Display bot performance statistics")(self.botstats_command_handler)
        self.tree.command(name="compare", description="Compare two RTanks players")(self.compare_command_handler)
        
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot status

    @discord.app_commands.describe(username="RTanks player username to lookup")
    async def player_command_handler(self, interaction: discord.Interaction, username: str):
        """Slash command to get player statistics."""
        await interaction.response.defer()
        
        start_time = time.time()
        self.commands_processed += 1
        
        try:
            # Scrape player data
            player_data = await self.scraper.get_player_data(username.strip())
            
            if not player_data:
                embed = discord.Embed(
                    title="❌ Player Not Found",
                    description=f"Player `{username}` not found,try again.",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                self.scraping_failures += 1
                return
            
            # Create player embed
            embed = await self._create_player_embed(player_data)
            
            # Create equipment view
            view = PlayerEquipmentView(username, interaction.user.id, player_data, 'en')
            
            await interaction.followup.send(embed=embed, view=view)
            
            # Update statistics
            scraping_time = time.time() - start_time
            self.total_scraping_time += scraping_time
            self.scraping_successes += 1
            
        except Exception as e:
            logger.error(f"Error processing player command: {e}")
            
            embed = discord.Embed(
                title="⚠️ Error",
                description="An error occurred while fetching player data. The RTanks website might be temporarily unavailable.",
                color=0xffa500
            )
            await interaction.followup.send(embed=embed)
            self.scraping_failures += 1

    @discord.app_commands.describe(username="Имя пользователя игрока RTanks")
    async def player_command_handler_russian(self, interaction: discord.Interaction, username: str):
        """Russian slash command to get player statistics."""
        await interaction.response.defer()
        
        start_time = time.time()
        self.commands_processed += 1
        
        try:
            # Scrape player data
            player_data = await self.scraper.get_player_data(username.strip())
            
            if not player_data:
                embed = discord.Embed(
                    title="❌ Игрок не найден",
                    description=f"Игрок `{username}` не найден, попробуйте еще раз.",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                self.scraping_failures += 1
                return
            
            # Create Russian player embed
            embed = await self._create_player_embed_russian(player_data)
            
            # Create equipment view with Russian language
            view = PlayerEquipmentView(username, interaction.user.id, player_data, 'ru')
            
            await interaction.followup.send(embed=embed, view=view)
            
            # Update statistics
            scraping_time = time.time() - start_time
            self.total_scraping_time += scraping_time
            self.scraping_successes += 1
            
        except Exception as e:
            logger.error(f"Error processing Russian player command: {e}")
            
            embed = discord.Embed(
                title="⚠️ Ошибка",
                description="Произошла ошибка при получении данных игрока. Веб-сайт RTanks может быть временно недоступен.",
                color=0xffa500
            )
            await interaction.followup.send(embed=embed)
            self.scraping_failures += 1

    @discord.app_commands.describe(
        player1="First RTanks player username",
        player2="Second RTanks player username"
    )
    async def compare_command_handler(self, interaction: discord.Interaction, player1: str, player2: str):
        """Slash command to compare two RTanks players."""
        await interaction.response.defer()
        
        start_time = time.time()
        self.commands_processed += 1
        
        try:
            # Clean usernames
            player1 = player1.strip()
            player2 = player2.strip()
            
            if player1.lower() == player2.lower():
                embed = discord.Embed(
                    title="❌ Invalid Comparison",
                    description="Cannot compare a player with themselves. Please provide two different usernames.",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Fetch data for both players
            logger.info(f"Fetching data for {player1} and {player2}")
            
            # Fetch both players concurrently
            player1_task = self.scraper.get_player_data(player1)
            player2_task = self.scraper.get_player_data(player2)
            
            player1_data, player2_data = await asyncio.gather(player1_task, player2_task, return_exceptions=True)
            
            # Check for errors in data fetching
            if isinstance(player1_data, Exception):
                logger.error(f"Error fetching {player1}: {player1_data}")
                player1_data = None
            if isinstance(player2_data, Exception):
                logger.error(f"Error fetching {player2}: {player2_data}")
                player2_data = None
            
            # Handle cases where one or both players are not found
            if not player1_data and not player2_data:
                embed = discord.Embed(
                    title="❌ Players Not Found",
                    description=f"Could not find data for either `{player1}` or `{player2}`. Please check the usernames and try again.",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                self.scraping_failures += 2
                return
            elif not player1_data:
                embed = discord.Embed(
                    title="❌ Player Not Found",
                    description=f"Could not find data for `{player1}`. Please check the username and try again.",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                self.scraping_failures += 1
                return
            elif not player2_data:
                embed = discord.Embed(
                    title="❌ Player Not Found",
                    description=f"Could not find data for `{player2}`. Please check the username and try again.",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                self.scraping_failures += 1
                return
            
            # Create comparison embed
            embed = await self._create_comparison_embed(player1_data, player2_data)
            await interaction.followup.send(embed=embed)
            
            # Update statistics
            scraping_time = time.time() - start_time
            self.total_scraping_time += scraping_time
            self.scraping_successes += 2
            
        except Exception as e:
            logger.error(f"Error processing compare command: {e}")
            
            embed = discord.Embed(
                title="⚠️ Error",
                description="An error occurred while comparing players. The RTanks website might be temporarily unavailable.",
                color=0xffa500
            )
            await interaction.followup.send(embed=embed)
            self.scraping_failures += 1

    async def botstats_command_handler(self, interaction: discord.Interaction):
        """Slash command to display bot statistics."""
        await interaction.response.defer()
        
        self.commands_processed += 1
        
        # Calculate bot latency
        bot_latency = round(self.latency * 1000, 2)
        
        # Calculate average scraping latency
        avg_scraping_latency = 0
        if self.scraping_successes > 0:
            avg_scraping_latency = round((self.total_scraping_time / self.scraping_successes) * 1000, 2)
        
        # Calculate uptime
        uptime = datetime.now() - self.start_time
        uptime_str = format_duration(uptime.total_seconds())
        
        # Get system stats
        process = psutil.Process(os.getpid())
        memory_usage = round(process.memory_info().rss / 1024 / 1024, 2)  # MB
        cpu_usage = round(process.cpu_percent(interval=1), 1)
        
        # Calculate success rate
        total_scrapes = self.scraping_successes + self.scraping_failures
        success_rate = 0
        if total_scrapes > 0:
            success_rate = round((self.scraping_successes / total_scrapes) * 100, 1)
        
        embed = discord.Embed(
            title="🤖 Bot Statistics",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        # Performance metrics
        embed.add_field(
            name="📡 Latency",
            value=f"**Discord API:** {bot_latency}ms\n**Scraping Avg:** {avg_scraping_latency}ms",
            inline=True
        )
        
        embed.add_field(
            name="⏱️ Uptime",
            value=uptime_str,
            inline=True
        )
        
        embed.add_field(
            name="🌐 Servers",
            value=f"{len(self.guilds)}",
            inline=True
        )
        
        # Command statistics
        embed.add_field(
            name="📊 Commands",
            value=f"**Total Processed:** {format_number(self.commands_processed)}\n**Success Rate:** {success_rate}%",
            inline=True
        )
        
        # Scraping statistics
        embed.add_field(
            name="🔍 Scraping Stats",
            value=f"**Successful:** {format_number(self.scraping_successes)}\n**Failed:** {format_number(self.scraping_failures)}",
            inline=True
        )
        
        # System resources
        embed.add_field(
            name="💻 System Resources",
            value=f"**Memory:** {memory_usage} MB\n**CPU:** {cpu_usage}%",
            inline=True
        )
        
        # Website status
        website_status = await self._check_website_status()
        embed.add_field(
            name="🌍 Website Status",
            value=website_status,
            inline=False
        )
        
        embed.set_footer(text="RTanks Online Bot", icon_url=self.user.display_avatar.url if self.user else None)
        
        await interaction.followup.send(embed=embed)

    async def _create_player_embed(self, player_data, expanded=False):
        """Create a formatted embed for player data."""
        # Create embed with activity status
        activity_status = "Online" if player_data['is_online'] else "Offline"
        # URL encode the username to handle special characters
        import urllib.parse
        encoded_username = urllib.parse.quote(player_data['username'])
        profile_url = f"{RTANKS_BASE_URL}/user/{encoded_username}"
        title_display = player_data['username']
        if player_data.get('clan'):
            title_display = f"{player_data['username']} [{player_data['clan']}]"
            
        embed = discord.Embed(
            title=title_display,
            url=profile_url,
            description=f"**Activity:** {activity_status}",
            color=0x00ff00 if player_data['is_online'] else 0x808080,
            timestamp=datetime.now()
        )
        
        # Player rank and basic info - make rank emoji bigger
        rank_emoji = get_rank_emoji(player_data['rank'], premium=player_data.get('premium', False))
        
        # Extract the emoji ID from the custom Discord emoji and use it as thumbnail
        import re
        emoji_match = re.search(r':(\d+)>', rank_emoji)
        if emoji_match:
            emoji_id = emoji_match.group(1)
            emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.png"
            embed.set_thumbnail(url=emoji_url)
        
        # Rank field with just the rank name, no emoji
        embed.add_field(
            name="Rank",
            value=f"**{player_data['rank']}**",
            inline=True
        )
        
        # Experience - show current/max format like "105613/125000"
        if 'max_experience' in player_data and player_data['max_experience']:
            exp_display = f"{format_exact_number(player_data['experience'])}/{format_exact_number(player_data['max_experience'])}"
        else:
            exp_display = f"{format_exact_number(player_data['experience'])}"
        
        embed.add_field(
            name="Experience",
            value=exp_display,
            inline=True
        )
        
        # Premium status - always show premium emoji
        premium_status = "Yes" if player_data['premium'] else "No"
        embed.add_field(
            name="Premium",
            value=f"{PREMIUM_EMOJI} {premium_status}",
            inline=True
        )
        
        # Combat Stats - remove non-custom emojis
        combat_stats = (
            f"**Kills:** {format_exact_number(player_data['kills'])}\n"
            f"**Deaths:** {format_exact_number(player_data['deaths'])}\n"
            f"**K/D:** {player_data['kd_ratio']}"
        )
        embed.add_field(
            name="Combat Stats",
            value=combat_stats,
            inline=True
        )
        
        # Other Stats - always show gold box emoji
        other_stats = (
            f"{GOLD_BOX_EMOJI} **Gold Boxes:** {player_data['gold_boxes']}\n"
            f"**Group:** {player_data['group']}"
        )
        embed.add_field(
            name="Other Stats",
            value=other_stats,
            inline=True
        )
        
        # Equipment - show basic or full based on expanded state
        if player_data['equipment']:
            equipment_text = ""
            
            if not expanded:
                # Show only actually equipped items
                equipped_turrets = player_data['equipment'].get('equipped_turrets', [])
                equipped_hulls = player_data['equipment'].get('equipped_hulls', [])
                equipped_protections = player_data['equipment'].get('equipped_protections', [])
                
                if equipped_turrets:
                    equipment_text += f"**Turret:** {equipped_turrets[0]}\n"
                
                if equipped_hulls:
                    equipment_text += f"**Hull:** {equipped_hulls[0]}\n"
                
                if equipped_protections:
                    # Show first 3 equipped protections
                    current_paints = equipped_protections[:3]
                    paints_text = ", ".join(current_paints)
                    equipment_text += f"**Paints:** {paints_text}"
                        
                # Show total counts
                total_turrets = len(player_data['equipment'].get('turrets', []))
                total_hulls = len(player_data['equipment'].get('hulls', []))
                total_protections = len(player_data['equipment'].get('protections', []))
                
                if total_turrets > 0 or total_hulls > 0 or total_protections > 0:
                    if equipment_text:
                        equipment_text += "\n\n"

            else:
                # Show all equipment
                if player_data['equipment'].get('turrets'):
                    turrets = ", ".join(player_data['equipment']['turrets'])
                    equipment_text += f"**Turrets:** {turrets}\n"
                
                if player_data['equipment'].get('hulls'):
                    hulls = ", ".join(player_data['equipment']['hulls'])
                    equipment_text += f"**Hulls:** {hulls}\n"
                
                if player_data['equipment'].get('protections'):
                    protections = ", ".join(player_data['equipment']['protections'])
                    equipment_text += f"**Protections:** {protections}"
            
            if equipment_text:
                embed.add_field(
                    name="Equipment",
                    value=equipment_text,
                    inline=False
                )
        
        embed.set_footer(text="Data from ratings.ranked-rtanks.online")
        
        return embed

    async def _create_player_embed_russian(self, player_data, expanded=False):
        """Create a formatted embed for player data in Russian."""
        # Create embed with activity status in Russian
        activity_status = "В сети" if player_data['is_online'] else "Не в сети"
        # URL encode the username to handle special characters
        import urllib.parse
        encoded_username = urllib.parse.quote(player_data['username'])
        profile_url = f"{RTANKS_BASE_URL}/user/{encoded_username}"
        title_display = player_data['username']
        if player_data.get('clan'):
            title_display = f"{player_data['username']} [{player_data['clan']}]"
            
        embed = discord.Embed(
            title=title_display,
            url=profile_url,
            description=f"**Активность:** {activity_status}",
            color=0x00ff00 if player_data['is_online'] else 0x808080,
            timestamp=datetime.now()
        )
        
        # Player rank and basic info - make rank emoji bigger
        rank_emoji = get_rank_emoji(player_data['rank'], premium=player_data.get('premium', False))
        
        # Extract the emoji ID from the custom Discord emoji and use it as thumbnail
        import re
        emoji_match = re.search(r':(\d+)>', rank_emoji)
        if emoji_match:
            emoji_id = emoji_match.group(1)
            emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.png"
            embed.set_thumbnail(url=emoji_url)
        
        # Rank field with Russian translation
        rank_russian = self._translate_rank_to_russian(player_data['rank'])
        embed.add_field(
            name="Звание",
            value=f"**{rank_russian}**",
            inline=True
        )
        
        # Experience - show current/max format like "105613/125000"
        if 'max_experience' in player_data and player_data['max_experience']:
            exp_display = f"{format_exact_number(player_data['experience'])}/{format_exact_number(player_data['max_experience'])}"
        else:
            exp_display = f"{format_exact_number(player_data['experience'])}"
        
        embed.add_field(
            name="Опыт",
            value=exp_display,
            inline=True
        )
        
        # Premium status - always show premium emoji
        premium_status = "Да" if player_data['premium'] else "Нет"
        embed.add_field(
            name="Премиум",
            value=f"{PREMIUM_EMOJI} {premium_status}",
            inline=True
        )
        
        # Combat Stats in Russian
        embed.add_field(
            name="Убийства",
            value=format_exact_number(player_data['kills']),
            inline=True
        )
        
        embed.add_field(
            name="Смерти", 
            value=format_exact_number(player_data['deaths']),
            inline=True
        )
        
        embed.add_field(
            name="У/С",
            value=player_data['kd_ratio'],
            inline=True
        )
        
        # Gold boxes - always show gold box emoji
        embed.add_field(
            name=f"{GOLD_BOX_EMOJI} Золотые ящики",
            value=format_exact_number(player_data['gold_boxes']),
            inline=True
        )
        
        # Group/Clan in Russian - translate all possible group types
        group_text = self._translate_group_to_russian(player_data.get('group', 'Нет группы'))
        embed.add_field(
            name="Группа",
            value=group_text,
            inline=True
        )
        
        # Equipment section in Russian - show basic or full based on expanded state
        if player_data.get('equipment'):
            equipment_text = ""
            
            if not expanded:
                # Show only actually equipped items in Russian
                equipped_turrets = player_data['equipment'].get('equipped_turrets', [])
                equipped_hulls = player_data['equipment'].get('equipped_hulls', [])
                equipped_protections = player_data['equipment'].get('equipped_protections', [])
                
                if equipped_turrets:
                    russian_turret = self._translate_equipment_to_russian(equipped_turrets[0])
                    equipment_text += f"**Башня:** {russian_turret}\n"
                
                if equipped_hulls:
                    russian_hull = self._translate_equipment_to_russian(equipped_hulls[0])
                    equipment_text += f"**Корпус:** {russian_hull}\n"
                
                if equipped_protections:
                    current_paints = equipped_protections[:3]
                    russian_paints = [self._translate_equipment_to_russian(paint) for paint in current_paints]
                    paints_text = ", ".join(russian_paints)
                    equipment_text += f"**Краски:** {paints_text}"
                        
                # Show total counts in Russian
                total_turrets = len(player_data['equipment'].get('turrets', []))
                total_hulls = len(player_data['equipment'].get('hulls', []))
                total_protections = len(player_data['equipment'].get('protections', []))
                
                if total_turrets > 0 or total_hulls > 0 or total_protections > 0:
                    if equipment_text:
                        equipment_text += "\n\n"

            else:
                # Show all equipment in Russian
                if player_data['equipment'].get('turrets'):
                    russian_turrets = [self._translate_equipment_to_russian(turret) for turret in player_data['equipment']['turrets']]
                    turrets = ", ".join(russian_turrets)
                    equipment_text += f"**Башни:** {turrets}\n"
                
                if player_data['equipment'].get('hulls'):
                    russian_hulls = [self._translate_equipment_to_russian(hull) for hull in player_data['equipment']['hulls']]
                    hulls = ", ".join(russian_hulls)
                    equipment_text += f"**Корпуса:** {hulls}\n"
                
                if player_data['equipment'].get('protections'):
                    russian_protections = [self._translate_equipment_to_russian(protection) for protection in player_data['equipment']['protections']]
                    protections = ", ".join(russian_protections)
                    equipment_text += f"**Защита:** {protections}"
            
            if equipment_text:
                embed.add_field(
                    name="Снаряжение",
                    value=equipment_text,
                    inline=False
                )
        
        embed.set_footer(text="Data from ratings.ranked-rtanks.online")
        
        return embed
    
    def _translate_rank_to_russian(self, rank):
        """Translate English rank names to Russian."""
        rank_translations = {
            # Basic ranks
            'Recruit': 'Рекрут',
            'Private': 'Рядовой',
            'Gefreiter': 'Ефрейтор', 
            'Corporal': 'Капрал',
            'Master Corporal': 'Старший капрал',
            'Sergeant': 'Сержант',
            'Staff Sergeant': 'Штаб-сержант',
            'Master Sergeant': 'Старший сержант',
            'First Sergeant': 'Старшина',
            'Sergeant Major': 'Старшина',
            
            # Warrant Officers (all levels)
            'Warrant Officer': 'Прапорщик',
            'Warrant Officer 1': 'Прапорщик 1',
            'Warrant Officer 2': 'Прапорщик 2', 
            'Warrant Officer 3': 'Прапорщик 3',
            'Warrant Officer 4': 'Прапорщик 4',
            'Warrant Officer 5': 'Прапорщик 5',
            'Master Warrant Officer': 'Старший прапорщик',
            
            # Officer ranks
            'Third Lieutenant': 'Младший лейтенант',
            'Second Lieutenant': 'Лейтенант',
            'First Lieutenant': 'Старший лейтенант',
            'Lieutenant': 'Лейтенант',
            'Captain': 'Капитан',
            'Major': 'Майор',
            'Lieutenant Colonel': 'Подполковник',
            'Colonel': 'Полковник',
            
            # General ranks
            'Brigadier': 'Бригадир',
            'Brigadier General': 'Генерал-бригадир',
            'Major General': 'Генерал-майор',
            'Lieutenant General': 'Генерал-лейтенант',
            'General': 'Генерал',
            'General of the Army': 'Генерал армии',
            
            # Marshal ranks
            'Marshal': 'Маршал',
            'Field Marshal': 'Фельдмаршал',
            'Air Marshal': 'Маршал авиации',
            'Fleet Admiral': 'Адмирал флота',
            
            # Special ranks
            'Commander': 'Командир',
            'Commander in Chief': 'Главнокомандующий',
            'Generalissimo': 'Генералиссимус',
            'Supreme Commander': 'Верховный командующий'
        }
        
        # Handle Legend ranks
        if rank.startswith('Legend'):
            if ' ' in rank:
                level = rank.split(' ')[1]
                return f"Легенда {level}"
            else:
                return "Легенда"
        
        return rank_translations.get(rank, rank)

    def _translate_equipment_to_russian(self, equipment: str) -> str:
        """Translate equipment names to Russian"""
        equipment_translations = {
            # Turrets
            'Smoky M0': 'Смоки М0',
            'Smoky M1': 'Смоки М1',
            'Smoky M2': 'Смоки М2',
            'Smoky M3': 'Смоки М3',
            'Rail M0': 'Рельса М0',
            'Rail M1': 'Рельса М1',
            'Rail M2': 'Рельса М2',
            'Rail M3': 'Рельса М3',
            'Ricochet M0': 'Рикошет М0',
            'Ricochet M1': 'Рикошет М1',
            'Ricochet M2': 'Рикошет М2',
            'Ricochet M3': 'Рикошет М3',
            'Isida M0': 'Изида М0',
            'Isida M1': 'Изида М1',
            'Isida M2': 'Изида М2',
            'Isida M3': 'Изида М3',
            'Freeze M0': 'Фриз М0',
            'Freeze M1': 'Фриз М1',
            'Freeze M2': 'Фриз М2',
            'Freeze M3': 'Фриз М3',
            'Flamethrower M0': 'Огнемёт М0',
            'Flamethrower M1': 'Огнемёт М1',
            'Flamethrower M2': 'Огнемёт М2',
            'Flamethrower M3': 'Огнемёт М3',
            'Thunder M0': 'Гром М0',
            'Thunder M1': 'Гром М1',
            'Thunder M2': 'Гром М2',
            'Thunder M3': 'Гром М3',
            'Hammer M0': 'Молот М0',
            'Hammer M1': 'Молот М1',
            'Hammer M2': 'Молот М2',
            'Hammer M3': 'Молот М3',
            'Vulcan M0': 'Вулкан М0',
            'Vulcan M1': 'Вулкан М1',
            'Vulcan M2': 'Вулкан М2',
            'Vulcan M3': 'Вулкан М3',
            'Twins M0': 'Близнецы М0',
            'Twins M1': 'Близнецы М1',
            'Twins M2': 'Близнецы М2',
            'Twins M3': 'Близнецы М3',
            'Shaft M0': 'Шафт М0',
            'Shaft M1': 'Шафт М1',
            'Shaft M2': 'Шафт М2',
            'Shaft M3': 'Шафт М3',
            'Striker M0': 'Страйкер М0',
            'Striker M1': 'Страйкер М1',
            'Striker M2': 'Страйкер М2',
            'Striker M3': 'Страйкер М3',
            
            # Hulls
            'Hunter M0': 'Охотник М0',
            'Hunter M1': 'Охотник М1',
            'Hunter M2': 'Охотник М2',
            'Hunter M3': 'Охотник М3',
            'Mammoth M0': 'Мамонт М0',
            'Mammoth M1': 'Мамонт М1',
            'Mammoth M2': 'Мамонт М2',
            'Mammoth M3': 'Мамонт М3',
            'Titan M0': 'Титан М0',
            'Titan M1': 'Титан М1',
            'Titan M2': 'Титан М2',
            'Titan M3': 'Титан М3',
            'Wasp M0': 'Оса М0',
            'Wasp M1': 'Оса М1',
            'Wasp M2': 'Оса М2',
            'Wasp M3': 'Оса М3',
            'Viking M0': 'Викинг М0',
            'Viking M1': 'Викинг М1',
            'Viking M2': 'Викинг М2',
            'Viking M3': 'Викинг М3',
            'Hornet M0': 'Хорнет М0',
            'Hornet M1': 'Хорнет М1',
            'Hornet M2': 'Хорнет М2',
            'Hornet M3': 'Хорнет М3',
            'Dictator M0': 'Диктатор М0',
            'Dictator M1': 'Диктатор М1',
            'Dictator M2': 'Диктатор М2',
            'Dictator M3': 'Диктатор М3',
            
            # Protections
            'Smoky Protection M0': 'Защита от Смоки М0',
            'Smoky Protection M1': 'Защита от Смоки М1',
            'Smoky Protection M2': 'Защита от Смоки М2',
            'Smoky Protection M3': 'Защита от Смоки М3',
            'Rail Protection M0': 'Защита от Рельса М0',
            'Rail Protection M1': 'Защита от Рельса М1',
            'Rail Protection M2': 'Защита от Рельса М2',
            'Rail Protection M3': 'Защита от Рельса М3',
            'Ricochet Protection M0': 'Защита от Рикошета М0',
            'Ricochet Protection M1': 'Защита от Рикошета М1',
            'Ricochet Protection M2': 'Защита от Рикошета М2',
            'Ricochet Protection M3': 'Защита от Рикошета М3',
            'Isida Protection M0': 'Защита от Изиды М0',
            'Isida Protection M1': 'Защита от Изиды М1',
            'Isida Protection M2': 'Защита от Изиды М2',
            'Isida Protection M3': 'Защита от Изиды М3',
            'Freeze Protection M0': 'Защита от Фриза М0',
            'Freeze Protection M1': 'Защита от Фриза М1',
            'Freeze Protection M2': 'Защита от Фриза М2',
            'Freeze Protection M3': 'Защита от Фриза М3',
            'Flamethrower Protection M0': 'Защита от Огнемета М0',
            'Flamethrower Protection M1': 'Защита от Огнемета М1',
            'Flamethrower Protection M2': 'Защита от Огнемета М2',
            'Flamethrower Protection M3': 'Защита от Огнемета М3',
            'Thunder Protection M0': 'Защита от Грома М0',
            'Thunder Protection M1': 'Защита от Грома М1',
            'Thunder Protection M2': 'Защита от Грома М2',
            'Thunder Protection M3': 'Защита от Грома М3',
            'Hammer Protection M0': 'Защита от Молота М0',
            'Hammer Protection M1': 'Защита от Молота М1',
            'Hammer Protection M2': 'Защита от Молота М2',
            'Hammer Protection M3': 'Защита от Молота М3',
            'Vulcan Protection M0': 'Защита от Вулкана М0',
            'Vulcan Protection M1': 'Защита от Вулкана М1',
            'Vulcan Protection M2': 'Защита от Вулкана М2',
            'Vulcan Protection M3': 'Защита от Вулкана М3',
            'Twins Protection M0': 'Защита от Твинса М0',
            'Twins Protection M1': 'Защита от Твинса М1',
            'Twins Protection M2': 'Защита от Твинса М2',
            'Twins Protection M3': 'Защита от Твинса М3',
            'Shaft Protection M0': 'Защита от Шафта М0',
            'Shaft Protection M1': 'Защита от Шафта М1',
            'Shaft Protection M2': 'Защита от Шафта М2',
            'Shaft Protection M3': 'Защита от Шафта М3',
            'Striker Protection M0': 'Защита от Страйкера М0',
            'Striker Protection M1': 'Защита от Страйкера М1',
            'Striker Protection M2': 'Защита от Страйкера М2',
            'Striker Protection M3': 'Защита от Страйкера М3',
            
            # Resistances (actual website format)
            'Badger M0': 'Барсук М0',
            'Badger M1': 'Барсук М1', 
            'Badger M2': 'Барсук М2',
            'Badger M3': 'Барсук М3',
            'Spider M0': 'Паук М0',
            'Spider M1': 'Паук М1',
            'Spider M2': 'Паук М2', 
            'Spider M3': 'Паук М3',
            'Falcon M0': 'Сокол М0',
            'Falcon M1': 'Сокол М1',
            'Falcon M2': 'Сокол М2',
            'Falcon M3': 'Сокол М3',
            'Bear M0': 'Медведь М0',
            'Bear M1': 'Медведь М1',
            'Bear M2': 'Медведь М2',
            'Bear M3': 'Медведь М3',
            'Wolf M0': 'Волк М0',
            'Wolf M1': 'Волк М1',
            'Wolf M2': 'Волк М2',
            'Wolf M3': 'Волк М3',
            'Eagle M0': 'Орёл М0',
            'Eagle M1': 'Орёл М1',
            'Eagle M2': 'Орёл М2',
            'Eagle M3': 'Орёл М3',
            'Tiger M0': 'Тигр М0',
            'Tiger M1': 'Тигр М1',
            'Tiger M2': 'Тигр М2',
            'Tiger M3': 'Тигр М3',
            'Shark M0': 'Акула М0',
            'Shark M1': 'Акула М1',
            'Shark M2': 'Акула М2',
            'Shark M3': 'Акула М3',
            'Lion M0': 'Лев М0',
            'Lion M1': 'Лев М1',
            'Lion M2': 'Лев М2',
            'Lion M3': 'Лев М3',
            'Snake M0': 'Змея М0',
            'Snake M1': 'Змея М1',
            'Snake M2': 'Змея М2',
            'Snake M3': 'Змея М3',
            'Hawk M0': 'Ястреб М0',
            'Hawk M1': 'Ястреб М1',
            'Hawk M2': 'Ястреб М2',
            'Hawk M3': 'Ястреб М3',
            'Panther M0': 'Пантера М0',
            'Panther M1': 'Пантера М1',
            'Panther M2': 'Пантера М2',
            'Panther M3': 'Пантера М3',
            'Dolphin M0': 'Дельфин М0',
            'Dolphin M1': 'Дельфин М1',
            'Dolphin M2': 'Дельфин М2',
            'Dolphin M3': 'Дельфин М3',
            'Ocelot M0': 'Оцелот М0',
            'Ocelot M1': 'Оцелот М1',
            'Ocelot M2': 'Оцелот М2',
            'Ocelot M3': 'Оцелот М3',
            'Leopard M0': 'Леопард М0',
            'Leopard M1': 'Леопард М1',
            'Leopard M2': 'Леопард М2',
            'Leopard M3': 'Леопард М3',
            'Rhino M0': 'Носорог М0',
            'Rhino M1': 'Носорог М1',
            'Rhino M2': 'Носорог М2',
            'Rhino M3': 'Носорог М3',
            'Gorilla M0': 'Горилла М0',
            'Gorilla M1': 'Горилла М1',
            'Gorilla M2': 'Горилла М2',
            'Gorilla M3': 'Горилла М3',
            'Cheetah M0': 'Гепард М0',
            'Cheetah M1': 'Гепард М1',
            'Cheetah M2': 'Гепард М2',
            'Cheetah M3': 'Гепард М3'
        }
        return equipment_translations.get(equipment, equipment)

    def _translate_group_to_russian(self, group: str) -> str:
        """Translate group names to Russian for any player"""
        if not group or group in ['Unknown', 'No Group', None]:
            return 'Нет группы'
        
        group_translations = {
            'Player': 'Игрок',
            'Premium': 'Премиум',
            'Moderator': 'Модератор',
            'Administrator': 'Администратор',
            'Developer': 'Разработчик',
            'Tester': 'Тестер',
            'VIP': 'ВИП',
            'Streamer': 'Стример',
            'Content Creator': 'Создатель контента',
            'Beta Tester': 'Бета-тестер',
            'Volunteer': 'Волонтёр',
            'Helper': 'Помощник',
            'Supporter': 'Поддержка',
            'Veteran': 'Ветеран',
            'Elite': 'Элита'
        }
        return group_translations.get(group, group)

    async def _create_comparison_embed(self, player1_data, player2_data):
        """Create a formatted embed for player comparison."""
        p1_name = player1_data['username']
        p2_name = player2_data['username']
        
        embed = discord.Embed(
            title="Player Comparison",
            description=f"**{p1_name}** vs **{p2_name}**",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        # Experience comparison
        p1_exp = player1_data.get('experience', 0)
        p2_exp = player2_data.get('experience', 0)
        
        if p1_exp > p2_exp:
            exp_winner = f"**{p1_name}** ({format_exact_number(p1_exp)})"
            exp_loser = f"{p2_name} ({format_exact_number(p2_exp)})"
        elif p2_exp > p1_exp:
            exp_winner = f"**{p2_name}** ({format_exact_number(p2_exp)})"
            exp_loser = f"{p1_name} ({format_exact_number(p1_exp)})"
        else:
            exp_winner = f"**Tie** ({format_exact_number(p1_exp)})"
            exp_loser = ""
        
        embed.add_field(
            name="Experience",
            value=f"{exp_winner}\n{exp_loser}".strip(),
            inline=True
        )
        
        # K/D ratio comparison
        p1_kd = float(player1_data.get('kd_ratio', '0.00'))
        p2_kd = float(player2_data.get('kd_ratio', '0.00'))
        
        if p1_kd > p2_kd:
            kd_winner = f"**{p1_name}** ({player1_data['kd_ratio']})"
            kd_loser = f"{p2_name} ({player2_data['kd_ratio']})"
        elif p2_kd > p1_kd:
            kd_winner = f"**{p2_name}** ({player2_data['kd_ratio']})"
            kd_loser = f"{p1_name} ({player1_data['kd_ratio']})"
        else:
            kd_winner = f"**Tie** ({player1_data['kd_ratio']})"
            kd_loser = ""
        
        embed.add_field(
            name="K/D Ratio",
            value=f"{kd_winner}\n{kd_loser}".strip(),
            inline=True
        )
        
        # Gold boxes comparison
        p1_gold = player1_data.get('gold_boxes', 0)
        p2_gold = player2_data.get('gold_boxes', 0)
        
        if p1_gold > p2_gold:
            gold_winner = f"**{p1_name}** ({format_exact_number(p1_gold)})"
            gold_loser = f"{p2_name} ({format_exact_number(p2_gold)})"
        elif p2_gold > p1_gold:
            gold_winner = f"**{p2_name}** ({format_exact_number(p2_gold)})"
            gold_loser = f"{p1_name} ({format_exact_number(p1_gold)})"
        else:
            gold_winner = f"**Tie** ({format_exact_number(p1_gold)})"
            gold_loser = ""
        
        embed.add_field(
            name=f"{GOLD_BOX_EMOJI} Gold Boxes",
            value=f"{gold_winner}\n{gold_loser}".strip(),
            inline=True
        )
        

        
        # Add player details section
        p1_details = (
            f"**{p1_name}**\n"
            f"Rank: {player1_data['rank']}\n"
            f"Kills: {format_exact_number(player1_data.get('kills', 0))}\n"
            f"Deaths: {format_exact_number(player1_data.get('deaths', 0))}"
        )
        
        p2_details = (
            f"**{p2_name}**\n"
            f"Rank: {player2_data['rank']}\n"
            f"Kills: {format_exact_number(player2_data.get('kills', 0))}\n"
            f"Deaths: {format_exact_number(player2_data.get('deaths', 0))}"
        )
        
        embed.add_field(
            name="Player 1",
            value=p1_details,
            inline=True
        )
        
        embed.add_field(
            name="Player 2",
            value=p2_details,
            inline=True
        )
        
        # Add empty field for spacing
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        
        embed.set_footer(text="Data from ratings.ranked-rtanks.online")
        
        return embed

    async def _check_website_status(self):
        """Check if the RTanks website is accessible."""
        try:
            start_time = time.time()
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get('https://ratings.ranked-rtanks.online/') as response:
                    response_time = round((time.time() - start_time) * 1000, 2)
                    if response.status == 200:
                        return f"🟢 Online ({response_time}ms)"
                    else:
                        return f"🟡 Partial ({response.status})"
        except Exception:
            return "🔴 Offline"

    async def on_command_error(self, ctx, error):
        """Global error handler."""
        logger.error(f"Command error: {error}")
        
    
    async def _update_online_status_task(self):
        """Background task to update bot status with number of online players."""
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                count = await self.scraper.get_online_players_count()
                activity = discord.Activity(type=discord.ActivityType.watching, name=f"{count} players online")
                await self.change_presence(activity=activity)
            except Exception as e:
                logger.warning(f"Failed to update online player count: {e}")
            await asyncio.sleep(30)

    async def close(self):
        """Clean up when bot is closing."""
        await self.scraper.close()
        await super().close()
