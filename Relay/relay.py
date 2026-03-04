import asyncio
import json
import websockets
from Crypto_Pub_Secret.crypto import Nostr
from Relay.database import RelayDatabase


class NostrRelay:
    def __init__(self, host="127.0.0.1", port=8008):
        self.host = host
        self.port = port
        self.db = RelayDatabase()
        self.clients_IoT = set()  # EVENT chi manda e REQ chi si sottoscrive
        self.event_counter = 0  # contiamo gli eventi (si presuppone che il server sia sempre attivo, se no si riazzera)

    # definiamo funzioni asincrone dato che siamo in comunicazione asincrona
    async def start_server(self):

        print(f"Relay Nostr IoT attivo sulla web socket:{self.host}:{self.port}")
        async with websockets.serve(self.handler, self.host, self.port):
            await asyncio.Future()

    # si possono connettere anche nuovi client_IoT alla websocket (ogni evento passa da questo canale anche di uno stesso client)
    async def handler(self, websocket):

        self.clients_IoT.add(websocket)
        print(f"Connessione alla Websocket stabilita: {websocket.remote_address}")

        try:
            async for message in websocket:
                await self.process_message(message, websocket)
        except websockets.ConnectionClosed:
            print(f"Canale Websocket chiuso: {websocket.remote_address}")
        finally:
            self.clients_IoT.remove(websocket)

    # prendiamo gli event json e li serializziamo in righe
    async def process_message(self, raw_message, websocket):

        try:
            msg = json.loads(raw_message)
            msg_type = msg[0]

            if msg_type == "EVENT":
                event = msg[1]
                await self.handle_event(event, websocket)

            elif msg_type == "REQ":
                subscription_id = msg[1]
                filters = msg[2]
                await self.handle_subscription(subscription_id, filters, websocket)

            else:
                print(f"Tipo di messaggio non supportato: {msg_type}")

        except Exception as e:
            print(f"Errore nel processare il messaggio: {e}")

    # calcoliamo l id e per essere sicuri lo verifichiamo (quello della classe Nostr )
    async def handle_event(self, event, websocket):

        # Se i dati vengono manomessi, l'id_locale sarà diverso da event['id']
        id_locale = Nostr.get_event_id(
            event['pubkey'], event['created_at'],
            event['kind'], event['tags'], event['content']
        )


        #verifichiamo la firma
        validazione = Nostr.verify_signature(event['pubkey'], event['id'], event['sig'])



        #Se l'hash non coincide, i dati sono falsi
        if event['id'] != id_locale:
            print(f"id non corrispondente al contenuto! Rifiutato.")
            await websocket.send(json.dumps(["OK", event['id'], False, "invalid: hash mismatch"]))
            return

        #Verifichiamo la validità  della firma
        if not validazione:
            print(f"Firma non valida o corrotta.")
            await websocket.send(json.dumps(["OK", event['id'], False, "invalid: signature failure"]))
            return

        # Se i controlli di integrità e firma passano, procediamo al salvataggio
        if self.db.save_event(event):

            self.event_counter += 1

            #Estrazione ID centralina dai tag
            sensor_id = "N/D"
            for tag in event['tags']:
                if tag[0] == 'd': sensor_id = tag[1]

            print(f"Centralina: {sensor_id} | Kind: {event['kind']} ricevuto e salvato.")

            if self.event_counter % 100 == 0:
                print("Soglia 100 RAGGIUNTA: Avvio pulizia automatica dati obsoleti")
                # se sono vecchi di 7 giorni li eliminiamo per fare spazio
                self.db.delete_old_events(days=7)

            await websocket.send(json.dumps(["OK", event['id'], True, "evento ricevuto"]))

            # Broadcast dell'evento a tutti gli altri client connessi
            await self.broadcast_event(event)
        else:
            await websocket.send(json.dumps(["OK", event['id'], False, "duplicato già presente"]))

    # se voglio recuperare i dati storici
    async def handle_subscription(self, sub_id, filters, websocket):
        print(f"Richiesta dati storici per la sottoscrizione: {sub_id}")
        events = self.db.fetch_events(
            pubkey=filters.get('authors', [None])[0],
            kind=filters.get('kinds', [None])[0]
        )

        for e in events:
            await websocket.send(json.dumps(["EVENT", sub_id, e]))

        # Segnaliamo la fine della trasmissione dati storici (EOSE)
        await websocket.send(json.dumps(["EOSE", sub_id]))

    # invio l evento a tutti i client in ascolto
    async def broadcast_event(self, event):
        if self.clients_IoT:
            message = json.dumps(["EVENT", "broadcast", event])

            # Creiamo una copia per evitare errori di iterazione se qualcuno si disconnette
            await asyncio.gather(*[client.send(message) for client in self.clients_IoT])


if __name__ == "__main__":
    relay = NostrRelay()
    asyncio.run(relay.start_server())