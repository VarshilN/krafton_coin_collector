import asyncio
import websockets
import json
import random
from common import encode, decode

TICK_RATE = 30
LATENCY = 0.2
MAP_SIZE = 500
PLAYER_SPEED = 120
PLAYER_RADIUS = 20
COIN_RADIUS = 12

players = {}         # pid -> state
connections = {}     # ws -> pid
coins = []
next_coin_id = 1


async def delayed_send(ws, data):
    await asyncio.sleep(LATENCY)
    await ws.send(data)


async def delayed_recv(ws):
    await asyncio.sleep(LATENCY)
    return await ws.recv()


async def handle_client(ws):
    """Handle a single client connection (websockets>=12 only passes ws)."""
    global next_coin_id

    pid = str(id(ws))
    connections[ws] = pid

    players[pid] = {
        "x": random.randint(0, MAP_SIZE),
        "y": random.randint(0, MAP_SIZE),
        "vx": 0,
        "vy": 0,
        "score": 0
    }

    print("Player joined:", pid)

    try:
        while True:
            msg = await delayed_recv(ws)
            data = decode(msg)

            if data["type"] == "input":
                players[pid]["vx"] = data["vx"]
                players[pid]["vy"] = data["vy"]

    except websockets.ConnectionClosed:
        print("Player disconnected:", pid)

    finally:
        if ws in connections:
            del connections[ws]
        if pid in players:
            del players[pid]


async def game_loop():
    global next_coin_id

    while True:
        dt = 1.0 / TICK_RATE

        # Movement
        for p in players.values():
            p["x"] += p["vx"] * PLAYER_SPEED * dt
            p["y"] += p["vy"] * PLAYER_SPEED * dt
            p["x"] = max(0, min(MAP_SIZE, p["x"]))
            p["y"] = max(0, min(MAP_SIZE, p["y"]))

        # Coin collision
        to_remove = []
        for coin in coins:
            for p in players.values():
                dx = p["x"] - coin["x"]
                dy = p["y"] - coin["y"]
                if dx*dx + dy*dy <= (PLAYER_RADIUS + COIN_RADIUS)**2:
                    p["score"] += 1
                    to_remove.append(coin)
                    break

        for c in to_remove:
            if c in coins:
                coins.remove(c)

        # Coin spawn
        if random.random() < 1 / (TICK_RATE * 5):
            coins.append({
                "id": next_coin_id,
                "x": random.randint(0, MAP_SIZE),
                "y": random.randint(0, MAP_SIZE)
            })
            next_coin_id += 1

        # Broadcast
        state = encode({
            "type": "state",
            "players": players,
            "coins": coins
        })

        dead = []
        for ws in list(connections.keys()):
            try:
                await delayed_send(ws, state)
            except:
                dead.append(ws)

        # Cleanup
        for ws in dead:
            pid = connections.get(ws)
            if pid in players:
                del players[pid]
            if ws in connections:
                del connections[ws]

        await asyncio.sleep(dt)


async def main():
    print("Server running on ws://localhost:8000")
    async with websockets.serve(handle_client, "localhost", 8000):
        await game_loop()


asyncio.run(main())
