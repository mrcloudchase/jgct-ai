#!/usr/bin/env python3
"""Ledger of every source item found, processed, unreachable, or skipped.

Backed by SQLite at state/ledger.sqlite. Never open the DB by hand; use this CLI.

  python3 tools/ledger.py add --id pmid:12345 --title "..." --year 2020 [--status found] [--priority 50] [--origin "pubmed search X"]
  python3 tools/ledger.py set pmid:12345 --status processed [--note "..."] [--record pmid-12345]
  python3 tools/ledger.py get pmid:12345
  python3 tools/ledger.py list [--status found] [--limit 30] [--order priority|year]
  python3 tools/ledger.py stats
  python3 tools/ledger.py search "AKT1"

Statuses: found, processed, unreachable, skipped.
Priority: higher = process sooner (series/genomic/guideline ~80+, review ~60, case report ~30).
"""
import argparse, os, sqlite3, sys, datetime

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "state", "ledger.sqlite")
STATUSES = ("found", "processed", "unreachable", "skipped")


def conn():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS items(
        id TEXT PRIMARY KEY, title TEXT, year INTEGER, pubtype TEXT,
        status TEXT NOT NULL DEFAULT 'found', priority INTEGER DEFAULT 0,
        origin TEXT, record TEXT, note TEXT, first_seen TEXT, updated TEXT)""")
    return c


def today():
    return datetime.date.today().isoformat()


def add(c, id, title=None, year=None, pubtype=None, status="found", priority=0, origin=None):
    """Insert if absent. Returns True if new. Never downgrades an existing item."""
    cur = c.execute("SELECT status FROM items WHERE id=?", (id,)).fetchone()
    if cur:
        c.execute("UPDATE items SET title=COALESCE(title,?), year=COALESCE(year,?), pubtype=COALESCE(pubtype,?), priority=MAX(priority,?) WHERE id=?",
                  (title, year, pubtype, priority, id))
        return False
    c.execute("INSERT INTO items(id,title,year,pubtype,status,priority,origin,first_seen,updated) VALUES(?,?,?,?,?,?,?,?,?)",
              (id, title, year, pubtype, status, priority, origin, today(), today()))
    return True


def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest="cmd", required=True)
    a = s.add_parser("add"); a.add_argument("--id", required=True); a.add_argument("--title"); a.add_argument("--year", type=int)
    a.add_argument("--pubtype"); a.add_argument("--status", default="found", choices=STATUSES); a.add_argument("--priority", type=int, default=0); a.add_argument("--origin")
    st = s.add_parser("set"); st.add_argument("id"); st.add_argument("--status", choices=STATUSES); st.add_argument("--note"); st.add_argument("--record"); st.add_argument("--priority", type=int)
    g = s.add_parser("get"); g.add_argument("id")
    l = s.add_parser("list"); l.add_argument("--status"); l.add_argument("--limit", type=int, default=30); l.add_argument("--order", default="priority", choices=("priority", "year"))
    s.add_parser("stats")
    se = s.add_parser("search"); se.add_argument("q")
    args = p.parse_args()
    c = conn()
    if args.cmd == "add":
        print("added" if add(c, args.id, args.title, args.year, args.pubtype, args.status, args.priority, args.origin) else "exists")
    elif args.cmd == "set":
        if not c.execute("SELECT 1 FROM items WHERE id=?", (args.id,)).fetchone():
            add(c, args.id)
        for col in ("status", "note", "record", "priority"):
            v = getattr(args, col)
            if v is not None:
                c.execute(f"UPDATE items SET {col}=?, updated=? WHERE id=?", (v, today(), args.id))
        print("ok")
    elif args.cmd == "get":
        r = c.execute("SELECT * FROM items WHERE id=?", (args.id,)).fetchone()
        cols = [d[0] for d in c.execute("SELECT * FROM items LIMIT 0").description]
        print(dict(zip(cols, r)) if r else "not found")
    elif args.cmd == "list":
        q = "SELECT id,status,priority,year,pubtype,substr(title,1,110),note FROM items"
        params = ()
        if args.status:
            q += " WHERE status=?"; params = (args.status,)
        q += " ORDER BY " + ("priority DESC, year DESC" if args.order == "priority" else "year DESC")
        q += " LIMIT ?"
        for r in c.execute(q, params + (args.limit,)):
            print(" | ".join("" if x is None else str(x) for x in r))
    elif args.cmd == "stats":
        for r in c.execute("SELECT status,count(*) FROM items GROUP BY status"):
            print(*r)
    elif args.cmd == "search":
        for r in c.execute("SELECT id,status,priority,year,substr(title,1,110) FROM items WHERE title LIKE ? OR note LIKE ? ORDER BY priority DESC",
                           (f"%{args.q}%", f"%{args.q}%")):
            print(" | ".join("" if x is None else str(x) for x in r))
    c.commit()


if __name__ == "__main__":
    main()
