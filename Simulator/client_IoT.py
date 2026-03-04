import asyncio
import json
import time
import websockets
import os
import random
from dotenv import load_dotenv
from Crypto_Pub_Secret.crypto import Nostr

load_dotenv()


class Simulatore_Centralina:

    # connettiamoci al relay attraverso il nostro canale web socket, inserendo le chiavi
    def __init__(self, relay_url="ws://127.0.0.1:8008"):
        self.relay_url = relay_url

        #chiave segreta conservata nel file env (come se fosse un wallet)
        self.nsec = os.getenv("NSEC_CENTRALINA")

        if not self.nsec:
            raise ValueError("Errore: Chiave segreta non trovata nel file .env. Eseguire prima setup_centralina.py")

        # genero la chiave pubblica dalla mia privata
        self.npub = Nostr.get_pubkey_from_env(self.nsec)

        self.fault_mode = False  #Se True simuliamo il guasto

        self.battery_level = 100.0  #livello batteria iniziale

        self.lat = 37.5023  #Coordinate geografiche (Catania)
        self.lon = 15.0873

        self.sensor_id = "centralina"  #id hardware univoco

    async def send_data(self, flow, current, moisture, status="OK", kind_IoT=None):
        try:
            #Aggiunto timeout di 10 secondi per evitare che il terminale rimanga vuoto all'avvio
            async with asyncio.timeout(10):
                async with websockets.connect(self.relay_url) as ws:
                    timestamp = int(time.time())

                    #facciamo calare di 0.1% la batteria a ogni invio
                    self.battery_level = max(0, self.battery_level - 0.1)

                    content = f"Stato del sistema {status}: Umidità {moisture}%"


                    event_kind = kind_IoT if kind_IoT is not None else 9001

                    #i vari tag
                    tags = [
                        ["t", "telemetria_avanzata"],
                        ["d", self.sensor_id],
                        ["g", f"{self.lat},{self.lon}"],
                        ["flow", str(flow)],
                        ["amp", str(current)],
                        ["battery", f"{self.battery_level:.1f}"],
                        ["status", status]
                    ]

                    #generiamo l'id (stringa hex di 64 caratteri)
                    #Usiamo Kind 9001 che sarebbe diverso da 1 proprio riservato alla telemetria
                    event_id = Nostr.get_event_id(self.npub, timestamp, event_kind, tags, content)

                    #firmiamo e restituisce una stringa hex di 128 caratteri
                    signature = Nostr.sign_event(self.nsec, event_id)

                    #costruiamo l' evento json
                    event = {
                        "id": str(event_id),
                        "pubkey": str(self.npub),
                        "created_at": timestamp,
                        "kind": event_kind, # Usiamo il kind determinato dinamicamente
                        "tags": tags,
                        "content": content,
                        "sig": str(signature)
                    }

                    # Invio al Relay
                    await ws.send(json.dumps(["EVENT", event]))
                    print(f"Inviato Kind {event_kind}: {status} | Batt: {self.battery_level:.1f}% | ID: {event_id[:8]}...")

                    response = await ws.recv()
                    print(f"Risposta Relay: {response}")

        except Exception as e:
            print(f"Errore durante l'invio: {e}")

    async def run(self):
        print(f"Centralina {self.sensor_id} avviata. Pubkey: {self.npub}")

        await self.send_data(flow=0, current=0, moisture=0, status="avviamento del sistema", kind_IoT=1)

        #ogni 4 eventi facciamo scattare un allarme
        count = 0
        while True:
            count += 1

            # Umidità dinamica per non avere sempre lo stesso valore nella dashboard
            moisture_var = random.randint(40, 50)

            if count % 4 == 0:
                # In caso di guasto, mandiamo popup (Kind 9001) e blocco meccanico (Kind 1)
                await self.send_data(flow=0.0, current=0.9, moisture=moisture_var, status="popup")
                #aspetto 1 secondo per non sovrascrivere il timestamp
                await asyncio.sleep(1.1)

                await self.send_data(flow=0.0, current=0.9, moisture=moisture_var, status="blocco meccanico",
                                     kind_IoT=1)
            else:
                flow_var = round(5.5 + random.uniform(-0.5, 0.5), 2)
                # Invio normale telemetria Kind 9001
                await self.send_data(flow=flow_var, current=0.7, moisture=moisture_var, status="OK")

            await asyncio.sleep(5)


if __name__ == "__main__":
    sim = Simulatore_Centralina()
    asyncio.run(sim.run())