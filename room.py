import threading
from protocol import OpCode, GamePacket


class GameRoom:
    def __init__(self, room_id):
        self.room_id = room_id
        self.players = {}
        self.game_state = {"players": {}}
        self.lock = threading.Lock()
        print(f"Room '{room_id}' created")

    def add_player(self, player_id, client_socket):
        with self.lock:
            self.players[player_id] = client_socket
            self.game_state["players"][player_id] = {"x": 375, "y": 275, "hp": 100, "score": 0}
        print(f"Player {player_id} joined Room {self.room_id}")

    def remove_player(self, player_id):
        with self.lock:
            if player_id in self.players:
                del self.players[player_id]
            if player_id in self.game_state["players"]:
                del self.game_state["players"][player_id]
        print(f"Player {player_id} removed from Room {self.room_id}")

    def broadcast(self, packet, exclude_id=None):
        if not self.players:
            return

        message = packet.to_json()
        dead_players = []

        for p_id, socket in self.players.items():
            if p_id != exclude_id:
                try:
                    socket.send(message)
                except Exception as e:
                    print(f"Failed to send to {p_id}: {e}")
                    dead_players.append(p_id)

        for p_id in dead_players:
            self.remove_player(p_id)

    def handle_move(self, player_id, data):
        with self.lock:
            if player_id in self.game_state["players"]:
                self.game_state["players"][player_id].update(data)
        update_packet = GamePacket(OpCode.MOVE, player_id, data)
        self.broadcast(update_packet, exclude_id=player_id)

    def handle_hit(self, attacker_id, data):
        target_id = data.get("target_id")
        damage = data.get("damage", 10)

        print(f"Room: Player {attacker_id} hits Player {target_id} for {damage} damage")

        with self.lock:
            if target_id in self.game_state["players"]:
                if "hp" not in self.game_state["players"][target_id]:
                    self.game_state["players"][target_id]["hp"] = 100
                self.game_state["players"][target_id]["hp"] -= damage
                self.game_state["players"][target_id]["hp"] = max(0, self.game_state["players"][target_id]["hp"])

                print(f"Player {target_id} health now: {self.game_state['players'][target_id]['hp']}")
                if self.game_state["players"][target_id]["hp"] <= 0:
                    print(f"Player {target_id} has been defeated!")
        hit_packet = GamePacket(
            OpCode.HIT,
            attacker_id,
            {
                'attacker_id': attacker_id,
                'target_id': target_id,
                'damage': damage,
                'target_health': self.game_state["players"][target_id]["hp"] if target_id in self.game_state[
                    "players"] else 0
            }
        )

        self.broadcast(hit_packet)

    def handle_collect(self, player_id, data):
        with self.lock:
            if player_id in self.game_state["players"]:
                if "score" not in self.game_state["players"][player_id]:
                    self.game_state["players"][player_id]["score"] = 0
                points = data.get('points', 10)
                self.game_state["players"][player_id]["score"] += points

        collect_packet = GamePacket(
            OpCode.COLLECT,
            player_id,
            {
                'player_id': player_id,
                'points': points,
                'total_score': self.game_state["players"][player_id]["score"]
            }
        )
        self.broadcast(collect_packet, exclude_id=player_id)