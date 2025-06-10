"""
Discord Gameserver Access Control Bot
====================================

Een Discord bot die gameserver toegang controleert op basis van Discord levels
en real-time log monitoring gebruikt om ongeautoriseerde spelers te kicken.

Auteur: VaultNet Homelab Project
"""

import discord
from discord.ext import commands
import aiosqlite
import asyncio
import os
import logging
from dotenv import load_dotenv
from datetime import datetime

# Laad environment variabelen
load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GameServerBot(commands.Bot):
    """
    Hoofdbot klasse die alle functionaliteiten beheert
    """

    def __init__(self):
        # Bot intents - wat de bot mag doen
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix='!', 
            intents=intents,
            description="Gameserver Access Control Bot voor VaultNet"
        )

        # Database
        self.db_path = os.getenv('DATABASE_PATH', 'gameserver_bot.db')

        # Configuratie
        self.guild_id = int(os.getenv('GUILD_ID', 0))
        self.debug_mode = os.getenv('DEBUG_MODE', 'False').lower() == 'true'

        # Game server monitoring
        self.log_monitors = {}
        self.rcon_connections = {}

    async def setup_hook(self):
        """
        Setup die wordt uitgevoerd wanneer de bot start
        """
        # Database initialiseren
        await self.init_database()

        # Log monitors starten
        await self.start_log_monitoring()

        logger.info("Bot setup voltooid!")

    async def init_database(self):
        """
        Initialiseer de database met het schema
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Lees database schema
                if os.path.exists('database_setup.sql'):
                    with open('database_setup.sql', 'r') as f:
                        schema = f.read()
                    await db.executescript(schema)
                    await db.commit()
                    logger.info("Database schema geladen")
                else:
                    logger.warning("database_setup.sql niet gevonden")
        except Exception as e:
            logger.error(f"Database initialisatie gefaald: {e}")

    async def start_log_monitoring(self):
        """
        Start log monitoring voor alle geconfigureerde servers
        """
        # Dit wordt later geïmplementeerd met watchdog
        logger.info("Log monitoring voorbereid (implementatie volgt)")

    async def on_ready(self):
        """
        Wordt uitgevoerd wanneer de bot online komt
        """
        logger.info(f'{self.user} is verbonden met Discord!')
        logger.info(f'Bot is actief in {len(self.guilds)} server(s)')

        # Sync slash commands
        if self.guild_id:
            guild = discord.Object(id=self.guild_id)
            await self.tree.sync(guild=guild)
            logger.info(f"Slash commands gesynchroniseerd voor guild {self.guild_id}")
        else:
            await self.tree.sync()
            logger.info("Slash commands globaal gesynchroniseerd")

# Commando's en event handlers
@discord.app_commands.describe(
    game="Het type game (minecraft, palworld, beamng, etc.)",
    username="Je gebruikersnaam in dit spel"
)
async def link_game_account(interaction: discord.Interaction, game: str, username: str):
    """
    Koppel je Discord account aan een game username
    """
    try:
        # Database operatie
        async with aiosqlite.connect(interaction.client.db_path) as db:
            # Voeg gebruiker toe als die nog niet bestaat
            await db.execute(
                "INSERT OR IGNORE INTO users (discord_id, discord_username) VALUES (?, ?)",
                (str(interaction.user.id), interaction.user.display_name)
            )

            # Voeg/update game account toe
            await db.execute(
                """INSERT OR REPLACE INTO game_accounts 
                   (discord_id, game_type, game_username) 
                   VALUES (?, ?, ?)""",
                (str(interaction.user.id), game.lower(), username)
            )

            await db.commit()

        # Succesbericht
        embed = discord.Embed(
            title="✅ Account Gekoppeld",
            description=f"Je Discord account is gekoppeld aan **{username}** voor **{game.title()}**",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        logger.info(f"User {interaction.user.display_name} linked {game}:{username}")

    except Exception as e:
        logger.error(f"Error linking account: {e}")
        await interaction.response.send_message(
            "❌ Er ging iets mis bij het koppelen van je account. Probeer het later opnieuw.",
            ephemeral=True
        )

@discord.app_commands.describe()
async def my_accounts(interaction: discord.Interaction):
    """
    Bekijk je gekoppelde game accounts
    """
    try:
        async with aiosqlite.connect(interaction.client.db_path) as db:
            cursor = await db.execute(
                """SELECT game_type, game_username, verified, created_at 
                   FROM game_accounts 
                   WHERE discord_id = ?""",
                (str(interaction.user.id),)
            )
            accounts = await cursor.fetchall()

        if not accounts:
            embed = discord.Embed(
                title="🎮 Mijn Game Accounts",
                description="Je hebt nog geen game accounts gekoppeld.\nGebruik `/link` om een account te koppelen.",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="🎮 Mijn Game Accounts",
                color=discord.Color.blue()
            )

            for game_type, username, verified, created_at in accounts:
                status = "✅ Geverifieerd" if verified else "⏳ Niet geverifieerd"
                embed.add_field(
                    name=f"{game_type.title()}",
                    value=f"**Username:** {username}\n**Status:** {status}",
                    inline=True
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        logger.error(f"Error fetching accounts: {e}")
        await interaction.response.send_message(
            "❌ Er ging iets mis bij het ophalen van je accounts.",
            ephemeral=True
        )

# Event handler voor berichten
async def on_member_update(before: discord.Member, after: discord.Member):
    """
    Detecteer level veranderingen (werkt met bots zoals MEE6)
    """
    # Dit wordt geïmplementeerd als er level bots zijn geconfigureerd
    pass

async def main():
    """
    Start de bot
    """
    # Controleer of bot token is ingesteld
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("DISCORD_BOT_TOKEN niet ingesteld in .env bestand!")
        return

    # Start bot
    bot = GameServerBot()

    # Voeg commands toe
    bot.tree.add_command(
        discord.app_commands.Command(
            name="link",
            description="Koppel je Discord account aan een game username",
            callback=link_game_account
        )
    )

    bot.tree.add_command(
        discord.app_commands.Command(
            name="accounts",
            description="Bekijk je gekoppelde game accounts",
            callback=my_accounts
        )
    )

    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot wordt afgesloten...")
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
