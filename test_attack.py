import socket
import json


def test_attack():
    print("🔍 Testing Attack System...")
    print("=" * 50)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 5555))
        print("✅ Connected to server")
        join_packet = {
            "op_code": 0,
            "sender_id": 0,
            "data": {}
        }
        sock.send(json.dumps(join_packet).encode())

        response = sock.recv(1024)
        print(f"📥 Server response: {response}")

        attack_packet = {
            "op_code": 3,
            "sender_id": 1,
            "data": {
                "target_id": 2,
                "damage": 10
            }
        }
        sock.send(json.dumps(attack_packet).encode())
        print("📤 Sent ATTACK packet")

        sock.close()
        print("✅ Test complete")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure:")
        print("1. Server is running: python server.py")
        print("2. Server handles ATTACK opcode (op_code=3)")
        print("3. Protocol.py has ATTACK = 3")


if __name__ == "__main__":
    test_attack()