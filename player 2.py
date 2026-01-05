import pygame
import socket
import threading
import sys
import time
import random
import math
from protocol import OpCode, GamePacket

HOST = '127.0.0.1'
PORT = 5555


class GameClient:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Desert Arena - Retro Shooter")
        self.clock = pygame.time.Clock()
        self.running = True

        self.load_sounds()

        self.create_retro_graphics()

        self.client_id = None
        self.player_pos = [400, 300]
        self.player_health = 100
        self.player_score = 0
        self.player_direction = 'right'
        self.last_shot = 0
        self.shot_cooldown = 300  # ms


        self.other_players = {}
        self.bullets = []
        self.particles = []
        self.cacti = []
        self.rocks = []
        self.generate_desert_objects()


        self.camera_x = 0
        self.camera_y = 0

        self.connected = False
        self.connection_error = None


        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 18)

        print("🤠 Connecting to Desert Arena...")
        self.connect_to_server()

        if self.connected:
            print("🤠 Connected! Yeehaw!")
            threading.Thread(target=self.receive_messages, daemon=True).start()
        else:
            print(f"❌ Failed to connect: {self.connection_error}")

    def load_sounds(self):
        try:
            self.shoot_sound = pygame.mixer.Sound(buffer=bytes([
                int(32767 * 0.3 * math.sin(440 * 2 * math.pi * i / 22050) *
                    math.exp(-i / 500.0))
                for i in range(500)
            ]))
            self.shoot_sound.set_volume(0.3)


            self.hit_sound = pygame.mixer.Sound(buffer=bytes([
                int(32767 * 0.4 * math.sin(220 * 2 * math.pi * i / 22050) *
                    (1 - i / 800.0))
                for i in range(800)
            ]))
            self.hit_sound.set_volume(0.4)


            self.death_sound = pygame.mixer.Sound(buffer=bytes([
                int(32767 * 0.5 * math.sin(110 * 2 * math.pi * i / 22050) *
                    math.exp(-i / 1000.0))
                for i in range(1000)
            ]))
            self.death_sound.set_volume(0.5)

        except:
            self.shoot_sound = None
            self.hit_sound = None
            self.death_sound = None

    def create_retro_graphics(self):
        self.player_colors = {
            1: {'body': (255, 100, 100), 'hat': (100, 200, 100), 'gun': (150, 150, 150)},
            2: {'body': (100, 100, 255), 'hat': (255, 200, 50), 'gun': (150, 150, 150)},
            3: {'body': (100, 255, 100), 'hat': (255, 100, 255), 'gun': (150, 150, 150)},
            4: {'body': (255, 255, 100), 'hat': (100, 100, 255), 'gun': (150, 150, 150)},
            5: {'body': (255, 100, 255), 'hat': (100, 255, 255), 'gun': (150, 150, 150)},
            6: {'body': (100, 255, 255), 'hat': (255, 150, 100), 'gun': (150, 150, 150)},
        }

        self.default_color = {'body': (200, 200, 200), 'hat': (100, 100, 100), 'gun': (150, 150, 150)}

        self.desert_pattern = pygame.Surface((800, 600))
        self.desert_pattern.fill((210, 180, 140))
        for _ in range(5000):
            x = random.randint(0, 799)
            y = random.randint(0, 599)
            brightness = random.randint(-20, 20)
            color = (
                max(0, min(255, 210 + brightness)),
                max(0, min(255, 180 + brightness)),
                max(0, min(255, 140 + brightness))
            )
            self.desert_pattern.set_at((x, y), color)

    def generate_desert_objects(self):
        for _ in range(15):
            x = random.randint(50, 750)
            y = random.randint(50, 550)
            height = random.randint(40, 80)
            width = random.randint(20, 40)
            self.cacti.append({
                'x': x, 'y': y,
                'width': width, 'height': height,
                'color': (80, 150, 80),
                'spikes': random.randint(3, 8)
            })

        for _ in range(20):
            x = random.randint(50, 750)
            y = random.randint(50, 550)
            size = random.randint(30, 60)
            self.rocks.append({
                'x': x, 'y': y,
                'size': size,
                'color': (120, 120, 120)
            })

    def draw_desert_background(self):
        self.screen.blit(self.desert_pattern, (0, 0))
        mountain_colors = [(150, 120, 100), (140, 110, 90), (130, 100, 80)]
        for i, color in enumerate(mountain_colors):
            points = [
                (0, 400 + i * 20),
                (200, 300 + i * 20),
                (400, 350 + i * 20),
                (600, 280 + i * 20),
                (800, 400 + i * 20),
                (800, 600),
                (0, 600)
            ]
            pygame.draw.polygon(self.screen, color, points)

        for cactus in self.cacti:
            x = cactus['x'] - self.camera_x
            y = cactus['y'] - self.camera_y
            pygame.draw.rect(self.screen, cactus['color'],
                             (x - cactus['width'] // 2, y - cactus['height'],
                              cactus['width'], cactus['height']))
            arm_height = cactus['height'] // 2
            pygame.draw.rect(self.screen, cactus['color'],
                             (x - cactus['width'] // 2 - 20, y - cactus['height'] + arm_height,
                              20, 15))
            pygame.draw.rect(self.screen, cactus['color'],
                             (x + cactus['width'] // 2, y - cactus['height'] + arm_height,
                              20, 15))
            for _ in range(cactus['spikes']):
                spike_x = x + random.randint(-cactus['width'] // 2, cactus['width'] // 2)
                spike_y = y - cactus['height'] + random.randint(0, cactus['height'])
                pygame.draw.line(self.screen, (50, 100, 50),
                                 (spike_x, spike_y),
                                 (spike_x + random.randint(-5, 5), spike_y + random.randint(-5, 5)), 2)
        for rock in self.rocks:
            x = rock['x'] - self.camera_x
            y = rock['y'] - self.camera_y


            pygame.draw.circle(self.screen, (80, 80, 80),
                               (int(x + 3), int(y + 3)), rock['size'] // 2)

            pygame.draw.circle(self.screen, rock['color'],
                               (int(x), int(y)), rock['size'] // 2)

            for _ in range(rock['size'] // 5):
                tx = x + random.randint(-rock['size'] // 2, rock['size'] // 2)
                ty = y + random.randint(-rock['size'] // 2, rock['size'] // 2)
                pygame.draw.circle(self.screen, (100, 100, 100), (int(tx), int(ty)), 2)

        pygame.draw.circle(self.screen, (255, 255, 200), (700, 80), 40)
        pygame.draw.circle(self.screen, (255, 240, 150), (700, 80), 35)


        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            start_x = 700 + 45 * math.cos(rad)
            start_y = 80 + 45 * math.sin(rad)
            end_x = 700 + 60 * math.cos(rad)
            end_y = 80 + 60 * math.sin(rad)
            pygame.draw.line(self.screen, (255, 240, 150, 150),
                             (start_x, start_y), (end_x, end_y), 3)

    def draw_player(self, x, y, player_id, is_current_player=False):
        colors = self.player_colors.get(player_id, self.default_color)

        screen_x = x - self.camera_x
        screen_y = y - self.camera_y

        pygame.draw.circle(self.screen, (50, 50, 50, 150),
                           (int(screen_x + 3), int(screen_y + 3)), 15)

        pygame.draw.circle(self.screen, colors['body'],
                           (int(screen_x), int(screen_y)), 15)

        hat_points = [
            (screen_x - 15, screen_y - 10),
            (screen_x + 15, screen_y - 10),
            (screen_x + 12, screen_y - 25),
            (screen_x - 12, screen_y - 25)
        ]
        pygame.draw.polygon(self.screen, colors['hat'], hat_points)

        pygame.draw.rect(self.screen, (80, 80, 80),
                         (screen_x - 18, screen_y - 12, 36, 4))

        pygame.draw.circle(self.screen, (255, 220, 180),
                           (int(screen_x), int(screen_y - 5)), 8)

        if self.player_direction == 'right' or (player_id != self.client_id and
                                                self.other_players.get(player_id, {}).get('direction') == 'right'):

            pygame.draw.circle(self.screen, (50, 50, 100),
                               (int(screen_x + 3), int(screen_y - 5)), 3)
            pygame.draw.circle(self.screen, (50, 50, 100),
                               (int(screen_x + 8), int(screen_y - 7)), 2)
        else:
            pygame.draw.circle(self.screen, (50, 50, 100),
                               (int(screen_x - 3), int(screen_y - 5)), 3)
            pygame.draw.circle(self.screen, (50, 50, 100),
                               (int(screen_x - 8), int(screen_y - 7)), 2)

        gun_length = 25
        if self.player_direction == 'right' or (player_id != self.client_id and
                                                self.other_players.get(player_id, {}).get('direction') == 'right'):
            gun_end_x = screen_x + gun_length
            gun_end_y = screen_y - 5
        else:
            gun_end_x = screen_x - gun_length
            gun_end_y = screen_y - 5
        pygame.draw.line(self.screen, colors['gun'],
                         (screen_x, screen_y - 5),
                         (gun_end_x, gun_end_y), 5)

        pygame.draw.rect(self.screen, (100, 70, 30),
                         (screen_x - 3, screen_y - 8, 6, 10))

        if is_current_player:
            pulse = abs(math.sin(time.time() * 3)) * 10
            glow_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 255, 255, 50),
                               (20, 20), 15 + pulse)
            self.screen.blit(glow_surf, (screen_x - 20, screen_y - 20))

            you_text = self.font_tiny.render("YOU", True, (255, 255, 255))
            self.screen.blit(you_text, (screen_x - you_text.get_width() // 2, screen_y - 45))
        else:
            id_text = self.font_tiny.render(f"Cowboy {player_id}", True, (255, 255, 200))
            self.screen.blit(id_text, (screen_x - id_text.get_width() // 2, screen_y - 45))

    def draw_bullet(self, x, y, dx, dy):
        screen_x = x - self.camera_x
        screen_y = y - self.camera_y

        trail_length = 10
        for i in range(trail_length):
            trail_x = screen_x - dx * i * 2
            trail_y = screen_y - dy * i * 2
            alpha = 255 * (1 - i / trail_length)
            pygame.draw.circle(self.screen, (255, 255, 100, int(alpha)),
                               (int(trail_x), int(trail_y)), 2)

        pygame.draw.circle(self.screen, (255, 255, 0), (int(screen_x), int(screen_y)), 3)
        pygame.draw.circle(self.screen, (255, 200, 0), (int(screen_x), int(screen_y)), 2)

    def update_camera(self):
        self.camera_x = self.player_pos[0] - 400
        self.camera_y = self.player_pos[1] - 300
        self.camera_x = max(0, min(self.camera_x, 800 - 800))
        self.camera_y = max(0, min(self.camera_y, 600 - 600))

    def connect_to_server(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((HOST, PORT))
            self.connected = True
            return True
        except Exception as e:
            self.connection_error = str(e)
            self.connected = False
            return False

    def receive_messages(self):
        while self.running and self.connected:
            try:
                data = self.socket.recv(1024)
                if not data:
                    self.connected = False
                    break

                packet = GamePacket.from_json(data)
                if packet:
                    self.handle_packet(packet)

            except socket.timeout:
                continue
            except:
                self.connected = False
                break

    def handle_packet(self, packet):
        if packet.op_code == OpCode.JOIN:
            if 'assigned_id' in packet.data:
                self.client_id = packet.data['assigned_id']
                if 'spawn_x' in packet.data and 'spawn_y' in packet.data:
                    self.player_pos = [packet.data['spawn_x'], packet.data['spawn_y']]
                print(f"🤠 Welcome Cowboy {self.client_id}!")

        elif packet.op_code == OpCode.MOVE:
            player_id = packet.sender_id
            if player_id != self.client_id:
                self.other_players[player_id] = {
                    'x': packet.data.get('x', 400),
                    'y': packet.data.get('y', 300),
                    'health': packet.data.get('health', 100),
                    'direction': packet.data.get('direction', 'right')
                }

        elif packet.op_code == OpCode.BULLET:
            self.bullets.append({
                'x': packet.data.get('x', 400),
                'y': packet.data.get('y', 300),
                'dx': packet.data.get('dx', 0),
                'dy': packet.data.get('dy', 0),
                'owner': packet.sender_id
            })

            if packet.sender_id != self.client_id and self.shoot_sound:
                self.shoot_sound.play()

        elif packet.op_code == OpCode.HIT:
            target_id = packet.data.get('target_id')
            damage = packet.data.get('damage', 10)

            if target_id == self.client_id:
                self.player_health -= damage
                self.player_health = max(0, self.player_health)


                if self.hit_sound:
                    self.hit_sound.play()

                for _ in range(15):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(2, 6)
                    self.particles.append({
                        'x': self.player_pos[0],
                        'y': self.player_pos[1],
                        'vx': math.cos(angle) * speed,
                        'vy': math.sin(angle) * speed,
                        'color': (200, 0, 0),
                        'life': 30,
                        'size': random.randint(2, 5)
                    })

                if self.player_health <= 0:
                    if self.death_sound:
                        self.death_sound.play()

                    for _ in range(30):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(3, 8)
                        self.particles.append({
                            'x': self.player_pos[0],
                            'y': self.player_pos[1],
                            'vx': math.cos(angle) * speed,
                            'vy': math.sin(angle) * speed,
                            'color': (150, 0, 0),
                            'life': 50,
                            'size': random.randint(3, 7)
                        })

            elif target_id in self.other_players:
                self.other_players[target_id]['health'] -= damage
                self.other_players[target_id]['health'] = max(0, self.other_players[target_id]['health'])

                if target_id in self.other_players:
                    player_data = self.other_players[target_id]
                    for _ in range(10):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(2, 5)
                        self.particles.append({
                            'x': player_data['x'],
                            'y': player_data['y'],
                            'vx': math.cos(angle) * speed,
                            'vy': math.sin(angle) * speed,
                            'color': (200, 0, 0),
                            'life': 25,
                            'size': random.randint(2, 4)
                        })

        elif packet.op_code == OpCode.RESPAWN:
            player_id = packet.sender_id
            if player_id == self.client_id:
                self.player_health = 100
                if 'x' in packet.data and 'y' in packet.data:
                    self.player_pos = [packet.data.get('x', 400), packet.data.get('y', 300)]
                print("🤠 You respawned!")
            elif player_id in self.other_players:
                self.other_players[player_id]['health'] = 100
                if 'x' in packet.data and 'y' in packet.data:
                    self.other_players[player_id]['x'] = packet.data.get('x', 400)
                    self.other_players[player_id]['y'] = packet.data.get('y', 300)

        elif packet.op_code == OpCode.DISCONNECT:
            player_id = packet.sender_id
            if player_id in self.other_players:
                print(f"👋 Cowboy {player_id} left the desert")
                del self.other_players[player_id]

    def send_packet(self, op_code, data):
        if not self.connected or not self.client_id:
            return

        try:
            packet = GamePacket(op_code, self.client_id, data)
            self.socket.send(packet.to_json())
        except:
            self.connected = False

    def update_bullets(self):
        for bullet in self.bullets[:]:
            bullet['x'] += bullet['dx'] * 8
            bullet['y'] += bullet['dy'] * 8

            if (bullet['x'] < 0 or bullet['x'] > 800 or
                    bullet['y'] < 0 or bullet['y'] > 600):
                self.bullets.remove(bullet)

    def update_particles(self):
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += 0.1  # Gravity
            particle['life'] -= 1

            if particle['life'] <= 0:
                self.particles.remove(particle)

    def shoot_bullet(self, target_x, target_y):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot < self.shot_cooldown:
            return

        self.last_shot = current_time

        dx = target_x - self.player_pos[0]
        dy = target_y - self.player_pos[1]
        distance = max(0.1, math.sqrt(dx * dx + dy * dy))
        dx /= distance
        dy /= distance


        bullet_data = {
            'x': self.player_pos[0] + dx * 20,
            'y': self.player_pos[1] + dy * 20,
            'dx': dx,
            'dy': dy
        }


        self.send_packet(OpCode.ATTACK, bullet_data)


        self.bullets.append({
            'x': bullet_data['x'],
            'y': bullet_data['y'],
            'dx': dx,
            'dy': dy,
            'owner': self.client_id
        })

        if self.shoot_sound:
            self.shoot_sound.play()

        for _ in range(8):
            angle = random.uniform(math.atan2(dy, dx) - 0.3, math.atan2(dy, dx) + 0.3)
            speed = random.uniform(2, 5)
            self.particles.append({
                'x': bullet_data['x'],
                'y': bullet_data['y'],
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'color': (255, 200, 100),
                'life': 15,
                'size': random.randint(2, 4)
            })

    def draw_ui(self):
        health_width = max(0, int(self.player_health * 1.5))
        pygame.draw.rect(self.screen, (120, 80, 40), (20, 20, 154, 24))
        pygame.draw.rect(self.screen, (150, 100, 50), (22, 22, 150, 20))
        if self.player_health > 60:
            health_color = (0, 200, 0)
        elif self.player_health > 30:
            health_color = (255, 200, 0)
        else:
            health_color = (200, 0, 0)
            pulse = abs(math.sin(time.time() * 5)) * 50
            health_color = (200 + pulse, 0, 0)

        pygame.draw.rect(self.screen, health_color, (22, 22, health_width, 20))
        health_text = self.font_small.render(f"HEALTH: {self.player_health}", True, (255, 255, 200))
        self.screen.blit(health_text, (180, 22))
        pygame.draw.rect(self.screen, (200, 180, 140), (20, 60, 200, 40))
        pygame.draw.rect(self.screen, (150, 120, 90), (20, 60, 200, 40), 3)
        score_text = self.font_medium.render(f"BOUNTY: ${self.player_score}", True, (50, 30, 10))
        self.screen.blit(score_text, (30, 68))

        if self.client_id:
            id_text = self.font_small.render(f"COWBOY #{self.client_id}", True, (255, 255, 200))
            self.screen.blit(id_text, (20, 110))
        players_text = self.font_small.render(f"PLAYERS: {len(self.other_players) + 1}", True, (200, 200, 200))
        self.screen.blit(players_text, (20, 140))
        cooldown_percent = min(1.0, (pygame.time.get_ticks() - self.last_shot) / self.shot_cooldown)
        ammo_width = int(100 * cooldown_percent)

        pygame.draw.rect(self.screen, (80, 80, 80), (680, 20, 104, 20))
        pygame.draw.rect(self.screen, (100, 200, 255), (682, 22, ammo_width, 16))

        ammo_text = self.font_tiny.render("READY" if cooldown_percent >= 1.0 else "RELOADING",
                                          True, (255, 255, 200))
        self.screen.blit(ammo_text, (690, 24))
        pygame.draw.rect(self.screen, (150, 120, 90), (600, 50, 180, 120))
        pygame.draw.rect(self.screen, (120, 90, 60), (600, 50, 180, 120), 3)

        controls = [
            "WASD: MOVE",
            "MOUSE: AIM",
            "CLICK: SHOOT",
            "R: RESPAWN"
        ]

        for i, text in enumerate(controls):
            control_text = self.font_tiny.render(text, True, (255, 255, 200))
            self.screen.blit(control_text, (610, 60 + i * 25))

    def draw_connection_screen(self):
        self.draw_desert_background()
        title_shadow = self.font_large.render("DESERT DUEL", True, (100, 50, 0))
        title_text = self.font_large.render("DESERT DUEL", True, (255, 200, 100))
        self.screen.blit(title_shadow, (403, 103))
        self.screen.blit(title_text, (400, 100))

        subtitle = self.font_medium.render("RETRO SHOOTOUT", True, (255, 255, 200))
        self.screen.blit(subtitle, (400 - subtitle.get_width() // 2, 160))
        if self.connection_error:
            error_text = self.font_medium.render(f"ERROR: {self.connection_error}", True, (255, 100, 100))
            self.screen.blit(error_text, (400 - error_text.get_width() // 2, 220))
        else:
            status_text = self.font_medium.render("CONNECTING TO SERVER...", True, (255, 255, 100))
            self.screen.blit(status_text, (400 - status_text.get_width() // 2, 220))
        pygame.draw.rect(self.screen, (200, 180, 140, 200), (150, 280, 500, 200))
        pygame.draw.rect(self.screen, (150, 120, 90), (150, 280, 500, 200), 4)

        instructions = [
            "HOW TO PLAY:",
            "1. RUN server.py FIRST in another terminal",
            "2. PRESS R to connect/retry",
            "3. OPEN multiple clients for multiplayer duels",
            "4. ELIMINATE other cowboys to earn bounty",
            "",
            "YEEHAW! READY FOR A SHOOTOUT?"
        ]

        for i, text in enumerate(instructions):
            color = (50, 30, 10) if i == 0 else (80, 60, 40)
            inst_text = self.font_small.render(text, True, color)
            self.screen.blit(inst_text, (400 - inst_text.get_width() // 2, 300 + i * 30))
        if int(time.time() * 2) % 2 == 0:
            cowboy_text = self.font_medium.render("🤠 PRESS R TO RIDE IN! 🤠", True, (255, 200, 100))
            self.screen.blit(cowboy_text, (400 - cowboy_text.get_width() // 2, 500))

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            mouse_pos = pygame.mouse.get_pos()
            mouse_world_x = mouse_pos[0] + self.camera_x
            mouse_world_y = mouse_pos[1] + self.camera_y

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        if not self.connected:
                            if self.connect_to_server():
                                threading.Thread(target=self.receive_messages, daemon=True).start()
                        elif self.player_health <= 0:
                            self.send_packet(OpCode.RESPAWN, {
                                'x': random.randint(100, 700),
                                'y': random.randint(100, 500)
                            })

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.connected and self.player_health > 0:
                            self.shoot_bullet(mouse_world_x, mouse_world_y)
            if self.connected and self.player_health > 0:
                if mouse_world_x > self.player_pos[0]:
                    self.player_direction = 'right'
                else:
                    self.player_direction = 'left'
                move_x, move_y = 0, 0
                speed = 200 * dt

                keys = pygame.key.get_pressed()
                if keys[pygame.K_a]: move_x -= speed
                if keys[pygame.K_d]: move_x += speed
                if keys[pygame.K_w]: move_y -= speed
                if keys[pygame.K_s]: move_y += speed

                if move_x != 0 or move_y != 0:
                    self.player_pos[0] += move_x
                    self.player_pos[1] += move_y
                    self.player_pos[0] = max(50, min(750, self.player_pos[0]))
                    self.player_pos[1] = max(50, min(550, self.player_pos[1]))
                    self.send_packet(OpCode.MOVE, {
                        'x': self.player_pos[0],
                        'y': self.player_pos[1],
                        'health': self.player_health,
                        'direction': self.player_direction
                    })

            self.update_camera()
            self.update_bullets()
            self.update_particles()
            if self.connected:
                self.draw_desert_background()
                for player_id, player_data in self.other_players.items():
                    if player_data['health'] > 0:
                        self.draw_player(
                            player_data['x'],
                            player_data['y'],
                            player_id,
                            is_current_player=False
                        )

                if self.client_id and self.player_health > 0:
                    self.draw_player(
                        self.player_pos[0],
                        self.player_pos[1],
                        self.client_id,
                        is_current_player=True
                    )

                for bullet in self.bullets:
                    self.draw_bullet(bullet['x'], bullet['y'], bullet['dx'], bullet['dy'])

                for particle in self.particles:
                    pygame.draw.circle(
                        self.screen,
                        particle['color'],
                        (int(particle['x'] - self.camera_x),
                         int(particle['y'] - self.camera_y)),
                        particle['size']
                    )


                self.draw_ui()
                pygame.draw.circle(self.screen, (255, 255, 255), mouse_pos, 3, 1)
                pygame.draw.line(self.screen, (255, 255, 255),
                                 (mouse_pos[0] - 8, mouse_pos[1]),
                                 (mouse_pos[0] + 8, mouse_pos[1]), 1)
                pygame.draw.line(self.screen, (255, 255, 255),
                                 (mouse_pos[0], mouse_pos[1] - 8),
                                 (mouse_pos[0], mouse_pos[1] + 8), 1)
                if self.player_health <= 0:
                    death_overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
                    death_overlay.fill((0, 0, 0, 150))
                    self.screen.blit(death_overlay, (0, 0))

                    death_text = self.font_large.render("YOU WERE ELIMINATED!", True, (255, 50, 50))
                    self.screen.blit(death_text, (400 - death_text.get_width() // 2, 250))

                    respawn_text = self.font_medium.render("PRESS R TO RESPAWN", True, (255, 255, 100))
                    self.screen.blit(respawn_text, (400 - respawn_text.get_width() // 2, 320))
            else:
                self.draw_connection_screen()

            pygame.display.flip()
        if hasattr(self, 'socket'):
            try:
                if self.connected:
                    self.send_packet(OpCode.DISCONNECT, {'reason': 'quit'})
                self.socket.close()
            except:
                pass
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    print("=" * 60)
    print("🤠 DESERT DUEL - RETRO SHOOTOUT")
    print("=" * 60)
    print("INSTRUCTIONS:")
    print("1. First run: python server.py")
    print("2. Then run: python game_client.py")
    print("3. Open multiple windows for multiplayer duels")
    print("4. Use mouse to aim, click to shoot")
    print("=" * 60)
    print("FEATURES:")
    print("- Retro cowboy avatars with guns")
    print("- Desert mountain background with cactus")
    print("- Bullet physics with trails")
    print("- Health system and score tracking")
    print("- Real-time multiplayer combat")
    print("=" * 60)

    client = GameClient()
    client.run()