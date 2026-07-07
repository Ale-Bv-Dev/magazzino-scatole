# 📦 Magazzino Scatole

App Streamlit per catalogare scatole di ferramenta/falegnameria: numero scatola, contenuto, quantità, categoria, misura, posizione in magazzino e note.

Multi-utente: ogni persona si registra con nome utente + PIN e vede **solo il proprio archivio**, da qualsiasi dispositivo. Tutto su servizi gratuiti (Streamlit Community Cloud + Supabase free tier).

## Architettura

```
Browser (client 1) ─┐
Browser (client 2) ─┼─► Streamlit Cloud (app, stateless) ─► Supabase (DB)
Browser (client N) ─┘        filtra per user_id di chi è loggato
```

## Setup — circa 15 minuti

### 1. Crea il database su Supabase

1. Vai su [supabase.com](https://supabase.com) → account gratuito → **New project** (scegli una password qualsiasi per il DB, non servirà all'app).
2. Nel progetto: menu **SQL Editor** → incolla tutto il contenuto di `schema.sql` → **Run**.
3. Menu **Project Settings → API**: copia **Project URL** e la chiave **anon public**.

### 2. Metti il codice su GitHub

1. Crea un repository (anche privato) su [github.com](https://github.com).
2. Carica `app.py` e `requirements.txt` (basta *Add file → Upload files* dal browser).

### 3. Deploy su Streamlit Cloud

1. Vai su [share.streamlit.io](https://share.streamlit.io) → accedi con GitHub → **New app**.
2. Scegli il repository, branch `main`, file `app.py`.
3. **Advanced settings → Secrets**, incolla (con i tuoi valori):

   ```toml
   SUPABASE_URL = "https://xxxxxxxx.supabase.co"
   SUPABASE_KEY = "la-tua-chiave-anon"
   ```

4. **Deploy**. Dopo 1–2 minuti l'app è online a un indirizzo tipo `https://tuonome-magazzino.streamlit.app`.

### 4. Primo utilizzo

Apri l'app → scheda **Registrati** → scegli nome utente e PIN → accedi e inizia a catalogare. Chiunque altro col link può registrarsi e avrà il proprio archivio separato.

## Test in locale (opzionale)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
mkdir -p .streamlit
# crea .streamlit/secrets.toml con SUPABASE_URL e SUPABASE_KEY
.venv/bin/streamlit run app.py
```

## Note

- **Limiti free tier**: Supabase 500 MB DB; Streamlit Cloud mette l'app in pausa dopo inattività — al primo accesso riparte in ~30 secondi.
- **Sicurezza**: il PIN è salvato con Argon2, mai in chiaro. Login e campi hanno limiti lato applicazione e database. Dettagli in [SECURITY.md](SECURITY.md).
- **Backup**: da Supabase, **Table Editor → boxes → Export CSV** quando vuoi una copia locale.

## Privacy e licenza

- Informativa privacy per gli utenti dell'app: [PRIVACY.md](PRIVACY.md)
- Segnalazione vulnerabilità: [SECURITY.md](SECURITY.md)
- Codice rilasciato con licenza [MIT](LICENSE)
