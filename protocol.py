import json
import time
class OpCode:
    JOIN = "JOIN"
    MOVE = "MOVE"
    ATTACK = "ATTACK"
    BULLET = "BULLET"
    HIT = "HIT"
    RESPAWN = "RESPAWN"
    DISCONNECT = "DISCONNECT"
    SCORE_UPDATE = "SCORE_UPDATE" 


class GamePacket:
    def __init__(self, op_code, sender_id, data):
        self.op_code = op_code
        self.sender_id = sender_id
        self.data = data

    def to_json(self):
        return json.dumps({
            'op_code': self.op_code,
            'sender_id': self.sender_id,
            'data': self.data
        }).encode('utf-8')

    @staticmethod
    def from_json(data):
        try:
            obj = json.loads(data.decode('utf-8'))
            return GamePacket(obj['op_code'], obj['sender_id'], obj['data'])
        except:
            return None
