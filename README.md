# Nostr IoT Monitoring System
Sistema di monitoraggio IoT basato sul protocollo Nostr per la trasmissione sicura di telemetria e allarmi.

## Caratteristiche
- **Crittografia**: Ogni evento è firmato digitalmente (Schnorr signatures) e verificato dal Relay.
- **Integrità**: Verifica dell'hash SHA-256 per prevenire la manomissione dei dati (batteria, umidità, allarmi).
- **Real-Time**: Dashboard interattiva per il monitoraggio istantaneo tramite WebSocket.
- **Gestione Guasti**: Simulazione di popup tecnici e blocchi meccanici.

## Installazione
1. Installa le dipendenze: `pip install -r requirements.txt`
2. Configura il file `.env` con la tua chiave NSEC.
3. Avvia il Relay: `python -m Relay.relay`
4. Avvia la Dashboard: `python -m Dashboard.utente`
5. Avvia il Simulatore: `python -m Simulator.client_IoT`