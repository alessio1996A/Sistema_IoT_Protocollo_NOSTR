import asyncio
import json
import websockets
import time
from Crypto_Pub_Secret.crypto import Nostr


#il monitor è un client che si sottoscrive al relay per recuperare le informazioni del client IoT
async def monitor(relay_url="ws://127.0.0.1:8008"):
    try:
        async with websockets.connect(relay_url) as ws:
            #mi sottoscrivo ad ogni singolo evento
            await ws.send(json.dumps(["REQ", "live_all", {"kinds": [1, 9001]}]))

            print("\n" + "=" * 115)
            print(" STATO CENTRALINA IN TEMPO REALE [Premi CTRL+C per uscire]")
            print("=" * 115)
            #stampiamo in ogni colonna i nostri dati della centralina
            print(
                f"{'DATA/ORA':<10} | {'BATT':<6} | {'UMID':<6} | {'FLUSSO':<8} | {'AMP':<6} | {'STATO':<18} | {'ALLARMI'}")
            print("-" * 115)

            while True:
                response = await ws.recv()
                data = json.loads(response)

                if data[0] == "EVENT":
                    event = data[2]
                    if Nostr.verify_signature(event['pubkey'], event['id'], event['sig']):
                        data_ora = time.strftime('%H:%M:%S', time.localtime(event['created_at']))

                        #Inizializzazione variabili telemetria
                        batt, umid, flusso, amp, stato, alert = "--", "--", "--", "--", "OPERATIVO", "NESSUNO"


                        if "Umidità" in event['content']:
                            umid = event['content'].split("Umidità ")[1].split("%")[0] + "%"

                        #lettura dei tag per Flusso, Corrente e Batteria
                        for tag in event['tags']:
                            if tag[0] == 'battery': batt = f"{tag[1]}%"
                            if tag[0] == 'flow': flusso = f"{tag[1]} L/m"
                            if tag[0] == 'amp': amp = f"{tag[1]} A"
                            if tag[0] == 'status':
                                s_val = tag[1].lower()
                                if "popup" in s_val:
                                    alert = "GUASTO POP-UP"
                                    stato = "NON OPERATIVO"
                                elif "ok" in s_val:
                                    stato = "OPERATIVO"


                        if event['kind'] == 1:
                            if "blocco" in event['content'].lower():
                                alert = "BLOCCO MECCANICO"
                                stato = "FERMO"


                        print(
                            f"{data_ora:<10} | {batt:<6} | {umid:<6} | {flusso:<8} | {amp:<6} | {stato:<18} | {alert}")

    except KeyboardInterrupt:
        print("\n\n Monitoraggio terminato")
    except Exception as e:
        print(f"\n Errore: {e}")


if __name__ == "__main__":
    asyncio.run(monitor())