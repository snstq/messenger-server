import asyncio
import json
import uuid
import time
from datetime import datetime
from typing import Dict, Set
import websockets
import aiosqlite

import os

DB_PATH = "messenger.db"
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8765))

online_users: Dict[str, websockets.WebSocketServerProtocol] = {}
user_connections: Dict[str, Set[websockets.WebSocketServerProtocol]] = {}

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                nickname TEXT NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                sender_id TEXT NOT NULL,
                receiver_id TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                is_delivered INTEGER DEFAULT 0,
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (receiver_id) REFERENCES users(id)
            )
        """)
        await db.commit()

async def register(username: str, nickname: str, password: str) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            user_id = str(uuid.uuid4())[:8]
            await db.execute(
                "INSERT INTO users (id, username, nickname, password) VALUES (?, ?, ?, ?)",
                (user_id, username, nickname, password)
            )
            await db.commit()
            return {"success": True, "user_id": user_id, "username": username, "nickname": nickname}
        except aiosqlite.IntegrityError:
            return {"success": False, "error": "用户名已存在"}

async def login(username: str, password: str) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, username, nickname FROM users WHERE username = ? AND password = ?",
            (username, password)
        )
        row = await cursor.fetchone()
        if row:
            return {"success": True, "user_id": row[0], "username": row[1], "nickname": row[2]}
        return {"success": False, "error": "用户名或密码错误"}

async def get_user_by_id(user_id: str) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, username, nickname FROM users WHERE id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            return {"id": row[0], "username": row[1], "nickname": row[2]}
        return None

async def search_users(query: str, exclude_id: str = None) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        if exclude_id:
            cursor = await db.execute(
                "SELECT id, username, nickname FROM users WHERE (username LIKE ? OR nickname LIKE ?) AND id != ?",
                (f"%{query}%", f"%{query}%", exclude_id)
            )
        else:
            cursor = await db.execute(
                "SELECT id, username, nickname FROM users WHERE username LIKE ? OR nickname LIKE ?",
                (f"%{query}%", f"%{query}%")
            )
        rows = await cursor.fetchall()
        return [{"id": r[0], "username": r[1], "nickname": r[2]} for r in rows]

async def save_message(sender_id: str, receiver_id: str, content: str) -> dict:
    msg_id = str(uuid.uuid4())[:8]
    timestamp = int(time.time() * 1000)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (id, sender_id, receiver_id, content, timestamp) VALUES (?, ?, ?, ?, ?)",
            (msg_id, sender_id, receiver_id, content, timestamp)
        )
        await db.commit()
    return {"id": msg_id, "sender_id": sender_id, "receiver_id": receiver_id, "content": content, "timestamp": timestamp}

async def get_offline_messages(user_id: str) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, sender_id, receiver_id, content, timestamp FROM messages WHERE receiver_id = ? AND is_delivered = 0 ORDER BY timestamp ASC",
            (user_id,)
        )
        rows = await cursor.fetchall()
        messages = [{"id": r[0], "sender_id": r[1], "receiver_id": r[2], "content": r[3], "timestamp": r[4]} for r in rows]
        await db.execute(
            "UPDATE messages SET is_delivered = 1 WHERE receiver_id = ? AND is_delivered = 0",
            (user_id,)
        )
        await db.commit()
    return messages

async def get_online_users() -> list:
    return list(online_users.keys())

async def send_to_user(user_id: str, message: dict):
    if user_id in user_connections:
        for ws in user_connections[user_id]:
            try:
                await ws.send(json.dumps(message))
            except:
                pass

async def handle_message(websocket: websockets.WebSocketServerProtocol, data: dict):
    msg_type = data.get("type")
    
    if msg_type == "register":
        result = await register(data["username"], data.get("nickname", data["username"]), data["password"])
        await websocket.send(json.dumps({"type": "register_result", **result}))
        
    elif msg_type == "login":
        result = await login(data["username"], data["password"])
        if result["success"]:
            user_id = result["user_id"]
            if user_id not in user_connections:
                user_connections[user_id] = set()
            user_connections[user_id].add(websocket)
            online_users[user_id] = websocket
            
            await websocket.send(json.dumps({"type": "login_result", **result}))
            
            offline_msgs = await get_offline_messages(user_id)
            if offline_msgs:
                await websocket.send(json.dumps({"type": "offline_messages", "messages": offline_msgs}))
            
            await broadcast_online_status()
        else:
            await websocket.send(json.dumps({"type": "login_result", **result}))
    
    elif msg_type == "search_users":
        user_id = data.get("user_id")
        query = data.get("query", "")
        results = await search_users(query, user_id)
        await websocket.send(json.dumps({"type": "search_results", "users": results}))
    
    elif msg_type == "send_message":
        sender_id = data["sender_id"]
        receiver_id = data["receiver_id"]
        content = data["content"]
        
        msg = await save_message(sender_id, receiver_id, content)
        
        if receiver_id in user_connections:
            await send_to_user(receiver_id, {"type": "new_message", "message": msg})
            await websocket.send(json.dumps({"type": "message_sent", "message": msg, "delivered": True}))
        else:
            await websocket.send(json.dumps({"type": "message_sent", "message": msg, "delivered": False}))
    
    elif msg_type == "get_online_users":
        users = await get_online_users()
        await websocket.send(json.dumps({"type": "online_users", "user_ids": users}))

async def broadcast_online_status():
    online_list = list(online_users.keys())
    for user_id, connections in user_connections.items():
        for ws in connections:
            try:
                await ws.send(json.dumps({"type": "online_users", "user_ids": online_list}))
            except:
                pass

async def handler(websocket: websockets.WebSocketServerProtocol):
    user_id = None
    try:
        async for message in websocket:
            data = json.loads(message)
            await handle_message(websocket, data)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        for uid, connections in list(user_connections.items()):
            if websocket in connections:
                connections.remove(websocket)
                if not connections:
                    del user_connections[uid]
                    if uid in online_users:
                        del online_users[uid]
                break
        await broadcast_online_status()

async def main():
    await init_db()
    print(f"Messenger Server started on ws://{HOST}:{PORT}")
    async with websockets.serve(handler, HOST, PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
