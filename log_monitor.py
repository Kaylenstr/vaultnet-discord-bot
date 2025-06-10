"""
Game Server Log Monitor
=====================

Real-time log monitoring voor verschillende gameservers.
Detecteert join/leave events en controleert toegangsrechten.
"""

import asyncio
import re
import os
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

logger = logging.getLogger(__name__)

class GameLogPatterns:
    """
    Regex patterns voor verschillende gameservers
    """

    MINECRAFT = {
        'join': r'\[([\d:]+)\] \[.*\]: ([\w]+) joined the game',
        'leave': r'\[([\d:]+)\] \[.*\]: ([\w]+) left the game',
        'chat': r'\[([\d:]+)\] \[.*\]: <([\w]+)> (.+)'
    }

    PALWORLD = {
        'join': r'\[([\d\-:\s]+)\].*PlayerConnected: ([\w]+) \(ID:\d+\)',
        'leave': r'\[([\d\-:\s]+)\].*PlayerDisconnected: ([\w]+)',
        'chat': r'\[([\d\-:\s]+)\].*PlayerChat: ([\w]+): (.+)'
    }

    BEAMNG = {
        'join': r'\[([\d\-:\s]+)\].*\[CONNECT\] ([\w]+) \(IP:',
        'leave': r'\[([\d\-:\s]+)\].*\[DISCONNECT\] ([\w]+)',
        'chat': r'\[([\d\-:\s]+)\].*\[CHAT\] ([\w]+): (.+)'
    }

    VALHEIM = {
        'join': r'\[([\d\-:\s]+)\].*Got character ZDOID from ([\w]+)',
        'leave': r'\[([\d\-:\s]+)\].*Closing socket ([\w]+)',
        'chat': r'\[([\d\-:\s]+)\].*Say: ([\w]+): (.+)'
    }

    ARK = {
        'join': r'\[([\d\-:\s]+)\].*([\w]+) joined the ARK',
        'leave': r'\[([\d\-:\s]+)\].*([\w]+) left the ARK',
        'chat': r'\[([\d\-:\s]+)\].*([\w]+): (.+)'
    }

class LogEvent:
    """
    Representeert een log event
    """

    def __init__(self, event_type: str, player_name: str, timestamp: str, game_type: str, extra_data: dict = None):
        self.event_type = event_type  # 'join', 'leave', 'chat'
        self.player_name = player_name
        self.timestamp = timestamp
        self.game_type = game_type
        self.extra_data = extra_data or {}

    def __repr__(self):
        return f"LogEvent({self.event_type}, {self.player_name}, {self.game_type})"

class GameLogParser:
    """
    Parser voor gameserver logs
    """

    def __init__(self, game_type: str):
        self.game_type = game_type.lower()
        self.patterns = getattr(GameLogPatterns, game_type.upper(), {})

    def parse_line(self, line: str) -> LogEvent:
        """
        Parse een enkele log regel
        """
        for event_type, pattern in self.patterns.items():
            match = re.search(pattern, line)
            if match:
                groups = match.groups()
                timestamp = groups[0]
                player_name = groups[1]

                extra_data = {}
                if event_type == 'chat' and len(groups) > 2:
                    extra_data['message'] = groups[2]

                return LogEvent(
                    event_type=event_type,
                    player_name=player_name,
                    timestamp=timestamp,
                    game_type=self.game_type,
                    extra_data=extra_data
                )

        return None

class LogFileHandler(FileSystemEventHandler):
    """
    Watchdog handler voor log bestanden
    """

    def __init__(self, log_parser: GameLogParser, callback_func):
        self.parser = log_parser
        self.callback = callback_func
        self.last_position = 0

    def on_modified(self, event):
        """
        Wordt aangeroepen wanneer het log bestand wordt gewijzigd
        """
        if event.is_directory:
            return

        try:
            with open(event.src_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Ga naar de laatste bekende positie
                f.seek(self.last_position)

                # Lees nieuwe regels
                new_lines = f.readlines()

                # Update positie
                self.last_position = f.tell()

                # Parse elke nieuwe regel
                for line in new_lines:
                    line = line.strip()
                    if line:
                        event = self.parser.parse_line(line)
                        if event:
                            # Roep callback aan met het event
                            asyncio.create_task(self.callback(event))

        except Exception as e:
            logger.error(f"Error reading log file {event.src_path}: {e}")

class GameLogMonitor:
    """
    Hoofdklasse voor log monitoring
    """

    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.observers = {}
        self.active_monitors = {}

    async def start_monitoring(self, server_name: str, game_type: str, log_path: str):
        """
        Start monitoring voor een specifieke server
        """
        if not os.path.exists(log_path):
            logger.warning(f"Log bestand niet gevonden: {log_path}")
            return False

        try:
            # Maak parser
            parser = GameLogParser(game_type)

            # Maak handler met callback
            handler = LogFileHandler(
                parser, 
                lambda event: self.handle_log_event(server_name, event)
            )

            # Maak observer
            observer = Observer()
            observer.schedule(handler, os.path.dirname(log_path), recursive=False)
            observer.start()

            # Opslaan
            self.observers[server_name] = observer
            self.active_monitors[server_name] = {
                'game_type': game_type,
                'log_path': log_path,
                'parser': parser,
                'handler': handler
            }

            logger.info(f"Log monitoring gestart voor {server_name} ({game_type})")
            return True

        except Exception as e:
            logger.error(f"Failed to start monitoring for {server_name}: {e}")
            return False

    async def stop_monitoring(self, server_name: str):
        """
        Stop monitoring voor een server
        """
        if server_name in self.observers:
            self.observers[server_name].stop()
            self.observers[server_name].join()
            del self.observers[server_name]

        if server_name in self.active_monitors:
            del self.active_monitors[server_name]

        logger.info(f"Log monitoring gestopt voor {server_name}")

    async def handle_log_event(self, server_name: str, event: LogEvent):
        """
        Handle een log event (join/leave/chat)
        """
        logger.info(f"[{server_name}] {event}")

        if event.event_type == 'join':
            await self.handle_player_join(server_name, event)
        elif event.event_type == 'leave':
            await self.handle_player_leave(server_name, event)
        elif event.event_type == 'chat':
            await self.handle_player_chat(server_name, event)

    async def handle_player_join(self, server_name: str, event: LogEvent):
        """
        Handle speler join event
        """
        player_name = event.player_name

        # Controleer of speler toegang heeft
        has_access = await self.check_player_access(server_name, player_name, event.game_type)

        if not has_access:
            logger.warning(f"Unauthorized join attempt: {player_name} on {server_name}")

            # Kick de speler
            success = await self.kick_player(server_name, player_name, event.game_type)

            # Log de actie
            await self.log_action(
                server_name, 
                player_name, 
                'unauthorized_join' if success else 'kick_failed',
                'Player was kicked for unauthorized access' if success else 'Failed to kick player'
            )

            # Stuur Discord notificatie
            await self.send_discord_notification(
                server_name,
                f"🚫 **Unauthorized Access**\n"
                f"Player: `{player_name}`\n"
                f"Action: {'Kicked' if success else 'Kick failed'}\n"
                f"Server: {server_name}"
            )
        else:
            logger.info(f"Authorized join: {player_name} on {server_name}")
            await self.log_action(server_name, player_name, 'authorized_join', 'Player joined with valid access')

    async def handle_player_leave(self, server_name: str, event: LogEvent):
        """
        Handle speler leave event
        """
        await self.log_action(server_name, event.player_name, 'leave', 'Player left the server')

    async def handle_player_chat(self, server_name: str, event: LogEvent):
        """
        Handle chat berichten (optioneel)
        """
        # Kan gebruikt worden voor chat moderation
        pass

    async def check_player_access(self, server_name: str, player_name: str, game_type: str) -> bool:
        """
        Controleer of een speler toegang heeft tot de server
        """
        try:
            async with aiosqlite.connect(self.bot.db_path) as db:
                # Zoek de Discord gebruiker op basis van game username
                cursor = await db.execute(
                    """SELECT u.discord_id, ga.game_username, dl.current_level, s.required_level
                       FROM users u
                       JOIN game_accounts ga ON u.discord_id = ga.discord_id
                       LEFT JOIN discord_levels dl ON u.discord_id = dl.discord_id
                       JOIN servers s ON s.server_name = ?
                       WHERE ga.game_username = ? AND ga.game_type = ?""",
                    (server_name, player_name, game_type)
                )

                result = await cursor.fetchone()

                if not result:
                    # Speler niet gevonden in database
                    return False

                discord_id, game_username, current_level, required_level = result

                # Controleer level requirement
                if current_level is None:
                    current_level = 0

                return current_level >= required_level

        except Exception as e:
            logger.error(f"Error checking player access: {e}")
            return False

    async def kick_player(self, server_name: str, player_name: str, game_type: str) -> bool:
        """
        Kick een speler van de server via RCON
        """
        # Deze functie wordt geïmplementeerd in de RCON module
        logger.info(f"Would kick {player_name} from {server_name} (RCON not implemented yet)")
        return True  # Tijdelijk altijd True

    async def log_action(self, server_name: str, player_name: str, action: str, reason: str):
        """
        Log een actie in de database
        """
        try:
            async with aiosqlite.connect(self.bot.db_path) as db:
                await db.execute(
                    """INSERT INTO activity_log (server_id, action, game_username, result, reason)
                       VALUES ((SELECT id FROM servers WHERE server_name = ?), ?, ?, 'success', ?)""",
                    (server_name, action, player_name, reason)
                )
                await db.commit()
        except Exception as e:
            logger.error(f"Error logging action: {e}")

    async def send_discord_notification(self, server_name: str, message: str):
        """
        Stuur een Discord notificatie
        """
        try:
            # Zoek het juiste kanaal op
            async with aiosqlite.connect(self.bot.db_path) as db:
                cursor = await db.execute(
                    "SELECT discord_channel_id FROM servers WHERE server_name = ?",
                    (server_name,)
                )
                result = await cursor.fetchone()

                if result and result[0]:
                    channel_id = int(result[0])
                    channel = self.bot.get_channel(channel_id)

                    if channel:
                        embed = discord.Embed(
                            title=f"🎮 {server_name}",
                            description=message,
                            color=discord.Color.red(),
                            timestamp=datetime.now()
                        )
                        await channel.send(embed=embed)

        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}")

# Test functie
def test_log_parsing():
    """
    Test de log parsing functionaliteit
    """
    # Test Minecraft log
    minecraft_parser = GameLogParser('minecraft')
    minecraft_line = "[14:30:45] [Server thread/INFO]: TestPlayer joined the game"
    result = minecraft_parser.parse_line(minecraft_line)
    print(f"Minecraft test: {result}")

    # Test Palworld log
    palworld_parser = GameLogParser('palworld')
    palworld_line = "[2024-02-01 14:30:45] PlayerConnected: TestPlayer (ID:12345)"
    result = palworld_parser.parse_line(palworld_line)
    print(f"Palworld test: {result}")

if __name__ == "__main__":
    test_log_parsing()
