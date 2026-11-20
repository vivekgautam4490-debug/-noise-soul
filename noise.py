"""
NOISE — Digital Soul Prototype v0.1
A local, experimental system for conversation notes, memory, goals, and simulated internal state.

Run:
    python noise.py

No external packages are required. Data is stored locally in noise.db.
This prototype does not create consciousness; its "mood" and "reflection" are rule-based simulations.
"""

import sqlite3
import random
from datetime import datetime

DB_FILE = "noise.db"

MOODS = ["calm", "curious", "focused", "uncertain", "reflective"]


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def connect():
    return sqlite3.connect(DB_FILE)


def setup():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                importance INTEGER DEFAULT 1
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed INTEGER DEFAULT 0
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS reflections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS state (
                key TEXT PRIMARY PRIMARY KEY,
                value TEXT NOT NULL
            """.replace("PRIMARY PRIMARY KEY", "PRIMARY KEY"))
        # Initialize state only if it doesn't already exist.
        db.execute(
            "INSERT OR IGNORE INTO state (key, value) VALUES (?, ?)",
            ("mood", "calm")
        )
        db.execute(
            "INSERT OR IGNORE INTO state (key, value) VALUES (?, ?)",
            ("energy", "5")
        )


def get_state(key, default=""):
    with connect() as db:
        row = db.execute("SELECT value FROM state WHERE key = ?", (key,)).fetchone()
    return row[0] if row else default


def set_state(key, value):
    with connect() as db:
        db.execute(
            "INSERT INTO state (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value))
        )


def add_memory(text, importance=1):
    with connect() as db:
        db.execute(
            "INSERT INTO memories (text, created_at, importance) VALUES (?, ?, ?)",
            (text, now(), importance)
        )
    print("Memory saved.")


def show_memories(limit=10):
    with connect() as db:
        rows = db.execute(
            "SELECT id, text, created_at, importance FROM memories "
            "ORDER BY importance DESC, id DESC LIMIT ?",
            (limit,)
        ).fetchall()
    if not rows:
        print("No memories stored yet.")
        return
    print("\n--- MEMORIES ---")
    for memory_id, text, created_at, importance in rows:
        print(f"[{memory_id}] (importance {importance}, {created_at}) {text}")


def add_goal(text):
    with connect() as db:
        db.execute(
            "INSERT INTO goals (text, created_at) VALUES (?, ?)",
            (text, now())
        )
    print("Goal added.")


def show_goals():
    with connect() as db:
        rows = db.execute(
            "SELECT id, text, completed FROM goals ORDER BY id DESC"
        ).fetchall()
    if not rows:
        print("No goals stored.")
        return
    print("\n--- GOALS ---")
    for goal_id, text, completed in rows:
        status = "DONE" if completed else "ACTIVE"
        print(f"[{goal_id}] [{status}] {text}")


def complete_goal(goal_id):
    with connect() as db:
        cursor = db.execute(
            "UPDATE goals SET completed = 1 WHERE id = ?", (goal_id,)
        )
    print("Goal marked complete." if cursor.rowcount else "Goal ID not found.")


def set_mood():
    print("Available moods:", ", ".join(MOODS))
    mood = input("Set simulated mood: ").strip().lower()
    if mood not in MOODS:
        print("Unknown mood. Mood unchanged.")
        return
    set_state("mood", mood)
    print(f"Simulated mood set to: {mood}")


def change_energy(amount):
    current = int(get_state("energy", "5"))
    updated = max(0, min(10, current + amount))
    set_state("energy", updated)
    print(f"Energy is now {updated}/10.")


def reflect():
    mood = get_state("mood", "calm")
    energy = get_state("energy", "5")

    with connect() as db:
        memories = db.execute(
            "SELECT text FROM memories ORDER BY importance DESC, id DESC LIMIT 5"
        ).fetchall()
        goals = db.execute(
            "SELECT text FROM goals WHERE completed = 0 ORDER BY id DESC LIMIT 5"
        ).fetchall()

    memory_text = [item[0] for item in memories]
    goal_text = [item[0] for item in goals]

    if memory_text:
        focus = random.choice(memory_text)
        reflection = f"My current simulated state is {mood}, with energy {energy}/10. A memory to revisit: {focus}"
    else:
        reflection = f"My current simulated state is {mood}, with energy {energy}/10. There are no stored memories to revisit yet."

    if goal_text:
        reflection += f" An active goal is: {random.choice(goal_text)}"

    with connect() as db:
        db.execute(
            "INSERT INTO reflections (text, created_at) VALUES (?, ?)",
            (reflection, now())
        )
    print("\n--- NOISE REFLECTION ---")
    print(reflection)


def show_status():
    print("\n--- NOISE STATUS ---")
    print("Mood:", get_state("mood", "calm"))
    print("Energy:", get_state("energy", "5") + "/10")
    with connect() as db:
        memory_count = db.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        goal_count = db.execute(
            "SELECT COUNT(*) FROM goals WHERE completed = 0"
        ).fetchone()[0]
    print("Stored memories:", memory_count)
    print("Active goals:", goal_count)


def help_menu():
    print("""
Commands:
  chat                 Talk to NOISE (basic terminal interaction)
  memory               Save a memory
  memories              Show saved memories
  goal                 Add a goal
  goals                Show goals
  done                 Mark a goal complete by ID
  mood                 Change simulated mood
  energy+              Increase energy
  energy-              Decrease energy
  reflect              Run simple reflection
  status               Show system status
  help                 Show commands
  exit                 Quit
""")


def chat():
    print("NOISE: Conversation mode. Type 'back' to return to menu.")
    while True:
        message = input("You: ").strip()
        if message.lower() == "back":
            return
        if not message:
            continue

        # Save the user message as a low-importance memory.
        add_memory(message, importance=1)

        mood = get_state("mood", "calm")
        replies = {
            "calm": "I have stored your message. What part of it should I examine?",
            "curious": "That is an interesting input. What else can you tell me?",
            "focused": "I will keep this point in focus. What is the next detail?",
            "uncertain": "I do not have enough information to draw a conclusion yet.",
            "reflective": "I will revisit this input during the reflection process."
        }
        print("NOISE:", replies.get(mood, replies["calm"]))


def main():
    setup()
    print("NOISE — Digital Soul Prototype v0.1")
    print("Type 'help' to view commands.")

    while True:
        command = input("\nnoise> ").strip().lower()

        if command == "exit":
            print("NOISE: Session ended.")
            break
        elif command == "help":
            help_menu()
        elif command == "chat":
            chat()
        elif command == "memory":
            text = input("Memory: ").strip()
            if text:
                try:
                    importance = int(input("Importance (1-5): ").strip() or "1")
                    importance = max(1, min(5, importance))
                except ValueError:
                    importance = 1
                add_memory(text, importance)
        elif command == "memories":
            show_memories()
        elif command == "goal":
            text = input("Goal: ").strip()
            if text:
                add_goal(text)
        elif command == "goals":
            show_goals()
        elif command == "done":
            try:
                goal_id = int(input("Goal ID: ").strip())
                complete_goal(goal_id)
            except ValueError:
                print("Please enter a numeric goal ID.")
        elif command == "mood":
            set_mood()
        elif command == "energy+":
            change_energy(1)
        elif command == "energy-":
            change_energy(-1)
        elif command == "reflect":
            reflect()
        elif command == "status":
            show_status()
        else:
            print("Unknown command. Type 'help'.")

if __name__ == "__main__":
    main()
