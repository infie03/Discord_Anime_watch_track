import logging
from datetime import datetime
import discord
import os

class AnimeLogger:
    def __init__(self, log_channel_id=None):
        self.log_channel_id = log_channel_id
        self.setup_file_logging()
        
    def setup_file_logging(self):
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Setup file logging
        log_file = f'logs/anime_bot_{datetime.now().strftime("%Y%m%d")}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('AnimeBot')

    async def log_action(self, bot, user, action, details=None, error=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_str = f"{user.name}#{user.discriminator} (ID: {user.id})"
        
        if error:
            log_message = f"ERROR - User: {user_str} - Action: {action} - Error: {error}"
            self.logger.error(log_message)
        else:
            log_message = f"User: {user_str} - Action: {action}"
            if details:
                log_message += f" - Details: {details}"
            self.logger.info(log_message)

        # If log channel is set up, send log message to Discord
        if self.log_channel_id:
            try:
                channel = bot.get_channel(self.log_channel_id)
                if channel:
                    embed = discord.Embed(
                        title="Bot Log",
                        timestamp=datetime.now(),
                        color=discord.Color.red() if error else discord.Color.blue()
                    )
                    embed.add_field(name="User", value=user_str, inline=False)
                    embed.add_field(name="Action", value=action, inline=False)
                    if details:
                        embed.add_field(name="Details", value=details, inline=False)
                    if error:
                        embed.add_field(name="Error", value=str(error), inline=False)
                    
                    await channel.send(embed=embed)
            except Exception as e:
                self.logger.error(f"Failed to send log to Discord channel: {str(e)}") 