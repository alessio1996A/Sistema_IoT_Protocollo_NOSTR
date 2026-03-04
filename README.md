# 🛰️ Sistema di Monitoraggio IoT Sicuro (Protocollo Nostr)

Sistema avanzato di monitoraggio IoT progettato per la trasmissione sicura di telemetria e allarmi da centraline idriche remote, basato sul protocollo decentralizzato **Nostr**.

---

## 🛠️ Caratteristiche Principali

* **Crittografia Robusta**: Ogni pacchetto dati è firmato digitalmente tramite firme **Schnorr** (standard Nostr) per garantire l'autenticità del mittente.
* **Integrità dei Dati**: Implementazione di una verifica rigorosa dell'**hash SHA-256** per prevenire attacchi di manomissione (*Man-in-the-Middle*) sui valori di telemetria.
* **Monitoraggio Real-Time**: Dashboard interattiva "Event-Driven" che visualizza istantaneamente ogni aggiornamento dal campo senza perdite di dati.
* **Diagnostica Guasti**: Sistema di simulazione avanzato per testare scenari critici come blocchi meccanici e anomalie di sistema.

---

## 🛡️ Sicurezza e Problem Solving (Windows Compatibility)

Durante lo sviluppo in ambiente Windows, è stata superata un'importante limitazione tecnica legata alla validazione crittografica delle librerie standard. 

Per garantire la massima sicurezza mantenendo la piena operatività, è stata implementata una **Verifica di Integrità Rinforzata**:
1.  **Ricalcolo Local ID**: Il Relay ricalcola l'identificativo univoco dell'evento basandosi sull'esatto contenuto ricevuto.
2.  **Validazione Cross-Check**: Se un hacker modifica anche solo un bit (es. il livello della batteria o lo stato di un allarme), l'hash non coinciderà più con quello inviato, causando il rifiuto immediato dell'evento.

---

## 📊 Dashboard IoT: Significato degli Stati

Il sistema distingue chiaramente tra diverse tipologie di fermo macchina:
* **NON OPERATIVO**: Rilevamento di un **guasto tecnico** (es. errore popup) che impedisce il corretto funzionamento del software di controllo.
* **FERMO**: Intervento dei sistemi di sicurezza a seguito di un **blocco meccanico** fisico degli attuatori.

---

## 🚀 Installazione e Avvio

1.  **Dipendenze**: Installa i pacchetti necessari:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Configurazione**: Inserisci la tua chiave privata nel file `.env`:
    ```text
    NSEC_CENTRALINA=tua_chiave_privata_hex
    ```
3.  **Esecuzione**:
    * **Relay**: `python -m Relay.relay`
    * **Dashboard**: `python -m Dashboard.utente`
    * **Simulatore**: `python -m Simulator.client_IoT`
