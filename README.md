🏜️ Desert Duel - Retro Multiplayer Shooter

A retro-style multiplayer shooter game where cowboys duel in the desert! Built with Python, PyGame, and Socket Programming.
🎮 Features

    🎯 Real-time Multiplayer Combat - Battle against other players in real-time

    🤠 Retro Cowboy Aesthetics - Pixel-art style characters with unique colors

    💥 Health & Damage System - Dynamic health bars that reduce when hit

    🔫 Bullet Physics - Realistic bullet trails and collision detection

    🏜️ Desert Environment - Scenic desert background with cacti and rocks

    📊 Score Tracking - SQLite database for persistent score tracking

    🎵 Retro Sound Effects - 8-bit style audio feedback

🚀 Installation
Prerequisites

    Python 3.8 or higher

    PyGame library

    SQLite3 (comes with Python)

Setup

    Clone the repository

bash

git clone https://github.com/thonywarrensjnr-hue/Retro_Shooting_Game.git

    Install dependencies

bash

pip install pygame

    Run the server

bash

python server.py

    Run clients (in separate terminals/windows)

bash

python game_client.py

🎯 How to Play
Controls

    WASD - Move your cowboy

    Mouse - Aim

    Left Click - Shoot

    R - Respawn when eliminated

Game Rules

    Each player starts with 100 health points

    Bullets deal 10 damage on hit

    Eliminate other players to earn bounty (100 points per kill)

    Respawn automatically when health reaches 0

    High scores are saved to the database

🏗️ Architecture
Project Structure
text

desert-duel/
├── game_client.py     # Main game client with PyGame interface
├── server.py          # Multiplayer server with database integration
├── protocol.py        # Network protocol definitions
├── game_data.db       # SQLite database (auto-generated)
└── README.md          # This file

Network Protocol

The game uses a custom JSON-based protocol with the following operations:

    JOIN - Player connects to server

    MOVE - Player movement updates

    ATTACK - Player shoots

    BULLET - Bullet creation and movement

    HIT - Damage dealt to players

    RESPAWN - Player respawns

    DISCONNECT - Player leaves

    SCORE_UPDATE - Score updates

Database Schema
sql

CREATE TABLE players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    kills INTEGER DEFAULT 0,
    deaths INTEGER DEFAULT 0,
    high_score INTEGER DEFAULT 0
)

🛠️ Development
Running Tests
bash

# Test server connection
python test_connection.py

# Test attack system
python test_attack.py

Debug Mode

Enable debug mode in game_client.py:
python

self.debug_mode = True

Adding New Features

    New Player Classes: Modify player_colors dictionary in create_retro_graphics()

    New Weapons: Add new bullet types in shoot_bullet() method

    New Maps: Update draw_desert_background() for different environments

    Power-ups: Implement new packet types in protocol and handle in server

📊 Performance

    Frame Rate: 60 FPS target

    Network Latency: ~100ms typical

    Max Players: 6 concurrent players

    Bullet Count: Unlimited (cleaned up automatically)

🐛 Known Issues & Fixes
Issue	Solution
Players not visible in second window	Ensure server is broadcasting MOVE packets correctly
Health bar not reducing	Check collision detection in update_bullets()
Database not updating	Verify SQLite file permissions
Connection refused	Make sure server is running on port 5555
🎨 Art & Assets

All graphics are procedurally generated using PyGame:

    Players: Colored circles with cowboy hats

    Environment: Gradient desert with random cacti and rocks

    Bullets: Yellow trails with particle effects

    UI: Retro-style health bars and score displays

🔧 Technical Details
Collision Detection
python

def check_bullet_player_collision(bullet, player_x, player_y):
    distance = math.sqrt((bullet['x'] - player_x)**2 + 
                         (bullet['y'] - player_y)**2)
    return distance < 25  # 25 pixel collision radius

Camera System

The game uses a follow-camera that centers on the player:
python

self.camera_x = self.player_pos[0] - 400
self.camera_y = self.player_pos[1] - 300

Sound Generation

Sounds are procedurally generated using sine waves:
python

self.shoot_sound = pygame.mixer.Sound(buffer=bytes([
    int(32767 * 0.3 * math.sin(440 * 2 * math.pi * i / 22050) *
        math.exp(-i / 500.0))
    for i in range(500)
]))


Coding Standards

    Follow PEP 8 style guide

    Add comments for complex logic

    Update documentation when changing APIs

    Write tests for new features

📝 License

This project is licensed under the MIT License - see the LICENSE file for details.
🙏 Acknowledgments

    Inspired by classic arcade shooters

    Built with PyGame community tutorials

    Thanks to all contributors and testers

s

🎯 Roadmap

    Add more player customization

    Implement different game modes

    Add environmental hazards

    Create power-up system

    Develop matchmaking system

    Add sound effects menu

    Implement spectator mode

Made with ❤️ by [thonywarrensjnr] <br> ⭐ Star this repo if you found it useful!
