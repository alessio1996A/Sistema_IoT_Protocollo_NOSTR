from Crypto_Pub_Secret.crypto import Nostr

#se vogliamo generare nuove chiavi segrete randomiche e conservarle nel nostro env (come un wallet)
def inizializza_centralina():
    print("Generazione nuova identità (NIP-01)")
    private_key, public_key = Nostr.generate_keys()

    #scrivo auotomaticamente nel file .env
    with open(".env", "w") as f:
        f.write(f"NSEC_CENTRALINA={private_key}\n")

    print(f"Chiave segreta salvata nel file .env")
    print(f"Chiave pubblica: {public_key}")


if __name__ == "__main__":
    inizializza_centralina()