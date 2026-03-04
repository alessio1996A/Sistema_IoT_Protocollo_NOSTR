import sqlite3
import json
import time


class RelayDatabase:

    def __init__(self, db_path="relay_data.db"):

        self.db_path = db_path
        self._create_table()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    #creazione del database strutturato per il nip-01, l id (hash) come chiave primaria
    def _create_table(self):

        with self._get_connection() as conn:

            conn.execute('''
                         CREATE TABLE IF NOT EXISTS events
                         (
                             id TEXT PRIMARY KEY,
                             pubkey TEXT,
                             created_at INTEGER,
                             kind INTEGER,
                             tags TEXT,
                             content TEXT,
                             sig TEXT
                         )
                         ''')

            # Indice sulla Pubkey: fondamentale per velocizzare la ricerca (REQ)
            conn.execute('CREATE INDEX IF NOT EXISTS idx_pubkey ON events(pubkey)')

            # Indice sul Kind, utile se vogliamo filtrare solo gli allarmi.
            conn.execute('CREATE INDEX IF NOT EXISTS idx_kind ON events(kind)')


#salviamo l evento nel database solo se viene verificata la firma
    def save_event(self, event):

        try:
            with self._get_connection() as conn:
                conn.execute('''
                             INSERT INTO events (id, pubkey, created_at, kind, tags, content, sig)
                             VALUES (?, ?, ?, ?, ?, ?, ?)
                             ''', (
                                 event['id'],
                                 event['pubkey'],
                                 event['created_at'],
                                 event['kind'],
                                 json.dumps(event['tags']),
                                 event['content'],
                                 event['sig']
                             ))
                return True
        except sqlite3.IntegrityError:
            return False


#recuperiamo gli eventi
    def fetch_events(self, pubkey=None, kind=None, limit=50):
        query = "SELECT * FROM events WHERE 1=1"
        params = []

        if pubkey:
            query += " AND pubkey = ?"
            params.append(pubkey)
        if kind is not None:
            query += " AND kind = ?"
            params.append(kind)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            # Trasformiamo le tuple del database in una lista di dizionari Nostr validi
            rows = cursor.fetchall()
            events = []
            for row in rows:
                events.append({
                    "id": row[0],
                    "pubkey": row[1],
                    "created_at": row[2],
                    "kind": row[3],
                    "tags": json.loads(row[4]),
                    "content": row[5],
                    "sig": row[6]
                })
            return events

    #affinche il database non si saturi mettiamo che i dati rimangono per 7 giorni
    def delete_old_events(self, days=7):

        try:
            # Calcoliamo il timestamp di 7 giorni fa (7 giorni * 24h * 3600s)
            cutoff_timestamp = int(time.time()) - (days * 24 * 3600)

            with self._get_connection() as conn:
                cursor = conn.execute("DELETE FROM events WHERE created_at < ?", (cutoff_timestamp,))
                deleted_count = cursor.rowcount
                if deleted_count > 0:
                    print(f"Eliminati {deleted_count} eventi più vecchi di {days} giorni.")
                return deleted_count
        except Exception as e:
            print(f"Errore durante la pulizia del database: {e}")
            return 0