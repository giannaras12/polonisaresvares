#!/usr/bin/env python3
"""
RTanks Online Discord Bot
Main entry point for the Discord bot application.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
import threading
from keepalive import run

from bot import RTanksBot
import patched_rank_emoji  # this will patch get_rank_emoji for the bot


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main function to start the bot."""
    # Get Discord token from environment
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables!")
        # Request token from user if not found in environment
        token = input("Please enter your Discord bot token: ").strip()
        if not token:
            logger.error("No token provided. Exiting.")
            return
    
    # Create and run the bot
    bot = RTanksBot()
    
    try:
        logger.info("Starting RTanks Discord Bot...")
        await asyncio.sleep(5)  # Add small delay to reduce chance of rate-limit
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot encountered an error: {e}")
    finally:
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    try:
        threading.Thread(target=run).start()
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
