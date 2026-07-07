# Security Policy

## Segnalare una vulnerabilità

Se trovi una vulnerabilità in questa app o nella sua configurazione, **non aprire una issue pubblica**. Scrivi a **magazzino.scatole.app@proton.me** descrivendo il problema e i passi per riprodurlo. Risposta indicativa entro 7 giorni.

## Ambito

- Codice in questo repository (`app.py`, `schema.sql`).
- Configurazione dell'istanza pubblica su Streamlit Community Cloud.

Fuori ambito: vulnerabilità delle piattaforme Supabase, Streamlit/Snowflake o GitHub (vanno segnalate ai rispettivi programmi).

## Modello di sicurezza (in breve)

- Autenticazione con nome utente + PIN; il PIN è salvato con Argon2. Gli hash SHA-256 legacy vengono migrati al primo login riuscito.
- Il login applica lockout temporaneo per username dopo tentativi falliti ripetuti. I campi principali hanno limiti applicativi e vincoli lato database.
- Le credenziali del database (URL e chiave anon di Supabase) vivono solo nei secrets dell'app (`.streamlit/secrets.toml` in locale, Secrets su Streamlit Cloud) e **non sono mai committate**. La chiave `service_role` non è mai usata.
- Isolamento tra utenti applicato a livello applicativo (filtro per `user_id`).
- RLS resta disattivata perché l'app usa una sessione server-side con anon key e autenticazione custom. Trade-off accettato solo per un catalogo non sensibile: se l'anon key viene compromessa, va ruotata e il modello va rivalutato.
- L'app non tratta dati sensibili: è un catalogo di magazzino.

## Versioni supportate

Solo il branch `main` (l'istanza deployata segue `main`).
