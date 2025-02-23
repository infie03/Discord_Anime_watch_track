import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
from datetime import datetime
from main import Anime, AnimeWatchList
from logger import AnimeLogger
from dotenv import load_dotenv

# Create bot instance
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Dictionary to store watchlists for different users
user_watchlists = {}

# Initialize logger with your log channel ID
LOG_CHANNEL_ID = None  # Replace with your log channel ID
logger = AnimeLogger(LOG_CHANNEL_ID)

load_dotenv()

# Update the WATERMARK constant at the top of the file
WATERMARK = "🎌 Made by INFIE_03 🎌"

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    try:
        # Set status
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="Made by INFIE_03"
            )
        )
        
        # Force sync all commands
        await bot.tree.sync()
        print("Commands synced!")
        await logger.log_action(bot, bot.user, "Bot Started", "Commands synced")
    except Exception as e:
        await logger.log_action(bot, bot.user, "Bot Start Failed", error=str(e))

def get_user_watchlist(user_id):
    if user_id not in user_watchlists:
        # Create a data directory if it doesn't exist
        data_dir = 'data'
        os.makedirs(data_dir, exist_ok=True)
        # Store user watchlists in the data directory
        file_path = os.path.join(data_dir, f'anime_list_{user_id}.json')
        user_watchlists[user_id] = AnimeWatchList(file_path)
    return user_watchlists[user_id]

@bot.tree.command(name="add_anime", description="Add a new anime to your watchlist")
async def add_anime(interaction: discord.Interaction, 
                   title: str, 
                   status: str, 
                   preference: str, 
                   total_episodes: int, 
                   genre: str = "Unknown", 
                   source_link: str = None):
    try:
        # Validate inputs
        if not title:
            await interaction.response.send_message("Title cannot be empty!")
            await logger.log_action(bot, interaction.user, "Add Anime Failed", "Empty title")
            return

        valid_statuses = ['Completed', 'To Watch', 'Watching']
        status = status.capitalize()
        if status not in valid_statuses:
            await interaction.response.send_message(f"Invalid status! Must be one of: {', '.join(valid_statuses)}")
            return

        valid_preferences = ['High', 'Medium', 'Low']
        preference = preference.capitalize()
        if preference not in valid_preferences:
            await interaction.response.send_message(f"Invalid preference! Must be one of: {', '.join(valid_preferences)}")
            return

        if total_episodes <= 0:
            await interaction.response.send_message("Total episodes must be positive!")
            return

        # Add anime to user's watchlist
        watch_list = get_user_watchlist(interaction.user.id)
        anime = Anime(title, status, preference, genre, 0, total_episodes, source_link=source_link)
        watch_list.add_anime(anime)
        
        await interaction.response.send_message(f"Added {title} to your list!")
        await logger.log_action(bot, interaction.user, "Add Anime", f"Title: {title}, Status: {status}, Episodes: {total_episodes}")
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}")
        await logger.log_action(bot, interaction.user, "Add Anime Failed", error=str(e))

@bot.tree.command(name="list_anime", description="List all anime in your watchlist")
async def list_anime(interaction: discord.Interaction):
    try:
        watch_list = get_user_watchlist(interaction.user.id)
        if not watch_list.anime_list:
            await interaction.response.send_message("Your watchlist is empty!")
            await logger.log_action(bot, interaction.user, "List Anime", "Empty watchlist")
            return

        embed = discord.Embed(title="Your Anime Watchlist", color=discord.Color.blue())
        
        for i, anime in enumerate(watch_list.anime_list):
            progress = f"[{anime.episodes_watched}/{anime.total_episodes}]" if anime.status == 'Watching' else ""
            favorite = "⭐ " if anime.favorite else ""
            embed.add_field(
                name=f"{i}. {favorite}{anime.title}",
                value=f"Status: {anime.status}\nPriority: {anime.preference}\nGenre: {anime.genre} {progress}",
                inline=False
            )
        
        # Add watermark
        embed.set_footer(text=WATERMARK)
        embed.timestamp = datetime.now()

        await interaction.response.send_message(embed=embed)
        await logger.log_action(bot, interaction.user, "List Anime", f"Listed {len(watch_list.anime_list)} anime")
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}")
        await logger.log_action(bot, interaction.user, "List Anime Failed", error=str(e))

@bot.tree.command(name="update_progress", description="Update the watched episodes for an anime")
async def update_progress(interaction: discord.Interaction, index: int, episodes: int):
    try:
        watch_list = get_user_watchlist(interaction.user.id)
        if 0 <= index < len(watch_list.anime_list):
            if episodes >= 0:
                watch_list.update_progress(index, episodes)
                await interaction.response.send_message("Progress updated successfully!")
            else:
                await interaction.response.send_message("Episodes cannot be negative!")
        else:
            await interaction.response.send_message("Invalid index!")
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}")

@bot.tree.command(name="random_anime", description="Get a random anime suggestion from your watchlist")
async def random_anime(interaction: discord.Interaction):
    watch_list = get_user_watchlist(interaction.user.id)
    anime = watch_list.pick_random_anime()
    
    if anime:
        embed = discord.Embed(title="Random Anime Suggestion", color=discord.Color.green())
        embed.add_field(name="Why not watch:", value=str(anime), inline=False)
        embed.set_footer(text=WATERMARK)  # Add watermark
        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("No unwatched anime in your list!")

@bot.tree.command(name="search_anime", description="Search for anime in your watchlist")
async def search_anime(interaction: discord.Interaction, keyword: str):
    watch_list = get_user_watchlist(interaction.user.id)
    results = watch_list.search_anime(keyword)
    
    if results:
        embed = discord.Embed(title=f"Search Results for '{keyword}'", color=discord.Color.blue())
        for i, anime in enumerate(results):
            embed.add_field(name=f"{i}.", value=str(anime), inline=False)
        embed.set_footer(text=WATERMARK)  # Add watermark
        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("No matches found!")

@bot.tree.command(name="view_logs", description="View recent bot logs (Admin only)")
async def view_logs(interaction: discord.Interaction, lines: int = 10):
    try:
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to view logs!", ephemeral=True)
            return

        # Read recent logs
        log_file = f'logs/anime_bot_{datetime.now().strftime("%Y%m%d")}.log'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.readlines()
                recent_logs = logs[-lines:] if lines < len(logs) else logs

            embed = discord.Embed(title="Recent Bot Logs", color=discord.Color.blue())
            log_content = ''.join(recent_logs)
            
            # Split long logs into multiple fields if needed
            while log_content:
                if len(log_content) <= 1024:
                    embed.add_field(name="Logs", value=f"```{log_content}```", inline=False)
                    break
                split_point = log_content[:1024].rindex('\n')
                embed.add_field(name="Logs", value=f"```{log_content[:split_point]}```", inline=False)
                log_content = log_content[split_point+1:]
            
            embed.set_footer(text=WATERMARK)  # Add watermark
            embed.timestamp = datetime.now()
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("No logs found for today.")
    except Exception as e:
        await interaction.response.send_message(f"Error retrieving logs: {str(e)}")
        await logger.log_action(bot, interaction.user, "View Logs Failed", error=str(e))

@bot.tree.command(name="help", description="Show all available commands")
async def help_command(interaction: discord.Interaction):
    """Shows the help menu with all available commands"""
    embed = discord.Embed(
        title="📖 Anime Watch List Bot Commands",
        description="Here are all the available commands:",
        color=discord.Color.blue()
    )

    # Slash Commands section
    slash_commands = {
        "/add_anime": "Add new anime with title, status, preference, episodes",
        "/list_anime": "Show your anime list",
        "/update_progress": "Update episodes watched",
        "/random_anime": "Get a random suggestion",
        "/search_anime": "Search in your list",
        "/help": "Show this help message"
    }

    for cmd, desc in slash_commands.items():
        embed.add_field(name=cmd, value=desc, inline=False)

    # Add Valid Values section
    embed.add_field(
        name="📊 Valid Values",
        value=(
            "**Status:** Completed, To Watch, Watching\n"
            "**Preference:** High, Medium, Low"
        ),
        inline=False
    )

    embed.set_footer(text=WATERMARK)
    embed.timestamp = datetime.now()

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="sync", description="Sync bot commands")
@app_commands.default_permissions(administrator=True)
async def sync_slash(interaction: discord.Interaction):
    try:
        await bot.tree.sync()
        await interaction.response.send_message("Commands synced!")
    except Exception as e:
        await interaction.response.send_message(f"Error: {str(e)}")

# Add prefix commands
@bot.command(name="add")
async def add(ctx, *, args=None):
    if not args:
        await ctx.send("Please provide anime details in the format: !add title | status | preference | episodes | genre | source_link")
        return
    
    try:
        # Split arguments by |
        parts = [part.strip() for part in args.split('|')]
        if len(parts) < 4:
            await ctx.send("Not enough information provided. Format: !add title | status | preference | episodes | genre | source_link")
            return

        title = parts[0]
        status = parts[1]
        preference = parts[2]
        total_episodes = int(parts[3])
        genre = parts[4] if len(parts) > 4 else "Unknown"
        source_link = parts[5] if len(parts) > 5 else None

        # Validate inputs
        if not title:
            await ctx.send("Title cannot be empty!")
            return

        valid_statuses = ['Completed', 'To Watch', 'Watching']
        status = status.capitalize()
        if status not in valid_statuses:
            await ctx.send(f"Invalid status! Must be one of: {', '.join(valid_statuses)}")
            return

        valid_preferences = ['High', 'Medium', 'Low']
        preference = preference.capitalize()
        if preference not in valid_preferences:
            await ctx.send(f"Invalid preference! Must be one of: {', '.join(valid_preferences)}")
            return

        if total_episodes <= 0:
            await ctx.send("Total episodes must be positive!")
            return

        # Add anime to user's watchlist
        watch_list = get_user_watchlist(ctx.author.id)
        anime = Anime(title, status, preference, genre, 0, total_episodes, source_link=source_link)
        watch_list.add_anime(anime)
        
        await ctx.send(f"Added {title} to your list!")
        await logger.log_action(bot, ctx.author, "Add Anime", f"Title: {title}, Status: {status}, Episodes: {total_episodes}")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
        await logger.log_action(bot, ctx.author, "Add Anime Failed", error=str(e))

@bot.command(name="list")
async def list_cmd(ctx):
    try:
        watch_list = get_user_watchlist(ctx.author.id)
        if not watch_list.anime_list:
            await ctx.send("Your watchlist is empty!")
            await logger.log_action(bot, ctx.author, "List Anime", "Empty watchlist")
            return

        embed = discord.Embed(title="Your Anime Watchlist", color=discord.Color.blue())
        
        for i, anime in enumerate(watch_list.anime_list):
            progress = f"[{anime.episodes_watched}/{anime.total_episodes}]" if anime.status == 'Watching' else ""
            favorite = "⭐ " if anime.favorite else ""
            embed.add_field(
                name=f"{i}. {favorite}{anime.title}",
                value=f"Status: {anime.status}\nPriority: {anime.preference}\nGenre: {anime.genre} {progress}",
                inline=False
            )
        
        embed.set_footer(text=WATERMARK)  # Add watermark
        embed.timestamp = datetime.now()
        await ctx.send(embed=embed)
        await logger.log_action(bot, ctx.author, "List Anime", f"Listed {len(watch_list.anime_list)} anime")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
        await logger.log_action(bot, ctx.author, "List Anime Failed", error=str(e))

@bot.command(name="progress")
async def progress(ctx, index: int, episodes: int):
    try:
        watch_list = get_user_watchlist(ctx.author.id)
        if 0 <= index < len(watch_list.anime_list):
            if episodes >= 0:
                watch_list.update_progress(index, episodes)
                await ctx.send("Progress updated successfully!")
            else:
                await ctx.send("Episodes cannot be negative!")
        else:
            await ctx.send("Invalid index!")
    except ValueError:
        await ctx.send("Please provide valid numbers for index and episodes!")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

@bot.command(name="random")
async def random_cmd(ctx):
    watch_list = get_user_watchlist(ctx.author.id)
    anime = watch_list.pick_random_anime()
    
    if anime:
        embed = discord.Embed(title="Random Anime Suggestion", color=discord.Color.green())
        embed.add_field(name="Why not watch:", value=str(anime), inline=False)
        embed.set_footer(text=WATERMARK)  # Add watermark
        embed.timestamp = datetime.now()
        await ctx.send(embed=embed)
    else:
        await ctx.send("No unwatched anime in your list!")

@bot.command(name="search")
async def search_cmd(ctx, *, keyword: str):
    watch_list = get_user_watchlist(ctx.author.id)
    results = watch_list.search_anime(keyword)
    
    if results:
        embed = discord.Embed(title=f"Search Results for '{keyword}'", color=discord.Color.blue())
        for i, anime in enumerate(results):
            embed.add_field(name=f"{i}.", value=str(anime), inline=False)
        embed.set_footer(text=WATERMARK)  # Add watermark
        embed.timestamp = datetime.now()
        await ctx.send(embed=embed)
    else:
        await ctx.send("No matches found!")

@bot.command()
@commands.has_permissions(administrator=True)
async def sync_commands(ctx):
    """Sync slash commands (Admin only)"""
    try:
        await bot.tree.sync()
        await ctx.send("Successfully synced commands!")
    except Exception as e:
        await ctx.send(f"Failed to sync commands: {e}")

# Add this error handler
@sync_commands.error
async def sync_commands_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need administrator permissions to use this command!")
    else:
        await ctx.send(f"An error occurred: {str(error)}")

@bot.command()
@commands.has_permissions(administrator=True)
async def forcesync(ctx):
    try:
        print("Force syncing commands...")
        bot.tree.copy_global_to(guild=ctx.guild)
        await bot.tree.sync(guild=ctx.guild)
        await ctx.send("Force synced commands to this server!")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command(name="help")
async def help_text(ctx):
    """Shows the help menu with all available commands"""
    embed = discord.Embed(
        title="📖 Anime Watch List Bot Commands",
        description="Here are all the available commands:",
        color=discord.Color.blue()
    )

    # Text Commands section
    text_commands = {
        "!add": "Add new anime: !add title | status | preference | episodes | genre | source_link",
        "!list": "Show your anime list",
        "!progress": "Update progress: !progress <index> <episodes>",
        "!random": "Get a random anime suggestion",
        "!search": "Search anime: !search <keyword>",
        "!help": "Show this help message"
    }

    for cmd, desc in text_commands.items():
        embed.add_field(name=cmd, value=desc, inline=False)

    # Add Valid Values section
    embed.add_field(
        name="📊 Valid Values",
        value=(
            "**Status:** Completed, To Watch, Watching\n"
            "**Preference:** High, Medium, Low"
        ),
        inline=False
    )

    embed.set_footer(text=WATERMARK)
    embed.timestamp = datetime.now()

    await ctx.send(embed=embed)

# Add your bot token here
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN) 