"""
FlashCard App — Single File Edition
=====================================
Stack   : Python 3 (http.server + sqlite3)
Database: SQLite (flashcards.db, auto-created)
Frontend: HTML + CSS + JS (embedded inside this file)

HOW TO RUN:
    python3 app.py
    Then open: http://localhost:5000

No pip install needed. No folder structure needed.
Just this one file!
"""

import http.server
import json
import sqlite3
import uuid
import os
from urllib.parse import urlparse, parse_qs
from datetime import datetime

PORT = 5000
DB   = os.path.join(os.path.dirname(__file__), "flashcards.db")

# ─── DATABASE SETUP ───────────────────────────────────────────

def get_db():
    """Return a database connection with row_factory for dict results."""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables and seed with sample data if empty."""
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS decks (
            id         TEXT PRIMARY KEY,
            name       TEXT NOT NULL,
            emoji      TEXT DEFAULT '📚',
            color      TEXT DEFAULT 'blue',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS cards (
            id         TEXT PRIMARY KEY,
            deck_id    TEXT NOT NULL,
            question   TEXT NOT NULL,
            answer     TEXT NOT NULL,
            tag        TEXT DEFAULT '',
            status     TEXT DEFAULT 'new',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
        );
    """)

    # Seed only if empty
    if c.execute("SELECT COUNT(*) FROM decks").fetchone()[0] == 0:
        decks = [
            (str(uuid.uuid4()), "Data Structures",   "🧩", "blue"),
            (str(uuid.uuid4()), "Operating Systems", "💻", "green"),
            (str(uuid.uuid4()), "Mathematics",       "🧮", "amber"),
        ]
        c.executemany("INSERT INTO decks(id,name,emoji,color) VALUES(?,?,?,?)", decks)

        ds_id = decks[0][0]
        os_id = decks[1][0]
        ma_id = decks[2][0]

        cards = [
            # Data Structures
            (str(uuid.uuid4()), ds_id, "What is a Stack?",
             "A linear data structure following LIFO (Last In, First Out). Elements are added and removed from the same end — the 'top'. Used in: function call stacks, undo/redo, expression evaluation.",
             "Linear DS", "known"),
            (str(uuid.uuid4()), ds_id, "What is a Queue?",
             "A linear data structure following FIFO (First In, First Out). Elements are inserted at the rear and removed from the front. Used in: BFS, CPU scheduling, print queues.",
             "Linear DS", "known"),
            (str(uuid.uuid4()), ds_id, "What is a Binary Search Tree (BST)?",
             "A tree where for each node, all left subtree values are smaller and all right subtree values are greater. Enables O(log n) average-case search, insertion, deletion.",
             "Trees", "again"),
            (str(uuid.uuid4()), ds_id, "What is Big-O Notation?",
             "A mathematical notation describing the upper bound (worst-case) complexity of an algorithm in terms of time or space as input size n grows. e.g. O(1), O(log n), O(n), O(n²).",
             "Complexity", "new"),
            (str(uuid.uuid4()), ds_id, "Array vs Linked List?",
             "Array: fixed size, O(1) random access, contiguous memory. Linked List: dynamic size, O(n) access, O(1) insert/delete at a known node. Choose based on your dominant operation.",
             "Comparison", "new"),
            # Operating Systems
            (str(uuid.uuid4()), os_id, "What is a Deadlock?",
             "A state where processes are blocked forever because each holds a resource the other needs. Four necessary conditions: Mutual Exclusion, Hold & Wait, No Preemption, Circular Wait.",
             "Process", "again"),
            (str(uuid.uuid4()), os_id, "What is Virtual Memory?",
             "A memory management technique that gives processes the illusion of more RAM than physically available, using disk storage as an extension. Managed via paging or segmentation.",
             "Memory", "new"),
            (str(uuid.uuid4()), os_id, "What is a Semaphore?",
             "A synchronization primitive controlling access to shared resources. Binary semaphore = mutex. Counting semaphore tracks N resources. Operations: wait(P) decrements, signal(V) increments.",
             "Sync", "known"),
            (str(uuid.uuid4()), os_id, "What is Round Robin Scheduling?",
             "CPU scheduling algorithm giving each process a fixed time quantum in circular order. Preemptive, fair, and widely used in time-sharing systems. Higher context-switch overhead than FCFS.",
             "Scheduling", "new"),
            # Mathematics
            (str(uuid.uuid4()), ma_id, "What is a Derivative?",
             "The instantaneous rate of change of a function at a point. Geometrically it represents the slope of the tangent line to the curve. Notation: f'(x) or dy/dx.",
             "Calculus", "known"),
            (str(uuid.uuid4()), ma_id, "State Euler's Identity",
             "e^(iπ) + 1 = 0 — widely considered the most beautiful equation in mathematics. Connects five fundamental constants: e (Euler's number), i (imaginary unit), π, 1, and 0.",
             "Algebra", "known"),
            (str(uuid.uuid4()), ma_id, "Fundamental Theorem of Calculus",
             "If F is an antiderivative of f on [a,b], then ∫(a→b) f(x)dx = F(b) − F(a). It unifies differentiation and integration as inverse operations.",
             "Calculus", "again"),
            (str(uuid.uuid4()), ma_id, "What is a Matrix Determinant?",
             "A scalar computed from a square matrix encoding properties like invertibility. If det(A) = 0, the matrix is singular (non-invertible). Computed via cofactor expansion.",
             "Linear Alg", "new"),
        ]
        c.executemany(
            "INSERT INTO cards(id,deck_id,question,answer,tag,status) VALUES(?,?,?,?,?,?)",
            cards
        )

    conn.commit()
    conn.close()
    print("  ✅  Database ready →", DB)


# ─── HELPERS ──────────────────────────────────────────────────

def row_to_dict(row):
    return dict(row) if row else None

def rows_to_list(rows):
    return [dict(r) for r in rows]

def deck_with_stats(deck_id, conn):
    """Return deck dict enriched with card count stats."""
    c = conn.cursor()
    deck = row_to_dict(c.execute("SELECT * FROM decks WHERE id=?", (deck_id,)).fetchone())
    if not deck:
        return None
    stats = c.execute("""
        SELECT
            COUNT(*) as card_count,
            SUM(CASE WHEN status='known' THEN 1 ELSE 0 END) as known_count,
            SUM(CASE WHEN status='again' THEN 1 ELSE 0 END) as again_count,
            SUM(CASE WHEN status='new'   THEN 1 ELSE 0 END) as new_count
        FROM cards WHERE deck_id=?
    """, (deck_id,)).fetchone()
    deck["card_count"]  = stats["card_count"]
    deck["known_count"] = stats["known_count"] or 0
    deck["again_count"] = stats["again_count"] or 0
    deck["new_count"]   = stats["new_count"]   or 0
    deck["mastered_pct"] = (
        round(deck["known_count"] / deck["card_count"] * 100)
        if deck["card_count"] > 0 else 0
    )
    return deck



# ─── EMBEDDED FRONTEND ───────────────────────────────────────
FRONTEND_HTML = '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8"/>\n<meta name="viewport" content="width=device-width, initial-scale=1.0"/>\n<title>FlashCard App</title>\n<style>\n/* ── TOKENS ───────────────────────────────────────────────── */\n:root {\n  --bg:       #f4f1ec;\n  --bg2:      #ece8e0;\n  --paper:    #fdfaf5;\n  --paper2:   #f8f4ed;\n  --ink:      #1e1a14;\n  --ink2:     #3d3728;\n  --ink3:     #7a7060;\n  --ink4:     #b5a890;\n  --border:   rgba(30,26,20,.1);\n  --border2:  rgba(30,26,20,.18);\n\n  /* Accent palette */\n  --blue:     #2d6be4;\n  --blue-s:   #eaf0fd;\n  --green:    #1f8a5e;\n  --green-s:  #e6f5ee;\n  --red:      #c0392b;\n  --red-s:    #fdf0ee;\n  --amber:    #b07820;\n  --amber-s:  #fdf6e3;\n  --purple:   #6b3fa0;\n  --purple-s: #f2edfa;\n\n  --shadow-sm: 0 1px 4px rgba(30,26,20,.07);\n  --shadow:    0 4px 18px rgba(30,26,20,.09);\n  --shadow-md: 0 8px 32px rgba(30,26,20,.12);\n  --shadow-lg: 0 20px 56px rgba(30,26,20,.15);\n  --r:         12px;\n  --r-sm:      8px;\n  --r-lg:      18px;\n}\n\n*,*::before,*::after { margin:0; padding:0; box-sizing:border-box; }\nhtml { scroll-behavior:smooth; }\n\nbody {\n  font-family:\'Nunito\',\'Segoe UI\',sans-serif;\n  background: var(--bg);\n  color: var(--ink);\n  min-height: 100vh;\n  font-size: 15px;\n  line-height: 1.6;\n}\n\n/* ── NAVBAR ────────────────────────────────────────────────── */\n.navbar {\n  height: 60px;\n  display: flex;\n  align-items: center;\n  justify-content: space-between;\n  padding: 0 28px;\n  background: var(--paper);\n  border-bottom: 1px solid var(--border);\n  position: sticky;\n  top: 0;\n  z-index: 60;\n  box-shadow: var(--shadow-sm);\n}\n\n.nav-brand {\n  display: flex;\n  align-items: center;\n  gap: 8px;\n  font-size: 18px;\n  font-weight: 800;\n  color: var(--ink);\n}\n\n.brand-icon { font-size: 22px; }\n.brand-name { letter-spacing: -.4px; }\n.brand-name em { font-style: italic; color: var(--red); }\n\n.nav-tabs { display: flex; gap: 3px; }\n\n.nav-tab {\n  padding: 7px 16px;\n  border-radius: 100px;\n  border: none;\n  background: transparent;\n  font-family: inherit;\n  font-size: 13.5px;\n  font-weight: 700;\n  color: var(--ink3);\n  cursor: pointer;\n  transition: all .18s;\n}\n\n.nav-tab:hover { background: var(--bg2); color: var(--ink); }\n.nav-tab.active { background: var(--ink); color: #fff; }\n\n.nav-badge {\n  display: flex;\n  align-items: center;\n  gap: 7px;\n  padding: 6px 14px;\n  border-radius: 100px;\n  background: var(--paper2);\n  border: 1px solid var(--border);\n  font-size: 11.5px;\n  font-family: \'JetBrains Mono\', monospace;\n  color: var(--ink3);\n  cursor: pointer;\n  transition: all .18s;\n}\n\n.nav-badge:hover { border-color: var(--green); color: var(--green); }\n\n.badge-dot {\n  width: 7px; height: 7px;\n  background: var(--green);\n  border-radius: 50%;\n  box-shadow: 0 0 6px var(--green);\n  animation: blink 2s infinite;\n}\n\n@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.35} }\n\n/* ── VIEWS ─────────────────────────────────────────────────── */\n.view { display: none; }\n.view.active { display: block; animation: fadeUp .3s ease both; }\n\n@keyframes fadeUp {\n  from { opacity:0; transform:translateY(14px); }\n  to   { opacity:1; transform:translateY(0); }\n}\n\n/* ── PAGE LAYOUT ───────────────────────────────────────────── */\n.page-wrap { max-width: 1140px; margin: 0 auto; padding: 36px 28px 60px; }\n\n.page-head {\n  display: flex;\n  justify-content: space-between;\n  align-items: flex-start;\n  margin-bottom: 28px;\n  flex-wrap: wrap;\n  gap: 14px;\n}\n\n.page-title {\n  font-family: \'Playfair Display\', serif;\n  font-size: clamp(24px, 4vw, 32px);\n  font-weight: 800;\n  color: var(--ink);\n  letter-spacing: -.6px;\n  margin-bottom: 2px;\n}\n\n.page-sub { font-size: 13px; color: var(--ink3); }\n.head-actions { display: flex; gap: 10px; flex-wrap: wrap; }\n\n.section-title {\n  font-family: \'Playfair Display\', serif;\n  font-size: 18px;\n  font-weight: 700;\n  color: var(--ink);\n  margin-bottom: 14px;\n}\n\n/* ── STATS ─────────────────────────────────────────────────── */\n.stats-grid {\n  display: grid;\n  grid-template-columns: repeat(4,1fr);\n  gap: 14px;\n  margin-bottom: 28px;\n}\n\n.stat-card {\n  background: var(--paper);\n  border: 1px solid var(--border);\n  border-radius: var(--r);\n  padding: 22px 24px;\n  box-shadow: var(--shadow-sm);\n  min-height: 88px;\n}\n\n.stat-card.loading {\n  background: linear-gradient(90deg, var(--bg2) 25%, var(--bg) 50%, var(--bg2) 75%);\n  background-size: 200% 100%;\n  animation: shimmer 1.4s infinite;\n}\n\n@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }\n\n.stat-val {\n  font-family: \'Playfair Display\', serif;\n  font-size: 36px;\n  font-weight: 800;\n  line-height: 1;\n  margin-bottom: 4px;\n}\n\n.stat-lbl { font-size: 12px; color: var(--ink3); font-weight: 600; }\n\n/* ── DECK GRID ─────────────────────────────────────────────── */\n.deck-grid {\n  display: grid;\n  grid-template-columns: repeat(auto-fill, minmax(268px,1fr));\n  gap: 16px;\n  margin-bottom: 36px;\n}\n\n.deck-card {\n  background: var(--paper);\n  border: 1px solid var(--border);\n  border-radius: var(--r-lg);\n  padding: 22px;\n  cursor: pointer;\n  transition: all .2s;\n  position: relative;\n  overflow: hidden;\n}\n\n.deck-card::after {\n  content:\'\';\n  position: absolute;\n  top:0; left:0; right:0; height: 3px;\n  border-radius: var(--r-lg) var(--r-lg) 0 0;\n}\n\n.dc-blue::after   { background: var(--blue); }\n.dc-green::after  { background: var(--green); }\n.dc-amber::after  { background: var(--amber); }\n.dc-purple::after { background: var(--purple); }\n.dc-red::after    { background: var(--red); }\n\n.deck-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); border-color: var(--border2); }\n\n.dc-top { display:flex; justify-content:space-between; align-items:flex-start; }\n.dc-emoji { font-size: 30px; margin-bottom: 10px; line-height: 1; }\n\n.dc-menu { display:flex; gap:4px; opacity:0; transition: opacity .18s; }\n.deck-card:hover .dc-menu { opacity:1; }\n\n.dc-menu-btn {\n  width: 28px; height: 28px;\n  border-radius: 7px;\n  border: 1px solid var(--border);\n  background: transparent;\n  cursor: pointer;\n  font-size: 13px;\n  color: var(--ink3);\n  display:flex; align-items:center; justify-content:center;\n  transition: all .15s;\n}\n\n.dc-menu-btn:hover { background: var(--bg2); color: var(--ink); }\n\n.dc-name {\n  font-family: \'Playfair Display\', serif;\n  font-size: 16px;\n  font-weight: 700;\n  color: var(--ink);\n  margin-bottom: 4px;\n}\n\n.dc-meta { font-size: 12px; color: var(--ink3); margin-bottom: 14px; }\n\n.dc-pbar { height: 4px; background: var(--bg2); border-radius: 2px; overflow: hidden; margin-bottom: 14px; }\n.dc-pbar-fill { height:100%; border-radius:2px; transition: width .6s ease; }\n.dc-blue  .dc-pbar-fill { background: var(--blue); }\n.dc-green .dc-pbar-fill { background: var(--green); }\n.dc-amber .dc-pbar-fill { background: var(--amber); }\n.dc-purple .dc-pbar-fill { background: var(--purple); }\n.dc-red   .dc-pbar-fill { background: var(--red); }\n\n.dc-btns { display:flex; gap:8px; }\n\n.dc-btn {\n  flex:1; padding:8px 4px;\n  border-radius: var(--r-sm);\n  border: 1px solid var(--border);\n  background: var(--bg);\n  font-family: inherit;\n  font-size: 12px; font-weight: 700;\n  color: var(--ink2); cursor: pointer;\n  transition: all .15s; text-align:center;\n}\n\n.dc-btn:hover { background: var(--bg2); border-color: var(--border2); }\n.dc-btn.study { background: var(--green); color:#fff; border-color: var(--green); }\n.dc-btn.study:hover { background: #23a570; }\n\n/* Add deck card */\n.add-deck-card {\n  background: transparent;\n  border: 2px dashed var(--bg2);\n  border-radius: var(--r-lg);\n  min-height: 200px;\n  display:flex; flex-direction:column; align-items:center; justify-content:center;\n  gap:8px; cursor:pointer; color: var(--ink4); font-size:13px; font-weight:700;\n  transition: all .2s;\n}\n\n.add-deck-card:hover { border-color: var(--blue); color: var(--blue); background: var(--blue-s); }\n\n/* ── CARDS TABLE ───────────────────────────────────────────── */\n.table-head {\n  display:flex; justify-content:space-between; align-items:flex-end;\n  flex-wrap:wrap; gap:12px; margin-bottom:14px;\n}\n\n.filter-row {\n  display:flex; gap:8px; flex-wrap:wrap; align-items:center;\n}\n\n.chip {\n  padding: 5px 14px;\n  border-radius: 100px;\n  border: 1.5px solid var(--border);\n  background: var(--paper);\n  font-size: 12px; font-weight: 700;\n  color: var(--ink3); cursor:pointer;\n  transition: all .15s;\n  font-family: \'JetBrains Mono\', monospace;\n}\n\n.chip:hover { border-color: var(--border2); color: var(--ink); }\n.chip.active { background: var(--ink); color:#fff; border-color: var(--ink); }\n\n.status-chips { display:flex; gap:6px; }\n\n.cards-table { display:flex; flex-direction:column; gap:7px; }\n\n.card-row {\n  background: var(--paper);\n  border: 1px solid var(--border);\n  border-radius: var(--r-sm);\n  padding: 13px 16px;\n  display:flex; align-items:center; gap:12px;\n  box-shadow: var(--shadow-sm);\n  transition: all .15s;\n}\n\n.card-row:hover { box-shadow: var(--shadow); border-color: var(--border2); }\n\n.cr-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }\n.dot-known { background: var(--green); }\n.dot-again { background: var(--red); }\n.dot-new   { background: var(--ink4); }\n\n.cr-body { flex:1; min-width:0; }\n.cr-q { font-size:13.5px; font-weight:700; color:var(--ink); margin-bottom:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }\n.cr-a { font-size:12px; color:var(--ink3); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }\n\n.cr-tag {\n  font-family:\'JetBrains Mono\',monospace;\n  font-size:10px; font-weight:600;\n  padding:3px 10px; border-radius:5px;\n  background: var(--bg2); color: var(--ink3);\n  flex-shrink:0;\n}\n\n.cr-status {\n  font-family:\'JetBrains Mono\',monospace;\n  font-size:10px; font-weight:700;\n  padding:3px 10px; border-radius:5px;\n  flex-shrink:0;\n}\n\n.cr-status.known { background:var(--green-s); color:var(--green); }\n.cr-status.again { background:var(--red-s);   color:var(--red); }\n.cr-status.new   { background:var(--bg2);     color:var(--ink3); }\n\n.cr-actions { display:flex; gap:5px; }\n\n.icon-btn {\n  padding:5px 9px; border:1px solid var(--border); background:transparent;\n  border-radius:6px; cursor:pointer; font-size:12px; color:var(--ink3);\n  transition: all .15s;\n}\n\n.icon-btn:hover { background:var(--bg2); color:var(--ink); }\n.icon-btn.del:hover { background:var(--red-s); color:var(--red); border-color:var(--red); }\n\n/* ── STUDY LAYOUT ──────────────────────────────────────────── */\n.study-layout {\n  display: grid;\n  grid-template-columns: 244px 1fr;\n  min-height: calc(100vh - 60px);\n}\n\n.study-aside {\n  background: var(--paper);\n  border-right: 1px solid var(--border);\n  padding: 22px 14px;\n  overflow-y: auto;\n}\n\n.aside-label {\n  font-size: 10px; font-weight: 800;\n  letter-spacing: 1.5px; text-transform: uppercase;\n  color: var(--ink4); font-family:\'JetBrains Mono\',monospace;\n  padding: 4px 10px 8px;\n}\n\n.aside-deck-item {\n  display:flex; align-items:center; gap:10px;\n  padding:9px 10px; border-radius:var(--r-sm);\n  cursor:pointer; transition: all .15s;\n  border: 1.5px solid transparent; margin-bottom:2px;\n}\n\n.aside-deck-item:hover { background: var(--bg2); }\n.aside-deck-item.active { background: var(--blue-s); border-color: rgba(45,107,228,.2); }\n\n.adi-emoji { font-size:16px; }\n.adi-body  { flex:1; }\n.adi-name  { font-size:13px; font-weight:700; color:var(--ink2); }\n.aside-deck-item.active .adi-name { color:var(--blue); }\n.adi-meta  { font-size:11px; color:var(--ink4); font-family:\'JetBrains Mono\',monospace; }\n\n.aside-hr { border:none; border-top:1px solid var(--border); margin:14px 0; }\n\n.aside-stat {\n  display:flex; justify-content:space-between; align-items:center;\n  padding:5px 10px; font-size:12.5px; color:var(--ink2);\n}\n\n.aside-stat strong { font-weight:800; font-family:\'JetBrains Mono\',monospace; color:var(--ink); }\n\n.toggle-row { cursor:pointer; border-radius:var(--r-sm); transition:background .15s; }\n.toggle-row:hover { background:var(--bg2); }\n.toggle-val { font-weight:800; font-family:\'JetBrains Mono\',monospace; color:var(--ink4); }\n.toggle-val.on { color:var(--green); }\n\n/* ── STUDY MAIN ─────────────────────────────────────────────── */\n.study-main {\n  display:flex; flex-direction:column; align-items:center;\n  padding: 36px 24px; overflow-y:auto;\n}\n\n.mid-state { text-align:center; padding:80px 20px; color:var(--ink3); }\n.mid-state .mid-icon { font-size:46px; margin-bottom:14px; }\n.mid-state h2 { font-family:\'Playfair Display\',serif; font-size:22px; color:var(--ink2); margin-bottom:6px; }\n.mid-state p  { font-size:14px; max-width:300px; margin:0 auto; }\n\n.card-area { display:flex; flex-direction:column; align-items:center; width:100%; max-width:600px; }\n\n.deck-label { font-size:12px; color:var(--ink3); font-family:\'JetBrains Mono\',monospace; margin-bottom:12px; font-weight:600; }\n\n/* Progress */\n.prog-wrap { width:100%; margin-bottom:8px; }\n.prog-info { display:flex; justify-content:space-between; font-size:11px; font-family:\'JetBrains Mono\',monospace; color:var(--ink4); margin-bottom:6px; }\n.prog-track { height:4px; background:var(--bg2); border-radius:2px; overflow:hidden; }\n.prog-bar   { height:100%; background:linear-gradient(90deg,var(--blue),var(--purple)); border-radius:2px; transition:width .5s ease; }\n\n/* Dots */\n.dots-row { display:flex; gap:5px; flex-wrap:wrap; width:100%; margin-bottom:22px; min-height:12px; }\n.dot  { width:10px; height:10px; border-radius:50%; background:var(--bg2); transition:all .3s; }\n.dot.known { background:var(--green); }\n.dot.again { background:var(--red); }\n.dot.curr  { background:var(--amber); transform:scale(1.3); box-shadow:0 0 0 3px rgba(176,120,32,.2); }\n\n/* Flashcard 3D */\n.fc-scene {\n  width:100%; height:300px;\n  perspective:1200px;\n  cursor:pointer;\n  margin-bottom:22px;\n}\n\n.fc {\n  width:100%; height:100%;\n  position:relative;\n  transform-style:preserve-3d;\n  transition:transform .52s cubic-bezier(.4,0,.2,1);\n}\n\n.fc.flipped { transform:rotateY(180deg); }\n\n.fc-face {\n  position:absolute; inset:0;\n  border-radius:20px;\n  border:1px solid var(--border);\n  display:flex; flex-direction:column;\n  align-items:center; justify-content:center;\n  text-align:center;\n  padding:42px 48px;\n  backface-visibility:hidden;\n  -webkit-backface-visibility:hidden;\n}\n\n.fc-front {\n  background: var(--paper);\n  box-shadow: var(--shadow-lg);\n  background-image: repeating-linear-gradient(0deg, transparent, transparent 30px, rgba(30,26,20,.03) 30px, rgba(30,26,20,.03) 31px);\n}\n\n.fc-back {\n  background: var(--ink);\n  transform: rotateY(180deg);\n  border-color:rgba(255,255,255,.06);\n  box-shadow: 0 20px 60px rgba(30,26,20,.4);\n}\n\n.fc-label {\n  position:absolute; top:16px; left:20px;\n  font-size:9px; font-weight:800; letter-spacing:2px;\n  font-family:\'JetBrains Mono\',monospace; color:var(--ink4);\n}\n\n.fc-label-back { color:rgba(255,255,255,.2); }\n\n.fc-tag {\n  position:absolute; top:16px; right:20px;\n  font-size:10px; font-weight:700;\n  padding:3px 11px; border-radius:5px;\n  background:var(--bg2); color:var(--ink3);\n  font-family:\'JetBrains Mono\',monospace;\n}\n\n.fc-tag-back { background:rgba(255,255,255,.08); color:rgba(255,255,255,.3); }\n\n.fc-q {\n  font-family:\'Playfair Display\',serif;\n  font-size:clamp(17px,3vw,22px);\n  font-weight:700; color:var(--ink); line-height:1.5;\n}\n\n.fc-a {\n  font-size:clamp(14px,2.2vw,17px);\n  color:rgba(253,250,245,.9); line-height:1.7;\n}\n\n.fc-hint {\n  position:absolute; bottom:16px;\n  font-size:11px; color:var(--ink4);\n  display:flex; align-items:center; gap:5px;\n}\n\n.fc-hint-back { color:rgba(255,255,255,.15); }\n\n.fc-hint kbd {\n  background:var(--bg2); border:1px solid var(--border);\n  border-radius:4px; padding:1px 7px;\n  font-family:\'JetBrains Mono\',monospace; font-size:9px;\n  color:var(--ink3); box-shadow:0 2px 0 var(--border);\n}\n\n/* Study controls */\n.study-controls { display:flex; gap:10px; width:100%; margin-bottom:16px; }\n\n.sc-btn {\n  flex:1; padding:13px;\n  border-radius:100px; border:2px solid var(--border);\n  background:var(--paper); font-family:inherit;\n  font-size:14px; font-weight:800; cursor:pointer;\n  color:var(--ink2); display:flex; align-items:center; justify-content:center; gap:7px;\n  transition: all .2s; box-shadow: var(--shadow-sm);\n}\n\n.sc-btn:disabled { opacity:.3; pointer-events:none; }\n.sc-btn:hover:not(:disabled) { transform:translateY(-2px); box-shadow: var(--shadow); }\n\n.sc-skip:hover  { background:var(--bg2); border-color:var(--border2); }\n.sc-again { border-color:rgba(192,57,43,.3); }\n.sc-again:hover { background:var(--red-s); border-color:var(--red); color:var(--red); }\n.sc-know  { border-color:rgba(31,138,94,.3); }\n.sc-know:hover  { background:var(--green-s); border-color:var(--green); color:var(--green); }\n\n.sess-row { display:flex; gap:20px; font-size:12.5px; font-family:\'JetBrains Mono\',monospace; color:var(--ink3); margin-bottom:12px; }\n.sess-know strong { color:var(--green); }\n.sess-again strong { color:var(--red); }\n\n.kbd-row { display:flex; gap:14px; font-size:11px; color:var(--ink4); }\n.kbd-row span { display:flex; align-items:center; gap:4px; }\n\n.kbd-row kbd {\n  background:var(--paper); border:1px solid var(--border);\n  border-radius:4px; padding:2px 7px;\n  font-family:\'JetBrains Mono\',monospace; font-size:9px;\n  color:var(--ink3); box-shadow:0 2px 0 var(--bg2);\n}\n\n/* ── COMPLETION ─────────────────────────────────────────────── */\n.completion { text-align:center; max-width:520px; }\n\n.comp-icon { font-size:52px; margin-bottom:16px; }\n\n.comp-title {\n  font-family:\'Playfair Display\',serif;\n  font-size:28px; font-weight:800; color:var(--ink);\n  letter-spacing:-.5px; margin-bottom:8px;\n}\n\n.comp-sub { font-size:14px; color:var(--ink3); margin-bottom:24px; line-height:1.6; }\n\n.result-bars { text-align:left; width:320px; margin:0 auto 24px; }\n\n.rbar { margin-bottom:14px; }\n.rbar-label { display:flex; justify-content:space-between; font-size:12.5px; font-weight:700; color:var(--ink2); margin-bottom:6px; }\n.rbar-track { height:10px; background:var(--bg2); border-radius:5px; overflow:hidden; }\n.rbar-fill  { height:100%; border-radius:5px; transition:width .8s cubic-bezier(.4,0,.2,1); }\n.rbar-green { background:var(--green); }\n.rbar-red   { background:var(--red); }\n\n.comp-btns { display:flex; gap:10px; justify-content:center; flex-wrap:wrap; }\n\n/* ── BUTTONS ────────────────────────────────────────────────── */\n.btn {\n  display:inline-flex; align-items:center; gap:7px;\n  padding:10px 22px; border-radius:100px;\n  font-family:inherit; font-size:13.5px; font-weight:800;\n  cursor:pointer; border:none; transition:all .2s;\n  text-decoration:none;\n}\n\n.btn-primary { background:var(--blue); color:#fff; box-shadow:0 4px 16px rgba(45,107,228,.3); }\n.btn-primary:hover { background:#3a7af5; transform:translateY(-1px); box-shadow:0 8px 24px rgba(45,107,228,.38); }\n\n.btn-outline {\n  background:transparent; border:2px solid var(--border);\n  color:var(--ink2); box-shadow:var(--shadow-sm);\n}\n\n.btn-outline:hover { border-color:var(--border2); background:var(--bg2); color:var(--ink); }\n\n.mt16 { margin-top:16px; }\n\n/* ── MODAL ──────────────────────────────────────────────────── */\n.overlay {\n  position:fixed; inset:0;\n  background:rgba(30,26,20,.45);\n  backdrop-filter:blur(7px);\n  z-index:100; display:flex; align-items:center; justify-content:center;\n  padding:20px;\n  opacity:0; pointer-events:none; transition:opacity .22s;\n}\n\n.overlay.show { opacity:1; pointer-events:all; }\n\n.modal {\n  background:var(--paper); border-radius:var(--r-lg);\n  width:100%; max-width:460px;\n  border:1px solid var(--border); box-shadow:var(--shadow-lg);\n  transform:scale(.95) translateY(8px); transition:transform .22s; overflow:hidden;\n}\n\n.modal-wide { max-width:600px; }\n.overlay.show .modal { transform:scale(1) translateY(0); }\n\n.modal-head {\n  padding:20px 22px 0;\n  display:flex; justify-content:space-between; align-items:center;\n}\n\n.modal-title { font-family:\'Playfair Display\',serif; font-size:18px; font-weight:800; color:var(--ink); }\n\n.modal-close {\n  width:30px; height:30px; border-radius:50%;\n  border:none; background:var(--bg2); cursor:pointer;\n  font-size:15px; color:var(--ink3);\n  display:flex; align-items:center; justify-content:center;\n  transition:all .15s;\n}\n\n.modal-close:hover { background:var(--bg); color:var(--ink); }\n\n.modal-body { padding:18px 22px 22px; }\n\n/* Form */\n.field { margin-bottom:14px; }\n\n.field label {\n  display:block; font-size:11px; font-weight:800;\n  letter-spacing:.8px; text-transform:uppercase;\n  color:var(--ink3); font-family:\'JetBrains Mono\',monospace; margin-bottom:6px;\n}\n\n.field label small { font-size:10px; text-transform:none; font-weight:600; opacity:.7; }\n\n.field input, .field textarea, .field select {\n  width:100%;\n  background:var(--paper2); border:1.5px solid var(--border);\n  border-radius:var(--r-sm); padding:10px 13px;\n  font-family:inherit; font-size:14px; color:var(--ink);\n  outline:none; transition:border-color .18s;\n}\n\n.field input:focus, .field textarea:focus, .field select:focus { border-color:var(--blue); }\n.field textarea { resize:vertical; min-height:78px; line-height:1.5; }\n.field select option { background:var(--paper); }\n\n.field-row { display:grid; grid-template-columns:1fr 1fr; gap:12px; }\n\n.modal-footer { display:flex; gap:8px; justify-content:flex-end; margin-top:16px; }\n\n/* Emoji / Color pickers */\n.emoji-grid { display:flex; flex-wrap:wrap; gap:6px; }\n\n.emoji-opt {\n  width:34px; height:34px; font-size:17px;\n  border:1.5px solid var(--border); border-radius:var(--r-sm);\n  cursor:pointer; display:flex; align-items:center; justify-content:center;\n  background:var(--paper2); transition:all .15s;\n}\n\n.emoji-opt:hover, .emoji-opt.on { border-color:var(--blue); background:var(--blue-s); }\n\n.color-row { display:flex; gap:9px; }\n\n.color-dot {\n  width:28px; height:28px; border-radius:50%; cursor:pointer;\n  border:2px solid transparent; transition:transform .15s;\n}\n\n.color-dot:hover, .color-dot.on { border-color:var(--ink); transform:scale(1.15); }\n\n/* ── API LOG ────────────────────────────────────────────────── */\n.api-log {\n  position:fixed; bottom:16px; right:16px;\n  width:320px; max-height:220px;\n  background:var(--ink); border:1px solid rgba(255,255,255,.1);\n  border-radius:var(--r); overflow:hidden;\n  display:none; flex-direction:column; z-index:80;\n  box-shadow:var(--shadow-lg);\n}\n\n.api-log.show { display:flex; }\n\n.api-log-head {\n  display:flex; justify-content:space-between; align-items:center;\n  padding:8px 12px; border-bottom:1px solid rgba(255,255,255,.08);\n  font-size:11px; font-weight:700; color:rgba(253,250,245,.7);\n  font-family:\'JetBrains Mono\',monospace;\n}\n\n.api-log-head button { background:none; border:none; cursor:pointer; color:rgba(255,255,255,.4); font-size:14px; }\n.api-log-head button:hover { color:rgba(255,255,255,.8); }\n\n.api-log-body { overflow-y:auto; padding:6px 0; }\n\n.log-entry {\n  padding:4px 12px; font-size:10.5px; font-family:\'JetBrains Mono\',monospace;\n  border-bottom:1px solid rgba(255,255,255,.04); line-height:1.5;\n}\n\n.log-get    { color:#60a5fa; }\n.log-post   { color:#34d399; }\n.log-put    { color:#fbbf24; }\n.log-delete { color:#f87171; }\n\n/* ── TOAST ──────────────────────────────────────────────────── */\n.toast {\n  position:fixed; bottom:24px; left:50%;\n  transform:translateX(-50%) translateY(60px);\n  background:var(--ink); color:var(--paper);\n  padding:11px 22px; border-radius:100px;\n  font-size:13px; font-weight:700;\n  box-shadow:var(--shadow-lg); z-index:200;\n  opacity:0; transition:all .3s; pointer-events:none; white-space:nowrap;\n}\n\n.toast.show { opacity:1; transform:translateX(-50%) translateY(0); }\n\n/* Loading row */\n.loading-row { color:var(--ink4); font-size:13px; padding:20px; }\n\n/* Spinner */\n.spin {\n  width:20px; height:20px; border:2px solid var(--border);\n  border-top-color:var(--blue); border-radius:50%;\n  animation:spin .6s linear infinite; display:inline-block;\n}\n\n@keyframes spin { to{transform:rotate(360deg)} }\n\n/* Empty state */\n.empty-state { text-align:center; padding:52px 20px; }\n.empty-state .ei { font-size:40px; margin-bottom:12px; }\n.empty-state h3 { font-family:\'Playfair Display\',serif; font-size:18px; color:var(--ink2); margin-bottom:5px; }\n.empty-state p  { font-size:13px; color:var(--ink3); max-width:280px; margin:0 auto 14px; }\n\n/* Responsive */\n@media (max-width:700px) {\n  .study-layout  { grid-template-columns:1fr; }\n  .study-aside   { display:none; }\n  .stats-grid    { grid-template-columns:repeat(2,1fr); }\n  .deck-grid     { grid-template-columns:1fr; }\n  .field-row     { grid-template-columns:1fr; }\n  .fc-scene      { height:260px; }\n  .study-controls { flex-wrap:wrap; }\n}\n\n</style>\n\n</head>\n<body>\n\n<!-- ░░ NAVBAR ░░ -->\n<nav class="navbar">\n  <div class="nav-brand">\n    <span class="brand-icon">🧠</span>\n    <span class="brand-name">Flash<em>Card</em></span>\n  </div>\n  <div class="nav-tabs">\n    <button class="nav-tab active" id="tab-home"  onclick="goto(\'home\')">🏠 Dashboard</button>\n    <button class="nav-tab"        id="tab-decks" onclick="goto(\'decks\')">📚 Decks</button>\n    <button class="nav-tab"        id="tab-study" onclick="goto(\'study\')">🃏 Study</button>\n  </div>\n  <div class="nav-badge" onclick="toggleApiLog()" title="Click to see API calls">\n    <span class="badge-dot"></span>\n    <span class="badge-text">Python · Port 5000</span>\n  </div>\n</nav>\n\n<!-- ░░ VIEWS ░░ -->\n<div id="app">\n\n  <!-- ── HOME / DASHBOARD ── -->\n  <section class="view active" id="view-home">\n    <div class="page-wrap">\n      <div class="page-head">\n        <div>\n          <h1 class="page-title">Dashboard</h1>\n          <p class="page-sub">Your study overview — fetched live from Python backend</p>\n        </div>\n        <div class="head-actions">\n          <button class="btn btn-outline" onclick="goto(\'decks\')">Manage Decks</button>\n          <button class="btn btn-primary" onclick="goto(\'study\')">▶ Start Studying</button>\n        </div>\n      </div>\n\n      <!-- Stats -->\n      <div class="stats-grid" id="home-stats">\n        <div class="stat-card loading"><div class="spin"></div></div>\n        <div class="stat-card loading"></div>\n        <div class="stat-card loading"></div>\n        <div class="stat-card loading"></div>\n      </div>\n\n      <!-- Deck cards -->\n      <h2 class="section-title">My Decks</h2>\n      <div class="deck-grid" id="home-decks">\n        <div class="loading-row">Loading decks from API…</div>\n      </div>\n    </div>\n  </section>\n\n  <!-- ── DECKS ── -->\n  <section class="view" id="view-decks">\n    <div class="page-wrap">\n      <div class="page-head">\n        <div>\n          <h1 class="page-title">My Decks</h1>\n          <p class="page-sub">Create and manage your flashcard decks & cards</p>\n        </div>\n        <div class="head-actions">\n          <button class="btn btn-outline" onclick="openCardModal()">＋ Card</button>\n          <button class="btn btn-primary" onclick="openDeckModal()">＋ New Deck</button>\n        </div>\n      </div>\n\n      <div class="deck-grid" id="decks-grid"></div>\n\n      <div class="table-head">\n        <h2 class="section-title">All Cards</h2>\n        <div class="filter-row">\n          <div id="deck-chips"></div>\n          <div class="status-chips">\n            <button class="chip active" data-s="all"   onclick="setStatusFilter(\'all\',this)">All</button>\n            <button class="chip"        data-s="new"    onclick="setStatusFilter(\'new\',this)">🆕 New</button>\n            <button class="chip"        data-s="again"  onclick="setStatusFilter(\'again\',this)">↺ Again</button>\n            <button class="chip"        data-s="known"  onclick="setStatusFilter(\'known\',this)">✓ Known</button>\n          </div>\n        </div>\n      </div>\n\n      <div class="cards-table" id="cards-table"></div>\n    </div>\n  </section>\n\n  <!-- ── STUDY ── -->\n  <section class="view" id="view-study">\n    <div class="study-layout">\n\n      <!-- Sidebar -->\n      <aside class="study-aside">\n        <p class="aside-label">DECKS</p>\n        <div id="aside-decks"></div>\n        <hr class="aside-hr"/>\n        <p class="aside-label">SESSION</p>\n        <div class="aside-stat"><span>✓ Know</span><strong id="sb-know">0</strong></div>\n        <div class="aside-stat"><span>↺ Again</span><strong id="sb-again">0</strong></div>\n        <div class="aside-stat"><span>Remaining</span><strong id="sb-rem">—</strong></div>\n        <hr class="aside-hr"/>\n        <p class="aside-label">OPTIONS</p>\n        <div class="aside-stat toggle-row" onclick="toggleShuffle()">\n          <span>Shuffle</span>\n          <span class="toggle-val" id="shuffle-val">OFF</span>\n        </div>\n      </aside>\n\n      <!-- Study content -->\n      <main class="study-main">\n\n        <!-- Initial prompt -->\n        <div class="mid-state" id="st-pick">\n          <div class="mid-icon">👈</div>\n          <h2>Pick a deck</h2>\n          <p>Choose a subject from the sidebar to begin studying</p>\n        </div>\n\n        <!-- No cards state -->\n        <div class="mid-state" id="st-empty" style="display:none">\n          <div class="mid-icon">🃏</div>\n          <h2>No cards yet</h2>\n          <p>Add cards to this deck first</p>\n          <button class="btn btn-primary mt16" onclick="goto(\'decks\')">＋ Add Cards</button>\n        </div>\n\n        <!-- Active card area -->\n        <div class="card-area" id="st-card" style="display:none">\n\n          <p class="deck-label" id="deck-label">Deck Name</p>\n\n          <!-- Progress -->\n          <div class="prog-wrap">\n            <div class="prog-info">\n              <span id="prog-text">1 / 0</span>\n              <span id="prog-pct">0%</span>\n            </div>\n            <div class="prog-track"><div class="prog-bar" id="prog-bar" style="width:0%"></div></div>\n          </div>\n\n          <!-- Dots -->\n          <div class="dots-row" id="dots-row"></div>\n\n          <!-- 3D Flashcard -->\n          <div class="fc-scene" onclick="flipCard()">\n            <div class="fc" id="flashcard">\n              <div class="fc-face fc-front">\n                <span class="fc-label">QUESTION</span>\n                <span class="fc-tag" id="fc-tag-f">Tag</span>\n                <p class="fc-q" id="fc-q">—</p>\n                <span class="fc-hint">Click or press <kbd>Space</kbd> to reveal answer</span>\n              </div>\n              <div class="fc-face fc-back">\n                <span class="fc-label fc-label-back">ANSWER</span>\n                <span class="fc-tag fc-tag-back" id="fc-tag-b">Tag</span>\n                <p class="fc-a" id="fc-a">—</p>\n                <span class="fc-hint fc-hint-back">Rate yourself below</span>\n              </div>\n            </div>\n          </div>\n\n          <!-- Controls -->\n          <div class="study-controls">\n            <button class="sc-btn sc-skip"  onclick="skipCard()">→ Skip</button>\n            <button class="sc-btn sc-again" id="sc-again" onclick="rateCard(\'again\')" disabled>✗ Again</button>\n            <button class="sc-btn sc-know"  id="sc-know"  onclick="rateCard(\'know\')"  disabled>✓ Got It</button>\n          </div>\n\n          <!-- Session live count -->\n          <div class="sess-row">\n            <span class="sess-know">✓ <strong id="sess-know">0</strong></span>\n            <span class="sess-again">✗ <strong id="sess-again">0</strong></span>\n            <span class="sess-left">Left: <strong id="sess-left">0</strong></span>\n          </div>\n\n          <!-- Keyboard hints -->\n          <div class="kbd-row">\n            <span><kbd>Space</kbd> Flip</span>\n            <span><kbd>K</kbd> Got it</span>\n            <span><kbd>L</kbd> Again</span>\n            <span><kbd>→</kbd> Skip</span>\n          </div>\n        </div>\n\n        <!-- Completion -->\n        <div class="completion" id="st-done" style="display:none">\n          <div class="comp-icon" id="comp-icon">🎉</div>\n          <h2 class="comp-title" id="comp-title">Round Complete!</h2>\n          <p class="comp-sub" id="comp-sub"></p>\n          <div class="result-bars">\n            <div class="rbar">\n              <div class="rbar-label"><span>✓ Got It</span><span id="rb-know-val">0/0</span></div>\n              <div class="rbar-track"><div class="rbar-fill rbar-green" id="rb-know" style="width:0%"></div></div>\n            </div>\n            <div class="rbar">\n              <div class="rbar-label"><span>↺ Again</span><span id="rb-again-val">0/0</span></div>\n              <div class="rbar-track"><div class="rbar-fill rbar-red" id="rb-again" style="width:0%"></div></div>\n            </div>\n          </div>\n          <div class="comp-btns">\n            <button class="btn btn-outline" onclick="goto(\'decks\')">📚 Decks</button>\n            <button class="btn btn-outline" onclick="restartStudy()">↺ Retry All</button>\n            <button class="btn btn-primary" onclick="retryWrong()">🔄 Review Wrong</button>\n          </div>\n        </div>\n\n      </main>\n    </div>\n  </section>\n</div>\n\n<!-- ░░ DECK MODAL ░░ -->\n<div class="overlay" id="deck-overlay">\n  <div class="modal">\n    <div class="modal-head">\n      <h3 class="modal-title" id="dm-title">New Deck</h3>\n      <button class="modal-close" onclick="closeDeckModal()">✕</button>\n    </div>\n    <div class="modal-body">\n      <div class="field"><label>Deck Name *</label><input id="dm-name" type="text" placeholder="e.g. Computer Networks, DBMS…"/></div>\n      <div class="field"><label>Icon</label><div class="emoji-grid" id="dm-emoji-grid"></div></div>\n      <div class="field"><label>Color</label><div class="color-row" id="dm-color-row"></div></div>\n      <div class="modal-footer">\n        <button class="btn btn-outline" onclick="closeDeckModal()">Cancel</button>\n        <button class="btn btn-primary" onclick="saveDeck()">Save Deck</button>\n      </div>\n    </div>\n  </div>\n</div>\n\n<!-- ░░ CARD MODAL ░░ -->\n<div class="overlay" id="card-overlay">\n  <div class="modal modal-wide">\n    <div class="modal-head">\n      <h3 class="modal-title" id="cm-title">Add Card</h3>\n      <button class="modal-close" onclick="closeCardModal()">✕</button>\n    </div>\n    <div class="modal-body">\n      <div class="field"><label>Deck *</label><select id="cm-deck"></select></div>\n      <div class="field-row">\n        <div class="field"><label>Question (Front) *</label><textarea id="cm-q" placeholder="e.g. What is a Semaphore?"></textarea></div>\n        <div class="field"><label>Answer (Back) *</label><textarea id="cm-a" placeholder="e.g. A sync primitive used to control…"></textarea></div>\n      </div>\n      <div class="field"><label>Tag <small>(optional)</small></label><input id="cm-tag" type="text" placeholder="e.g. Chapter 3, Week 2"/></div>\n      <div class="modal-footer">\n        <button class="btn btn-outline" onclick="closeCardModal()">Cancel</button>\n        <button class="btn btn-primary" onclick="saveCard()">Save Card</button>\n      </div>\n    </div>\n  </div>\n</div>\n\n<!-- ░░ API LOG ░░ -->\n<div class="api-log" id="api-log">\n  <div class="api-log-head">\n    <span>🐍 API Calls — Python Backend</span>\n    <button onclick="toggleApiLog()">✕</button>\n  </div>\n  <div class="api-log-body" id="api-log-body"></div>\n</div>\n\n<!-- ░░ TOAST ░░ -->\n<div class="toast" id="toast"></div>\n\n<script>\n/**\n * FlashCard App — Frontend JavaScript\n * All data comes from the Python backend via fetch() REST API calls\n * Backend: http://localhost:5000\n */\n\nconst API_BASE = "";   // same origin — Python serves both API + static files\n\n// ── API CLIENT ────────────────────────────────────────────────\nconst api = {\n  async get(path) {\n    addLog("GET", path);\n    const res = await fetch(API_BASE + "/api" + path);\n    if (!res.ok) throw new Error(await res.text());\n    return res.json();\n  },\n\n  async post(path, data) {\n    addLog("POST", path);\n    const res = await fetch(API_BASE + "/api" + path, {\n      method: "POST",\n      headers: { "Content-Type": "application/json" },\n      body: JSON.stringify(data),\n    });\n    if (!res.ok) throw new Error(await res.text());\n    return res.json();\n  },\n\n  async put(path, data) {\n    addLog("PUT", path);\n    const res = await fetch(API_BASE + "/api" + path, {\n      method: "PUT",\n      headers: { "Content-Type": "application/json" },\n      body: JSON.stringify(data),\n    });\n    if (!res.ok) throw new Error(await res.text());\n    return res.json();\n  },\n\n  async del(path) {\n    addLog("DELETE", path);\n    const res = await fetch(API_BASE + "/api" + path, { method: "DELETE" });\n    if (!res.ok) throw new Error(await res.text());\n    return res.json();\n  },\n};\n\n// ── STATE ─────────────────────────────────────────────────────\nlet allDecks      = [];\nlet allCards      = [];\nlet currentView   = "home";\nlet deckFilter    = "all";\nlet statusFilter  = "all";\n\nlet editingDeckId = null;\nlet editingCardId = null;\nlet selEmoji      = "📚";\nlet selColor      = "blue";\n\nconst EMOJIS = ["🧩","💻","🧮","📚","🔬","🌍","⚗️","🎵","🧬","📐","🔭","🎯","🧠","📖","⚽","🌿","🔐","🧪"];\nconst COLORS  = ["blue","green","amber","purple","red"];\nconst CHEX    = { blue:"#2d6be4", green:"#1f8a5e", amber:"#b07820", purple:"#6b3fa0", red:"#c0392b" };\n\nconst study = {\n  deckId:     null,\n  queue:      [],\n  idx:        0,\n  knowCount:  0,\n  againCount: 0,\n  isFlipped:  false,\n  shuffleOn:  false,\n};\n\n// ── NAVIGATION ────────────────────────────────────────────────\nfunction goto(view) {\n  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));\n  document.querySelectorAll(".nav-tab").forEach(t => t.classList.remove("active"));\n  document.getElementById("view-" + view).classList.add("active");\n  document.getElementById("tab-" + view).classList.add("active");\n  currentView = view;\n\n  if (view === "home")  loadHome();\n  if (view === "decks") loadDecks();\n  if (view === "study") loadStudySidebar();\n}\n\n// ── HOME ──────────────────────────────────────────────────────\nasync function loadHome() {\n  // Parallel API calls\n  const [stats, decks] = await Promise.all([\n    api.get("/stats"),\n    api.get("/decks"),\n  ]);\n  allDecks = decks;\n\n  // Stats\n  document.getElementById("home-stats").innerHTML = `\n    <div class="stat-card">\n      <div class="stat-val" style="color:var(--blue)">${stats.total_decks}</div>\n      <div class="stat-lbl">📚 Decks</div>\n    </div>\n    <div class="stat-card">\n      <div class="stat-val" style="color:var(--purple)">${stats.total_cards}</div>\n      <div class="stat-lbl">🃏 Cards</div>\n    </div>\n    <div class="stat-card">\n      <div class="stat-val" style="color:var(--green)">${stats.known}</div>\n      <div class="stat-lbl">✓ Mastered</div>\n    </div>\n    <div class="stat-card">\n      <div class="stat-val" style="color:var(--amber)">${stats.mastered_pct}%</div>\n      <div class="stat-lbl">📈 Progress</div>\n    </div>`;\n\n  // Decks grid\n  document.getElementById("home-decks").innerHTML =\n    decks.map(d => deckCardHTML(d)).join("") +\n    `<div class="add-deck-card" onclick="openDeckModal()">\n      <div style="font-size:30px">＋</div>New Deck\n    </div>`;\n}\n\nfunction deckCardHTML(d) {\n  return `\n  <div class="deck-card dc-${d.color}">\n    <div class="dc-top">\n      <div class="dc-emoji">${d.emoji}</div>\n      <div class="dc-menu">\n        <button class="dc-menu-btn" onclick="event.stopPropagation();editDeck(\'${d.id}\')" title="Edit">✏️</button>\n        <button class="dc-menu-btn" onclick="event.stopPropagation();deleteDeck(\'${d.id}\')" title="Delete">🗑</button>\n      </div>\n    </div>\n    <div class="dc-name">${esc(d.name)}</div>\n    <div class="dc-meta">${d.card_count} card${d.card_count !== 1 ? "s" : ""} · ${d.mastered_pct}% mastered</div>\n    <div class="dc-pbar"><div class="dc-pbar-fill" style="width:${d.mastered_pct}%"></div></div>\n    <div class="dc-btns">\n      <button class="dc-btn" onclick="event.stopPropagation();openDeckCards(\'${d.id}\')">📋 Cards</button>\n      <button class="dc-btn study" onclick="event.stopPropagation();startStudy(\'${d.id}\')">▶ Study</button>\n    </div>\n  </div>`;\n}\n\n// ── DECKS PAGE ────────────────────────────────────────────────\nasync function loadDecks() {\n  const [decks, cards] = await Promise.all([\n    api.get("/decks"),\n    api.get("/cards"),\n  ]);\n  allDecks = decks;\n  allCards = cards;\n\n  // Deck grid\n  document.getElementById("decks-grid").innerHTML =\n    decks.map(d => deckCardHTML(d)).join("") +\n    `<div class="add-deck-card" onclick="openDeckModal()"><div style="font-size:30px">＋</div>New Deck</div>`;\n\n  // Deck filter chips\n  document.getElementById("deck-chips").innerHTML =\n    `<button class="chip${deckFilter==="all"?" active":""}" onclick="setDeckFilter(\'all\',this)">All Decks</button>` +\n    decks.map(d =>\n      `<button class="chip${deckFilter===d.id?" active":""}" onclick="setDeckFilter(\'${d.id}\',this)">${d.emoji} ${esc(d.name)}</button>`\n    ).join("");\n\n  renderCardsTable();\n}\n\nfunction setDeckFilter(id, btn) {\n  deckFilter = id;\n  document.querySelectorAll("#deck-chips .chip").forEach(b => b.classList.remove("active"));\n  btn.classList.add("active");\n  renderCardsTable();\n}\n\nfunction setStatusFilter(s, btn) {\n  statusFilter = s;\n  document.querySelectorAll(".status-chips .chip").forEach(b => b.classList.remove("active"));\n  btn.classList.add("active");\n  renderCardsTable();\n}\n\nfunction openDeckCards(deckId) {\n  deckFilter = deckId;\n  goto("decks");\n}\n\nfunction renderCardsTable() {\n  let cards = allCards;\n  if (deckFilter !== "all")   cards = cards.filter(c => c.deck_id === deckFilter);\n  if (statusFilter !== "all") cards = cards.filter(c => c.status  === statusFilter);\n\n  const el = document.getElementById("cards-table");\n  if (!cards.length) {\n    el.innerHTML = `<div class="empty-state"><div class="ei">🃏</div><h3>No cards here</h3><p>Add a card to get started</p><button class="btn btn-primary" onclick="openCardModal()">＋ Add Card</button></div>`;\n    return;\n  }\n\n  el.innerHTML = cards.map(c => {\n    const dotCls  = c.status === "known" ? "dot-known" : c.status === "again" ? "dot-again" : "dot-new";\n    const statLbl = c.status === "known" ? "✓ Known"   : c.status === "again" ? "↺ Again"   : "🆕 New";\n    return `\n    <div class="card-row">\n      <div class="cr-dot ${dotCls}"></div>\n      <div class="cr-body">\n        <div class="cr-q">${esc(c.question)}</div>\n        <div class="cr-a">${esc(c.answer)}</div>\n      </div>\n      ${c.tag ? `<span class="cr-tag">#${esc(c.tag)}</span>` : ""}\n      <span class="cr-status ${c.status}">${statLbl}</span>\n      <div class="cr-actions">\n        <button class="icon-btn" onclick="editCard(\'${c.id}\')">✏️</button>\n        <button class="icon-btn del" onclick="deleteCard(\'${c.id}\')">🗑</button>\n      </div>\n    </div>`;\n  }).join("");\n}\n\n// ── STUDY ─────────────────────────────────────────────────────\nasync function loadStudySidebar() {\n  const decks = await api.get("/decks");\n  allDecks = decks;\n\n  document.getElementById("aside-decks").innerHTML = decks.map(d => `\n    <div class="aside-deck-item${study.deckId === d.id ? " active" : ""}" onclick="selectStudyDeck(\'${d.id}\')">\n      <div class="adi-emoji">${d.emoji}</div>\n      <div class="adi-body">\n        <div class="adi-name">${esc(d.name)}</div>\n        <div class="adi-meta">${d.card_count} cards · ${d.mastered_pct}%</div>\n      </div>\n    </div>`).join("");\n\n  // Auto-select first deck\n  if (!study.deckId && decks.length) selectStudyDeck(decks[0].id);\n}\n\nasync function selectStudyDeck(deckId) {\n  study.deckId = deckId;\n  document.querySelectorAll(".aside-deck-item").forEach(el => el.classList.remove("active"));\n  document.querySelectorAll(".aside-deck-item").forEach(el => {\n    if (el.getAttribute("onclick")?.includes(deckId)) el.classList.add("active");\n  });\n  await startStudy(deckId);\n}\n\nasync function startStudy(deckId) {\n  if (currentView !== "study") { goto("study"); return; }\n  study.deckId     = deckId;\n  study.isFlipped  = false;\n  study.idx        = 0;\n  study.knowCount  = 0;\n  study.againCount = 0;\n\n  const cards = await api.get(`/cards?deck_id=${deckId}`);\n\n  // Priority order: new → again → known\n  const ordered = [\n    ...cards.filter(c => c.status === "new"),\n    ...cards.filter(c => c.status === "again"),\n    ...cards.filter(c => c.status === "known"),\n  ];\n\n  study.queue = study.shuffleOn ? shuffle(ordered) : ordered;\n\n  hideAllStudyStates();\n  if (!cards.length) { document.getElementById("st-empty").style.display = "block"; return; }\n  document.getElementById("st-card").style.display = "flex";\n\n  const deck = allDecks.find(d => d.id === deckId);\n  document.getElementById("deck-label").textContent = deck ? `${deck.emoji}  ${deck.name}` : "";\n\n  showStudyCard();\n  updateSidebarStats();\n}\n\nfunction showStudyCard() {\n  const { queue, idx } = study;\n  if (!queue.length || idx >= queue.length) { showCompletion(); return; }\n\n  study.isFlipped = false;\n  document.getElementById("flashcard").classList.remove("flipped");\n  document.getElementById("sc-know").disabled  = true;\n  document.getElementById("sc-again").disabled = true;\n\n  const c     = queue[idx];\n  const total = queue.length;\n  const pct   = Math.round((idx / total) * 100);\n\n  document.getElementById("fc-q").textContent    = c.question;\n  document.getElementById("fc-a").textContent    = c.answer;\n  document.getElementById("fc-tag-f").textContent = c.tag || "Card";\n  document.getElementById("fc-tag-b").textContent = c.tag || "Card";\n  document.getElementById("prog-text").textContent = `${idx + 1} / ${total}`;\n  document.getElementById("prog-pct").textContent  = pct + "%";\n  document.getElementById("prog-bar").style.width  = pct + "%";\n\n  renderDots();\n  updateSidebarStats();\n  document.getElementById("sess-know").textContent  = study.knowCount;\n  document.getElementById("sess-again").textContent = study.againCount;\n  document.getElementById("sess-left").textContent  = total - idx;\n}\n\nfunction flipCard() {\n  if (!study.queue.length || study.idx >= study.queue.length) return;\n  study.isFlipped = !study.isFlipped;\n  document.getElementById("flashcard").classList.toggle("flipped", study.isFlipped);\n  document.getElementById("sc-know").disabled  = !study.isFlipped;\n  document.getElementById("sc-again").disabled = !study.isFlipped;\n}\n\nasync function rateCard(result) {\n  const card = study.queue[study.idx];\n  const newStatus = result === "know" ? "known" : "again";\n\n  // PUT to Python backend\n  await api.put(`/cards/${card.id}`, { status: newStatus });\n  card.status = newStatus;   // update local copy too\n\n  if (result === "know") study.knowCount++;\n  else study.againCount++;\n\n  study.idx++;\n  if (study.idx >= study.queue.length) showCompletion();\n  else showStudyCard();\n}\n\nfunction skipCard() {\n  study.idx++;\n  if (study.idx >= study.queue.length) showCompletion();\n  else showStudyCard();\n}\n\nfunction restartStudy() {\n  hideAllStudyStates();\n  document.getElementById("st-card").style.display = "flex";\n  startStudy(study.deckId);\n}\n\nasync function retryWrong() {\n  const cards = await api.get(`/cards?deck_id=${study.deckId}&status=again`);\n  if (!cards.length) { showToast("🎉 No wrong cards — all mastered!"); return; }\n  study.queue      = shuffle(cards);\n  study.idx        = 0;\n  study.knowCount  = 0;\n  study.againCount = 0;\n  study.isFlipped  = false;\n  hideAllStudyStates();\n  document.getElementById("st-card").style.display = "flex";\n  showStudyCard();\n}\n\nfunction showCompletion() {\n  hideAllStudyStates();\n  const total = study.queue.length || 1;\n  const kPct  = Math.round((study.knowCount  / total) * 100);\n  const aPct  = Math.round((study.againCount / total) * 100);\n\n  let icon, title, sub;\n  if (kPct === 100)    { icon = "🏆"; title = "Perfect Score!";    sub = "Every single card nailed. Outstanding!"; }\n  else if (kPct >= 75) { icon = "🎉"; title = "Great Job!";         sub = `${study.knowCount} of ${total} correct. Keep it up!`; }\n  else if (kPct >= 50) { icon = "💪"; title = "Good Effort!";       sub = `${study.knowCount} of ${total}. Review the ones you missed.`; }\n  else                  { icon = "📖"; title = "Keep Practicing!";   sub = `${study.knowCount} of ${total}. Practice makes perfect!`; }\n\n  document.getElementById("comp-icon").textContent  = icon;\n  document.getElementById("comp-title").textContent = title;\n  document.getElementById("comp-sub").textContent   = sub;\n  document.getElementById("rb-know-val").textContent  = `${study.knowCount}/${total}`;\n  document.getElementById("rb-again-val").textContent = `${study.againCount}/${total}`;\n  document.getElementById("st-done").style.display = "flex";\n  document.getElementById("st-done").style.flexDirection = "column";\n  document.getElementById("st-done").style.alignItems = "center";\n\n  document.getElementById("prog-bar").style.width = "100%";\n  document.getElementById("prog-pct").textContent = "100%";\n  renderDots();\n\n  setTimeout(() => {\n    document.getElementById("rb-know").style.width  = kPct + "%";\n    document.getElementById("rb-again").style.width = aPct + "%";\n  }, 100);\n}\n\nfunction hideAllStudyStates() {\n  ["st-pick","st-empty","st-card","st-done"].forEach(id => {\n    document.getElementById(id).style.display = "none";\n  });\n}\n\nfunction renderDots() {\n  const el = document.getElementById("dots-row");\n  el.innerHTML = study.queue.map((c, i) => {\n    let cls = "dot";\n    if (i < study.idx)      cls += c.status === "known" ? " known" : " again";\n    else if (i === study.idx) cls += " curr";\n    return `<div class="${cls}"></div>`;\n  }).join("");\n}\n\nfunction updateSidebarStats() {\n  document.getElementById("sb-know").textContent  = study.knowCount;\n  document.getElementById("sb-again").textContent = study.againCount;\n  document.getElementById("sb-rem").textContent   = Math.max(0, study.queue.length - study.idx);\n}\n\nfunction toggleShuffle() {\n  study.shuffleOn = !study.shuffleOn;\n  const el = document.getElementById("shuffle-val");\n  el.textContent = study.shuffleOn ? "ON" : "OFF";\n  el.classList.toggle("on", study.shuffleOn);\n  if (study.deckId) { showToast(study.shuffleOn ? "Shuffle ON 🔀" : "Shuffle OFF"); startStudy(study.deckId); }\n}\n\n// ── DECK MODAL ────────────────────────────────────────────────\nfunction openDeckModal(id = null) {\n  editingDeckId = id;\n  const deck = id ? allDecks.find(d => d.id === id) : null;\n  selEmoji = deck?.emoji || EMOJIS[0];\n  selColor = deck?.color || "blue";\n\n  document.getElementById("dm-title").textContent = deck ? "Edit Deck" : "New Deck";\n  document.getElementById("dm-name").value = deck?.name || "";\n\n  document.getElementById("dm-emoji-grid").innerHTML = EMOJIS.map(e =>\n    `<div class="emoji-opt${e === selEmoji ? " on" : ""}" onclick="pickEmoji(\'${e}\')">${e}</div>`\n  ).join("");\n\n  document.getElementById("dm-color-row").innerHTML = COLORS.map(c =>\n    `<div class="color-dot${c === selColor ? " on" : ""}" style="background:${CHEX[c]}" onclick="pickColor(\'${c}\')"></div>`\n  ).join("");\n\n  document.getElementById("deck-overlay").classList.add("show");\n  setTimeout(() => document.getElementById("dm-name").focus(), 80);\n}\n\nfunction editDeck(id) { openDeckModal(id); }\nfunction closeDeckModal() { document.getElementById("deck-overlay").classList.remove("show"); }\nfunction pickEmoji(e) { selEmoji = e; document.querySelectorAll("#dm-emoji-grid .emoji-opt").forEach(el => el.classList.toggle("on", el.textContent === e)); }\nfunction pickColor(c) { selColor = c; document.querySelectorAll("#dm-color-row .color-dot").forEach((el, i) => el.classList.toggle("on", COLORS[i] === c)); }\n\nasync function saveDeck() {\n  const name = document.getElementById("dm-name").value.trim();\n  if (!name) { showToast("Enter a deck name!"); return; }\n  const payload = { name, emoji: selEmoji, color: selColor };\n\n  try {\n    if (editingDeckId) {\n      await api.put(`/decks/${editingDeckId}`, payload);\n      showToast("Deck updated ✓");\n    } else {\n      await api.post("/decks", payload);\n      showToast("Deck created 🎉");\n    }\n    closeDeckModal();\n    if (currentView === "home")  loadHome();\n    if (currentView === "decks") loadDecks();\n    if (currentView === "study") loadStudySidebar();\n  } catch (e) { showToast("Error saving deck"); }\n}\n\nasync function deleteDeck(id) {\n  if (!confirm("Delete this deck and all its cards?")) return;\n  try {\n    await api.del(`/decks/${id}`);\n    showToast("Deck deleted.");\n    if (study.deckId === id) study.deckId = null;\n    if (currentView === "home")  loadHome();\n    if (currentView === "decks") loadDecks();\n  } catch (e) { showToast("Error deleting deck"); }\n}\n\n// ── CARD MODAL ────────────────────────────────────────────────\nfunction openCardModal(deckId = null) {\n  editingCardId = null;\n  document.getElementById("cm-title").textContent = "Add Card";\n  document.getElementById("cm-q").value = "";\n  document.getElementById("cm-a").value = "";\n  document.getElementById("cm-tag").value = "";\n\n  const preferred = deckId || deckFilter !== "all" ? deckFilter : allDecks[0]?.id;\n  document.getElementById("cm-deck").innerHTML = allDecks.map(d =>\n    `<option value="${d.id}" ${d.id === preferred ? "selected" : ""}>${d.emoji} ${esc(d.name)}</option>`\n  ).join("");\n\n  document.getElementById("card-overlay").classList.add("show");\n  setTimeout(() => document.getElementById("cm-q").focus(), 80);\n}\n\nfunction editCard(id) {\n  const card = allCards.find(c => c.id === id);\n  if (!card) return;\n  editingCardId = id;\n\n  document.getElementById("cm-title").textContent = "Edit Card";\n  document.getElementById("cm-q").value   = card.question;\n  document.getElementById("cm-a").value   = card.answer;\n  document.getElementById("cm-tag").value = card.tag || "";\n\n  document.getElementById("cm-deck").innerHTML = allDecks.map(d =>\n    `<option value="${d.id}" ${d.id === card.deck_id ? "selected" : ""}>${d.emoji} ${esc(d.name)}</option>`\n  ).join("");\n\n  document.getElementById("card-overlay").classList.add("show");\n  setTimeout(() => document.getElementById("cm-q").focus(), 80);\n}\n\nfunction closeCardModal() { document.getElementById("card-overlay").classList.remove("show"); }\n\nasync function saveCard() {\n  const question = document.getElementById("cm-q").value.trim();\n  const answer   = document.getElementById("cm-a").value.trim();\n  const deck_id  = document.getElementById("cm-deck").value;\n  const tag      = document.getElementById("cm-tag").value.trim();\n\n  if (!question || !answer) { showToast("Fill in question and answer!"); return; }\n\n  try {\n    if (editingCardId) {\n      await api.put(`/cards/${editingCardId}`, { question, answer, deck_id, tag });\n      showToast("Card updated ✓");\n    } else {\n      await api.post("/cards", { question, answer, deck_id, tag });\n      showToast("Card added 🃏");\n    }\n    closeCardModal();\n    loadDecks();\n  } catch (e) { showToast("Error saving card"); }\n}\n\nasync function deleteCard(id) {\n  if (!confirm("Delete this card?")) return;\n  try {\n    await api.del(`/cards/${id}`);\n    showToast("Card deleted.");\n    loadDecks();\n  } catch (e) { showToast("Error deleting card"); }\n}\n\n// ── API LOG ────────────────────────────────────────────────────\nfunction addLog(method, path) {\n  const el = document.createElement("div");\n  el.className = `log-entry log-${method.toLowerCase()}`;\n  el.textContent = `${new Date().toLocaleTimeString()}  ${method.padEnd(6)}  /api${path}`;\n  const body = document.getElementById("api-log-body");\n  body.prepend(el);\n  while (body.children.length > 30) body.removeChild(body.lastChild);\n}\n\nfunction toggleApiLog() {\n  document.getElementById("api-log").classList.toggle("show");\n}\n\n// ── UTILS ─────────────────────────────────────────────────────\nfunction esc(s) { return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }\nfunction shuffle(arr) { return [...arr].sort(() => Math.random() - 0.5); }\n\nfunction showToast(msg) {\n  const t = document.getElementById("toast");\n  t.textContent = msg;\n  t.classList.add("show");\n  clearTimeout(t._t);\n  t._t = setTimeout(() => t.classList.remove("show"), 2400);\n}\n\n// ── KEYBOARD ──────────────────────────────────────────────────\ndocument.addEventListener("keydown", e => {\n  if (["INPUT","TEXTAREA","SELECT"].includes(e.target.tagName)) return;\n  if (currentView !== "study") return;\n  if (e.key === " " || e.key === "ArrowUp") { e.preventDefault(); flipCard(); }\n  if (e.key === "ArrowRight") skipCard();\n  if ((e.key === "k" || e.key === "K") && study.isFlipped) rateCard("know");\n  if ((e.key === "l" || e.key === "L") && study.isFlipped) rateCard("again");\n});\n\n// ── CLOSE OVERLAYS ON BACKDROP CLICK ─────────────────────────\ndocument.querySelectorAll(".overlay").forEach(o => {\n  o.addEventListener("click", e => { if (e.target === o) o.classList.remove("show"); });\n});\n\n// ── BOOT ──────────────────────────────────────────────────────\nwindow.addEventListener("load", () => loadHome());\n\n</script>\n</body>\n</html>\n'

# ─── REQUEST HANDLER ──────────────────────────────────────────

class FlashCardHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"  [{self.command}] {self.path}  →  {args[1] if len(args)>1 else ''}")

    # ── CORS & common headers ──────────────────────────────────

    def send_json(self, code, data):
        body = json.dumps(data, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, code, message):
        self.send_json(code, {"error": message})

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ── ROUTING ───────────────────────────────────────────────

    def route(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)
        # flatten single-value params
        params = {k: v[0] for k, v in params.items()}
        return path, params

    # ── GET ───────────────────────────────────────────────────

    def do_GET(self):
        path, params = self.route()

        # Static files
        if not path.startswith("/api"):
            self.serve_static(path)
            return

        conn = get_db()
        try:
            # GET /api/stats
            if path == "/api/stats":
                c = conn.cursor()
                total  = c.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
                known  = c.execute("SELECT COUNT(*) FROM cards WHERE status='known'").fetchone()[0]
                again  = c.execute("SELECT COUNT(*) FROM cards WHERE status='again'").fetchone()[0]
                new    = c.execute("SELECT COUNT(*) FROM cards WHERE status='new'").fetchone()[0]
                decks  = c.execute("SELECT COUNT(*) FROM decks").fetchone()[0]
                self.send_json(200, {
                    "total_decks":   decks,
                    "total_cards":   total,
                    "known":         known,
                    "again":         again,
                    "new":           new,
                    "mastered_pct":  round(known / total * 100) if total > 0 else 0,
                })

            # GET /api/decks
            elif path == "/api/decks":
                c = conn.cursor()
                decks = c.execute("SELECT id FROM decks ORDER BY created_at").fetchall()
                result = [deck_with_stats(row["id"], conn) for row in decks]
                self.send_json(200, result)

            # GET /api/decks/<id>
            elif path.startswith("/api/decks/"):
                deck_id = path.split("/api/decks/")[1]
                result = deck_with_stats(deck_id, conn)
                if not result:
                    self.send_error_json(404, "Deck not found")
                else:
                    self.send_json(200, result)

            # GET /api/cards
            elif path == "/api/cards":
                c = conn.cursor()
                query  = "SELECT * FROM cards WHERE 1=1"
                args   = []
                if "deck_id" in params:
                    query += " AND deck_id=?"; args.append(params["deck_id"])
                if "status" in params:
                    query += " AND status=?";  args.append(params["status"])
                query += " ORDER BY created_at"
                rows = c.execute(query, args).fetchall()
                self.send_json(200, rows_to_list(rows))

            # GET /api/cards/<id>
            elif path.startswith("/api/cards/"):
                card_id = path.split("/api/cards/")[1]
                c = conn.cursor()
                row = c.execute("SELECT * FROM cards WHERE id=?", (card_id,)).fetchone()
                if not row:
                    self.send_error_json(404, "Card not found")
                else:
                    self.send_json(200, row_to_dict(row))

            else:
                self.send_error_json(404, "Route not found")

        finally:
            conn.close()

    # ── POST ──────────────────────────────────────────────────

    def do_POST(self):
        path, _ = self.route()
        body = self.read_json_body()
        conn = get_db()
        try:
            # POST /api/decks
            if path == "/api/decks":
                if not body.get("name"):
                    self.send_error_json(400, "name is required"); return
                deck_id = str(uuid.uuid4())
                conn.execute(
                    "INSERT INTO decks(id,name,emoji,color) VALUES(?,?,?,?)",
                    (deck_id, body["name"], body.get("emoji","📚"), body.get("color","blue"))
                )
                conn.commit()
                self.send_json(201, deck_with_stats(deck_id, conn))

            # POST /api/cards
            elif path == "/api/cards":
                required = ["question", "answer", "deck_id"]
                missing  = [f for f in required if not body.get(f)]
                if missing:
                    self.send_error_json(400, f"Missing fields: {', '.join(missing)}"); return
                card_id = str(uuid.uuid4())
                conn.execute(
                    "INSERT INTO cards(id,deck_id,question,answer,tag,status) VALUES(?,?,?,?,?,?)",
                    (card_id, body["deck_id"], body["question"], body["answer"],
                     body.get("tag",""), body.get("status","new"))
                )
                conn.commit()
                row = conn.execute("SELECT * FROM cards WHERE id=?", (card_id,)).fetchone()
                self.send_json(201, row_to_dict(row))

            else:
                self.send_error_json(404, "Route not found")

        finally:
            conn.close()

    # ── PUT ───────────────────────────────────────────────────

    def do_PUT(self):
        path, _ = self.route()
        body = self.read_json_body()
        conn = get_db()
        try:
            # PUT /api/decks/<id>
            if path.startswith("/api/decks/"):
                deck_id = path.split("/api/decks/")[1]
                row = conn.execute("SELECT id FROM decks WHERE id=?", (deck_id,)).fetchone()
                if not row:
                    self.send_error_json(404, "Deck not found"); return
                fields = {k: v for k, v in body.items() if k in ("name","emoji","color")}
                if fields:
                    set_clause = ", ".join(f"{k}=?" for k in fields)
                    conn.execute(
                        f"UPDATE decks SET {set_clause} WHERE id=?",
                        list(fields.values()) + [deck_id]
                    )
                    conn.commit()
                self.send_json(200, deck_with_stats(deck_id, conn))

            # PUT /api/cards/<id>
            elif path.startswith("/api/cards/"):
                card_id = path.split("/api/cards/")[1]
                row = conn.execute("SELECT id FROM cards WHERE id=?", (card_id,)).fetchone()
                if not row:
                    self.send_error_json(404, "Card not found"); return
                fields = {k: v for k, v in body.items() if k in ("question","answer","tag","status","deck_id")}
                if fields:
                    set_clause = ", ".join(f"{k}=?" for k in fields)
                    conn.execute(
                        f"UPDATE cards SET {set_clause} WHERE id=?",
                        list(fields.values()) + [card_id]
                    )
                    conn.commit()
                row = conn.execute("SELECT * FROM cards WHERE id=?", (card_id,)).fetchone()
                self.send_json(200, row_to_dict(row))

            else:
                self.send_error_json(404, "Route not found")

        finally:
            conn.close()

    # ── DELETE ────────────────────────────────────────────────

    def do_DELETE(self):
        path, _ = self.route()
        conn = get_db()
        try:
            # DELETE /api/decks/<id>
            if path.startswith("/api/decks/"):
                deck_id = path.split("/api/decks/")[1]
                row = conn.execute("SELECT id FROM decks WHERE id=?", (deck_id,)).fetchone()
                if not row:
                    self.send_error_json(404, "Deck not found"); return
                conn.execute("DELETE FROM cards WHERE deck_id=?", (deck_id,))
                conn.execute("DELETE FROM decks WHERE id=?",      (deck_id,))
                conn.commit()
                self.send_json(200, {"success": True, "deleted_id": deck_id})

            # DELETE /api/cards/<id>
            elif path.startswith("/api/cards/"):
                card_id = path.split("/api/cards/")[1]
                row = conn.execute("SELECT id FROM cards WHERE id=?", (card_id,)).fetchone()
                if not row:
                    self.send_error_json(404, "Card not found"); return
                conn.execute("DELETE FROM cards WHERE id=?", (card_id,))
                conn.commit()
                self.send_json(200, {"success": True, "deleted_id": card_id})

            else:
                self.send_error_json(404, "Route not found")

        finally:
            conn.close()

    # ── STATIC FILE SERVER ────────────────────────────────────

    def serve_static(self, path):
        # All frontend is embedded — just serve the single HTML page
        if path in ("/", "", "/index.html"):
            content = FRONTEND_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")


# ─── ENTRY POINT ──────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    server = http.server.HTTPServer(("", PORT), FlashCardHandler)

    print(f"""
╔══════════════════════════════════════════╗
║      FlashCard App — Python Backend      ║
╚══════════════════════════════════════════╝

  🌐  http://localhost:{PORT}

  REST API Endpoints:
  ──────────────────────────────────────────
  GET     /api/stats
  GET     /api/decks
  POST    /api/decks
  PUT     /api/decks/<id>
  DELETE  /api/decks/<id>
  GET     /api/cards?deck_id=&status=
  POST    /api/cards
  PUT     /api/cards/<id>
  DELETE  /api/cards/<id>
  ──────────────────────────────────────────

  Press Ctrl+C to stop
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
