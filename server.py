import socket
import threading
import json
import time
import random
import sqlite3
from protocol import OpCode, GamePacket

HOST = '127.0.0.1'
PORT = 5555
DATABASE_NAME = "game_data.db"


class GameServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(5)

        self.clients = {}
        self.next_player_id = 1
        self.running = True


        self.init_db()

        print(f"🤠 Desert Arena Server started on {HOST}:{PORT}")
        print("Waiting for cowboys to connect...")

    def init_db(self):
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    kills INTEGER DEFAULT 0,
                    deaths INTEGER DEFAULT 0,
                    high_score INTEGER DEFAULT 0
                )
            ''')
            conn.commit()
            print("📊 Database initialized")

    def save_score(self, username, score):
        try:
            with sqlite3.connect(DATABASE_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE players 
                    SET high_score = MAX(high_score, ?) 
                    WHERE username = ?
                ''', (score, username))
                conn.commit()
                print(f"💾 Saved score for {username}: {score}")
        except Exception as e:
            print(f"❌ Error saving score: {e}")

    def get_leaderboard(self, limit=10):
        try:
            with sqlite3.connect(DATABASE_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT username, high_score 
                    FROM players 
                    ORDER BY high_score DESC 
                    LIMIT ?
                ''', (limit,))
                return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error getting leaderboard: {e}")
            return []

    def handle_client(self, client_socket, client_address):
        player_id = self.next_player_id
        self.next_player_id += 1

        print(f"🤠 Cowboy {player_id} connected from {client_address}")

        spawn_x = random.randint(100, 700)
        spawn_y = random.randint(100, 500)

        self.clients[player_id] = {
            'socket': client_socket,
            'address': client_address,
            'x': spawn_x,
            'y': spawn_y,
            'health': 100,
            'score': 0,  
            'total_score': 0,  
            'username': f'Player_{player_id}',  
            'kills': 0,
            'deaths': 0,
            'direction': 'right',
            'last_seen': time.time()
        }

    
        join_response = GamePacket(OpCode.JOIN, 0, {
            'assigned_id': player_id,
            'spawn_x': spawn_x,
            'spawn_y': spawn_y
        })
        client_socket.send(join_response.to_json())
        print(f"  Sent JOIN response to Cowboy {player_id}")

        print(f"  Sending {len(self.clients) - 1} existing players to Cowboy {player_id}")
        for other_id, other_data in self.clients.items():
            if other_id != player_id:
                existing_player_packet = GamePacket(OpCode.MOVE, other_id, {
                    'x': other_data['x'],
                    'y': other_data['y'],
                    'health': other_data['health'],
                    'direction': other_data['direction']
                })
                try:
                    client_socket.send(existing_player_packet.to_json())
                    print(f"  Sent player {other_id} to new player {player_id}")
                except:
                    print(f"  Failed to send player {other_id} to new player {player_id}")

        print(f"  Broadcasting new player {player_id} to {len(self.clients) - 1} existing players")
        for other_id, other_data in self.clients.items():
            if other_id != player_id:
                new_player_packet = GamePacket(OpCode.MOVE, player_id, {
                    'x': spawn_x,
                    'y': spawn_y,
                    'health': 100,
                    'direction': 'right'
                })
                try:
                    other_data['socket'].send(new_player_packet.to_json())
                    print(f"  Sent new player {player_id} to player {other_id}")
                except:
                    print(f"  Failed to send new player {player_id} to player {other_id}")

        try:
            while self.running:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        print(f"  Cowboy {player_id} disconnected (no data)")
                        break

                    packet = GamePacket.from_json(data)
                    if packet:
                        self.handle_packet(player_id, packet)
                    else:
                        print(f"  Invalid packet from Cowboy {player_id}")

                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"  Error from Cowboy {player_id}: {e}")
                    break

        except Exception as e:
            print(f"  Exception in handle_client for Cowboy {player_id}: {e}")
        finally:
            print(f"🤠 Cowboy {player_id} disconnected")

            if player_id in self.clients:
                player_data = self.clients[player_id]
                total_score = player_data['total_score'] + player_data['score']
                self.save_score(player_data['username'], total_score)
                print(f"💾 Saved score for {player_data['username']}: {total_score}")

                for other_id, other_data in self.clients.items():
                    if other_id != player_id:
                        disconnect_packet = GamePacket(OpCode.DISCONNECT, player_id, {
                            'player_id': player_id,
                            'reason': 'left the desert'
                        })
                        try:
                            other_data['socket'].send(disconnect_packet.to_json())
                        except:
                            pass

                del self.clients[player_id]

            try:
                client_socket.close()
            except:
                pass

    def handle_packet(self, player_id, packet):
        if packet.op_code == OpCode.MOVE:
            if player_id in self.clients:
                self.clients[player_id]['x'] = packet.data.get('x', self.clients[player_id]['x'])
                self.clients[player_id]['y'] = packet.data.get('y', self.clients[player_id]['y'])
                self.clients[player_id]['health'] = packet.data.get('health', self.clients[player_id]['health'])
                self.clients[player_id]['direction'] = packet.data.get('direction',
                                                                       self.clients[player_id]['direction'])
                self.clients[player_id]['last_seen'] = time.time()

                for other_id, other_data in self.clients.items():
                    if other_id != player_id:
                        move_packet = GamePacket(OpCode.MOVE, player_id, {
                            'x': self.clients[player_id]['x'],
                            'y': self.clients[player_id]['y'],
                            'health': self.clients[player_id]['health'],
                            'direction': self.clients[player_id]['direction']
                        })
                        try:
                            other_data['socket'].send(move_packet.to_json())
                        except:
                            print(f"  Failed to broadcast MOVE from player {player_id} to player {other_id}")

        elif packet.op_code == OpCode.ATTACK:
            bullet_data = packet.data.copy()
            bullet_packet = GamePacket(OpCode.BULLET, player_id, bullet_data)

            for other_id, other_data in self.clients.items():
                try:
                    other_data['socket'].send(bullet_packet.to_json())
                except:
                    print(f"  Failed to broadcast BULLET from player {player_id} to player {other_id}")

        elif packet.op_code == OpCode.HIT:
            target_id = packet.data.get('target_id')
            damage = packet.data.get('damage', 10)
            shooter_id = packet.data.get('shooter_id', player_id)

            print(f"🎯 Player {shooter_id} hit player {target_id} for {damage} damage")
            if target_id in self.clients:
                self.clients[target_id]['health'] -= damage

                if self.clients[target_id]['health'] <= 0:
                    self.clients[target_id]['health'] = 0

                    self.clients[target_id]['deaths'] += 1
                    print(f"💀 Player {target_id} was eliminated by player {shooter_id}")

                    if shooter_id in self.clients:
                        self.clients[shooter_id]['kills'] += 1
                        self.clients[shooter_id]['score'] += 100
                        print(
                            f"💰 Player {shooter_id} earned 100 bounty! Total score: ${self.clients[shooter_id]['score']}")


                        score_packet = GamePacket(OpCode.SCORE_UPDATE, 0, {
                            'player_id': shooter_id,
                            'score': self.clients[shooter_id]['score'],
                            'kills': self.clients[shooter_id]['kills']
                        })
                        try:
                            self.clients[shooter_id]['socket'].send(score_packet.to_json())
                        except:
                            print(f"  Failed to send score update to player {shooter_id}")

            hit_packet = GamePacket(OpCode.HIT, player_id, {
                'target_id': target_id,
                'damage': damage,
                'shooter_id': shooter_id
            })

            for other_id, other_data in self.clients.items():
                try:
                    other_data['socket'].send(hit_packet.to_json())
                except:
                    print(f"  Failed to broadcast HIT to player {other_id}")

        elif packet.op_code == OpCode.RESPAWN:
            if player_id in self.clients:
                self.clients[player_id]['health'] = 100
                self.clients[player_id]['x'] = random.randint(100, 700)
                self.clients[player_id]['y'] = random.randint(100, 500)
                self.clients[player_id]['direction'] = 'right'

                print(
                    f"🔄 Player {player_id} respawned at ({self.clients[player_id]['x']}, {self.clients[player_id]['y']})")

                respawn_packet = GamePacket(OpCode.RESPAWN, player_id, {
                    'x': self.clients[player_id]['x'],
                    'y': self.clients[player_id]['y'],
                    'health': 100
                })

                for other_id, other_data in self.clients.items():
                    if other_id != player_id:
                        try:
                            other_data['socket'].send(respawn_packet.to_json())
                        except:
                            print(f"  Failed to broadcast RESPAWN for player {player_id} to player {other_id}")

    def run(self):
        print("🤠 Server is running. Press Ctrl+C to stop.")
        try:
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    client_socket.settimeout(0.1)
                    client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
                    client_thread.daemon = True
                    client_thread.start()
                    print(f"🤠 New connection from {client_address}")
                except socket.timeout:
                    continue
                except KeyboardInterrupt:
                    print("\n🤠 Server shutting down...")
                    self.running = False
                    break
        except KeyboardInterrupt:
            print("\n🤠 Server shutting down...")
        finally:
            self.server_socket.close()
            print("🤠 Server stopped.")


if __name__ == "__main__":
    server = GameServer()
    server.run()
