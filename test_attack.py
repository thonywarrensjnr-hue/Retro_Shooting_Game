import socket
import json
import time


def test_attack():
    print("🔍 Testing Attack/Damage System...")
    print("=" * 50)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 5555))
        print("✅ Connected to server")

        join_packet = {
            "op_code": "JOIN",
            "sender_id": 0,
            "data": {}
        }
        sock.send(json.dumps(join_packet).encode())
        print("📤 Sent JOIN packet")
        response = sock.recv(1024)
        if response:
            response_data = json.loads(response.decode())
            print(f"📥 Server JOIN response:")
            print(f"   OpCode: {response_data.get('op_code')}")
            print(f"   Sender ID: {response_data.get('sender_id')}")
            print(f"   Data: {response_data.get('data')}")
            player_id = response_data['data'].get('assigned_id')
            print(f"🎮 Assigned Player ID: {player_id}")

            time.sleep(1)

            attack_packet = {
                "op_code": "ATTACK",
                "sender_id": player_id,
                "data": {
                    "x": 400,  
                    "y": 300,  
                    "dx": 1.0,  
                    "dy": 0.0  
                }
            }
            sock.send(json.dumps(attack_packet).encode())
            print("📤 Sent ATTACK (bullet) packet")
            print(f"   Bullet from: ({400}, {300})")
            print(f"   Direction: ({1.0}, {0.0})")

            time.sleep(0.5)
            
            hit_packet = {
                "op_code": "HIT",
                "sender_id": player_id,
                "data": {
                    "target_id": 2,  
                    "damage": 10,
                    "shooter_id": player_id
                }
            }
            sock.send(json.dumps(hit_packet).encode())
            print("📤 Sent HIT packet")
            print(f"   Target: Player 2")
            print(f"   Damage: 10")
            print(f"   Shooter: Player {player_id}")

            sock.settimeout(1.0)
            try:
                while True:
                    data = sock.recv(1024)
                    if data:
                        response = json.loads(data.decode())
                        print(f"📥 Server broadcast: {response.get('op_code')}")
                    else:
                        break
            except socket.timeout:
                print("⏰ No more responses from server")

        else:
            print("❌ No response from server")

        sock.close()
        print("✅ Test complete")
        print("\n💡 Next steps:")
        print("1. Run two game clients")
        print("2. Shoot at each other")
        print("3. Check if health bars reduce")
        print("4. Check server console for hit messages")

    except ConnectionRefusedError:
        print("❌ Cannot connect to server")
        print("\n💡 Make sure:")
        print("1. Server is running: python server.py")
        print("2. Server is on 127.0.0.1:5555")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_attack()
