import socket
import threading
import json
import time
import random
from protocol import OpCode, GamePacket

HOST = '127.0.0.1'
PORT = 5555


class GameServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(5)

        self.clients = {}
        self.next_player_id = 1
        self.running = True

        print(f"🤠 Desert Arena Server started on {HOST}:{PORT}")
        print("Waiting for cowboys to connect...")

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
                del self.clients[player_id]
            for other_id, other_data in self.clients.items():
                disconnect_packet = GamePacket(OpCode.DISCONNECT, player_id, {
                    'player_id': player_id,
                    'reason': 'left the desert'
                })
                try:
                    other_data['socket'].send(disconnect_packet.to_json())
                except:
                    pass

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
                            pass

        elif packet.op_code == OpCode.ATTACK:
            bullet_packet = GamePacket(OpCode.BULLET, player_id, packet.data)
            for other_id, other_data in self.clients.items():
                if other_id != player_id:
                    try:
                        other_data['socket'].send(bullet_packet.to_json())
                    except:
                        pass

        elif packet.op_code == OpCode.HIT:
            target_id = packet.data.get('target_id')
            damage = packet.data.get('damage', 10)

            if target_id in self.clients:
                self.clients[target_id]['health'] -= damage
                self.clients[target_id]['health'] = max(0, self.clients[target_id]['health'])
                hit_packet = GamePacket(OpCode.HIT, player_id, {
                    'attacker_id': player_id,
                    'target_id': target_id,
                    'damage': damage
                })

                if player_id in self.clients:
                    try:
                        self.clients[player_id]['socket'].send(hit_packet.to_json())
                    except:
                        pass

                try:
                    self.clients[target_id]['socket'].send(hit_packet.to_json())
                except:
                    pass

                for other_id, other_data in self.clients.items():
                    if other_id not in [player_id, target_id]:
                        try:
                            other_data['socket'].send(hit_packet.to_json())
                        except:
                            pass

                if self.clients[target_id]['health'] <= 0:
                    if player_id in self.clients:
                        self.clients[player_id]['score'] += 100
                        print(f"🎯 Cowboy {player_id} eliminated Cowboy {target_id}!")
                    death_packet = GamePacket(OpCode.RESPAWN, target_id, {
                        'player_id': target_id,
                        'health': 0
                    })
                    for other_id, other_data in self.clients.items():
                        try:
                            other_data['socket'].send(death_packet.to_json())
                        except:
                            pass

        elif packet.op_code == OpCode.RESPAWN:
            if player_id in self.clients:
                spawn_x = packet.data.get('x', random.randint(100, 700))
                spawn_y = packet.data.get('y', random.randint(100, 500))

                self.clients[player_id]['x'] = spawn_x
                self.clients[player_id]['y'] = spawn_y
                self.clients[player_id]['health'] = 100
                respawn_packet = GamePacket(OpCode.RESPAWN, player_id, {
                    'x': spawn_x,
                    'y': spawn_y,
                    'health': 100
                })

                for other_id, other_data in self.clients.items():
                    if other_id != player_id:
                        try:
                            other_data['socket'].send(respawn_packet.to_json())
                        except:
                            pass

        elif packet.op_code == OpCode.PING:
            pong_packet = GamePacket(OpCode.PING, 0, {'pong': True})
            try:
                self.clients[player_id]['socket'].send(pong_packet.to_json())
            except:
                pass

    def start(self):
        print("🤠 Server is running. Press Ctrl+C to stop.")
        print(f"👥 Current players: {len(self.clients)}")

        try:
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    client_socket.settimeout(1.0)

                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()

                    print(f"👥 Total players connected: {len(self.clients)}")

                except KeyboardInterrupt:
                    print("\n🌵 Shutting down server...")
                    self.running = False
                    break
                except Exception as e:
                    print(f"  Accept error: {e}")
                    continue

        finally:
            for player_id, client_data in list(self.clients.items()):
                try:
                    client_data['socket'].close()
                except:
                    pass

            self.server_socket.close()
            print("🌵 Server stopped.")


if __name__ == "__main__":
    server = GameServer()
    server.start()