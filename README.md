# Discord Gameserver Access Control Bot

Een Discord bot voor automatische toegangscontrole van gameservers op basis van Discord levels. Speciaal ontwikkeld voor VaultNet homelab met Unraid server (16GB RAM, Ryzen 3) en Raspberry Pi 4 (2GB).

## 🎯 Wat doet deze bot?

- **Level-based toegang**: Alleen gebruikers met het juiste Discord level krijgen toegang tot gameservers
- **Real-time monitoring**: Monitort gameserver logs en detecteert ongeautoriseerde toegang
- **Automatisch kicken**: Kick spelers die niet in de database staan of het verkeerde level hebben
- **Multi-game support**: Ondersteunt alle games die AMP kan hosten (Minecraft, Palworld, BeamNG, etc.)
- **Discord integratie**: Slash commands voor eenvoudig beheer

## 🚀 Snelle Start

### 1. Installatie

```bash
# Clone dit project
git clone <repository-url>
cd discord-gameserver-bot

# Run automatische setup
python setup.py
```

### 2. Configuratie

Pas `.env` bestand aan met je eigen instellingen:

```env
# Discord instellingen
DISCORD_BOT_TOKEN=your_bot_token_here
GUILD_ID=your_discord_server_id

# Game server paden (pas aan naar jouw setup)
MINECRAFT_LOG_PATH=/mnt/user/appdata/minecraft/logs/latest.log
PALWORLD_LOG_PATH=/mnt/user/appdata/palworld/logs/server.log

# RCON instellingen
MINECRAFT_RCON_HOST=localhost
MINECRAFT_RCON_PORT=25575
MINECRAFT_RCON_PASSWORD=your_rcon_password
```

### 3. Bot starten

```bash
# Windows
start_bot.bat

# Linux/Mac
./start_bot.sh
```

## 📋 Discord Commands

### Voor spelers:
- `/link <game> <username>` - Koppel je Discord aan een game username
- `/accounts` - Bekijk je gekoppelde accounts

### Voor beheerders:
- `/server add <name> <game> <level>` - Voeg server toe
- `/server list` - Bekijk alle servers
- `/logs <server>` - Bekijk recente activiteit

## 🎮 Ondersteunde Games

De bot werkt met alle games die AMP ondersteunt:

### Populaire games:
- **Minecraft** (Java & Bedrock)
- **Palworld**
- **BeamNG.drive**
- **Valheim**
- **Rust**
- **ARK: Survival Evolved**
- **Project Zomboid**
- **Terraria**
- **Satisfactory**
- **7 Days to Die**
- **The Forest**
- **V Rising**

En nog vele anderen via AMP's uitgebreide ondersteuning.

## 🔧 Hoe het werkt

### 1. Account koppeling
```
Discord gebruiker → /link minecraft Steve123
                 → Database opslaan: Discord ID ↔ Minecraft naam
```

### 2. Level controle
```
Discord level 5+ → Toegang tot Minecraft server
Discord level 3+ → Toegang tot Palworld server
Discord level 7+ → Toegang tot BeamNG server
```

### 3. Real-time monitoring
```
Gameserver log → Bot detecteert join
              → Controleert database
              → Kick indien ongeautoriseerd
              → Discord notificatie
```

## 📁 Project Structuur

```
discord-gameserver-bot/
├── bot.py                 # Hoofdbot code
├── log_monitor.py         # Log monitoring module
├── database_setup.sql     # Database schema
├── requirements.txt       # Python dependencies
├── .env.template         # Configuratie template
├── setup.py              # Automatische installatie
├── start_bot.sh/.bat     # Start scripts
└── README.md             # Deze documentatie
```

## 🗄️ Database Schema

```sql
users           # Discord gebruikers
game_accounts   # Game usernames per gebruiker  
servers         # Server configuraties
activity_log    # Audit log van alle acties
discord_levels  # Cache voor Discord levels
```

## ⚙️ Configuratie voor VaultNet

### Unraid Server Setup
```bash
# Minecraft server pad
MINECRAFT_LOG_PATH=/mnt/user/appdata/minecraft/logs/latest.log

# AMP integratie
AMP_URL=http://192.168.1.100:8080
AMP_USERNAME=admin
```

### Raspberry Pi 4 Setup
```bash
# Bot draaien op Pi voor 24/7 operatie
# Lichtgewicht setup zonder GUI
sudo apt update
sudo apt install python3-venv python3-pip
```

## 🔐 Security Features

- **Token bescherming**: Bot tokens in environment variables
- **Input validatie**: Alle user input wordt gevalideerd
- **Rate limiting**: Voorkomt spam van commands
- **Audit logging**: Alle acties worden gelogd
- **Database encryptie**: Gevoelige data wordt beveiligd

## 🐛 Troubleshooting

### Bot start niet
```bash
# Check Python versie
python --version  # Moet 3.8+ zijn

# Check dependencies
pip list | grep discord

# Check logs
tail -f bot.log
```

### Log monitoring werkt niet
```bash
# Check file permissions
ls -la /path/to/gameserver/logs/

# Check log bestand bestaat
tail -f /path/to/gameserver/logs/latest.log
```

### RCON connectie problemen
```bash
# Test RCON handmatig
mcrcon -H localhost -P 25575 -p password "list"
```

## 📊 Performance

### Systeem vereisten:
- **RAM**: 100-500MB (afhankelijk van aantal servers)
- **CPU**: Minimaal (async processing)
- **Disk**: 50MB + log storage
- **Network**: Lokaal netwerk toegang tot gameservers

### Schaalbaarheid:
- ✅ 1-10 gameservers: Uitstekende performance
- ✅ 10-50 gameservers: Goede performance  
- ⚠️ 50+ gameservers: Mogelijk extra optimalisatie nodig

## 🔄 Updates

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Update database schema
python -c "import sqlite3; # run migration script"

# Restart bot
./start_bot.sh
```

## 📞 Support

Bij problemen:

1. **Check logs**: `bot.log` en console output
2. **Database**: Controleer `gameserver_bot.db` met SQLite browser
3. **Discord permissions**: Zorg dat bot juiste rechten heeft
4. **File paths**: Controleer of log bestanden bestaan en readable zijn

## 📝 License

Dit project is ontwikkeld voor VaultNet homelab. Gebruik op eigen risico.

## 🙏 Credits

- **Discord.py**: Python Discord API wrapper
- **Watchdog**: File system monitoring
- **MCRcon**: Minecraft RCON client
- **AMP**: CubeCoders Application Management Panel