#!/usr/bin/env python3
'''
Discord Gameserver Bot - Setup Script
===================================

Automatische installatie en configuratie van de Discord Gameserver Access Control Bot.
Voor VaultNet homelab project.
'''

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def print_header():
    '''Print setup header'''
    print("=" * 60)
    print("🎮 Discord Gameserver Access Control Bot")
    print("   Setup Script voor VaultNet")
    print("=" * 60)
    print()

def check_python_version():
    '''Controleer Python versie'''
    print("🐍 Python versie controleren...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 of hoger is vereist!")
        print(f"   Huidige versie: {sys.version}")
        return False
    print(f"✅ Python versie OK: {sys.version.split()[0]}")
    return True

def create_virtual_environment():
    '''Maak virtual environment'''
    print("\n📦 Virtual environment maken...")

    if os.path.exists("venv"):
        print("⚠️  Virtual environment bestaat al")
        return True

    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment aangemaakt")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Fout bij maken virtual environment: {e}")
        return False

def get_pip_command():
    '''Get correct pip command voor virtual environment'''
    if os.name == 'nt':  # Windows
        return os.path.join("venv", "Scripts", "pip")
    else:  # Linux/Mac
        return os.path.join("venv", "bin", "pip")

def install_dependencies():
    '''Installeer dependencies'''
    print("\n📥 Dependencies installeren...")

    pip_cmd = get_pip_command()

    try:
        # Upgrade pip eerst
        subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True)
        print("✅ Pip geüpdatet")

        # Installeer requirements
        if os.path.exists("requirements.txt"):
            subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
            print("✅ Dependencies geïnstalleerd")
        else:
            print("❌ requirements.txt niet gevonden!")
            return False

        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Fout bij installeren dependencies: {e}")
        return False

def setup_database():
    '''Setup database'''
    print("\n🗃️  Database opzetten...")

    db_path = "gameserver_bot.db"

    try:
        # Maak database connectie
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Lees en voer schema uit
        if os.path.exists("database_setup.sql"):
            with open("database_setup.sql", "r") as f:
                schema = f.read()
            cursor.executescript(schema)
            conn.commit()
            print("✅ Database schema geladen")
        else:
            print("❌ database_setup.sql niet gevonden!")
            return False

        # Voeg voorbeeld server configuratie toe
        cursor.execute('''
            INSERT OR IGNORE INTO servers 
            (server_name, game_type, required_level, log_path, rcon_host, rcon_port) 
            VALUES 
            ('minecraft-main', 'minecraft', 5, '/path/to/minecraft/logs/latest.log', 'localhost', 25575),
            ('palworld-server', 'palworld', 3, '/path/to/palworld/logs/server.log', 'localhost', 8211),
            ('beamng-server', 'beamng', 7, '/path/to/beamng/logs/server.log', 'localhost', 64256)
        ''')
        conn.commit()
        conn.close()

        print("✅ Database opgezet met voorbeeld configuratie")
        return True

    except Exception as e:
        print(f"❌ Database setup fout: {e}")
        return False

def create_env_file():
    '''Maak .env bestand van template'''
    print("\n⚙️  Configuratie bestand maken...")

    if os.path.exists(".env"):
        print("⚠️  .env bestand bestaat al - wordt niet overschreven")
        return True

    if os.path.exists(".env.template"):
        # Kopieer template naar .env
        with open(".env.template", "r") as template:
            content = template.read()

        with open(".env", "w") as env_file:
            env_file.write(content)

        print("✅ .env bestand aangemaakt van template")
        print("⚠️  BELANGRIJK: Pas .env aan met je eigen configuratie!")
        return True
    else:
        print("❌ .env.template niet gevonden!")
        return False

def create_start_script():
    '''Maak start script'''
    print("\n🚀 Start script maken...")

    if os.name == 'nt':  # Windows
        script_content = '@echo off\necho Starting Discord Gameserver Bot...\n.\\venv\\Scripts\\python.exe bot.py\npause\n'
        script_name = "start_bot.bat"
    else:  # Linux/Mac
        script_content = '#!/bin/bash\necho "Starting Discord Gameserver Bot..."\n./venv/bin/python bot.py\n'
        script_name = "start_bot.sh"

    with open(script_name, "w") as f:
        f.write(script_content)

    # Maak executable op Linux/Mac
    if os.name != 'nt':
        os.chmod(script_name, 0o755)

    print(f"✅ Start script aangemaakt: {script_name}")

def print_next_steps():
    '''Print volgende stappen'''
    print("\n" + "=" * 60)
    print("🎉 Setup voltooid!")
    print("=" * 60)
    print()
    print("📋 Volgende stappen:")
    print("1. Pas .env bestand aan met je configuratie:")
    print("   - Discord bot token")
    print("   - Discord server ID")
    print("   - Game server log paden")
    print("   - RCON instellingen")
    print()
    print("2. Start de bot:")
    if os.name == 'nt':
        print("   Windows: start_bot.bat")
    else:
        print("   Linux/Mac: ./start_bot.sh")
    print()
    print("3. Voeg de bot toe aan je Discord server met deze permissions:")
    print("   - Send Messages")
    print("   - Use Slash Commands") 
    print("   - Read Message History")
    print("   - Manage Messages")
    print()
    print("4. Test de bot met /link commando in Discord")
    print()
    print("📚 Voor hulp en documentatie:")
    print("   - Bekijk README.md")
    print("   - Check bot.log voor error logs")
    print("   - Database: gameserver_bot.db")
    print()

def main():
    '''Hoofdfunctie'''
    print_header()

    # Check Python versie
    if not check_python_version():
        sys.exit(1)

    # Maak virtual environment
    if not create_virtual_environment():
        sys.exit(1)

    # Installeer dependencies
    if not install_dependencies():
        sys.exit(1)

    # Setup database
    if not setup_database():
        sys.exit(1)

    # Maak .env bestand
    if not create_env_file():
        sys.exit(1)

    # Maak start script
    create_start_script()

    # Print volgende stappen
    print_next_steps()

if __name__ == "__main__":
    main()
