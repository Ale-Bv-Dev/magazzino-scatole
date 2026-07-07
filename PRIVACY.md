# Informativa sulla privacy — Magazzino Scatole

Informativa resa ai sensi degli artt. 13–14 del Regolamento (UE) 2016/679 ("GDPR") per gli utenti dell'app Magazzino Scatole.

**Ultimo aggiornamento:** 7 luglio 2026

## 1. Titolare del trattamento

Alessandro (GitHub: [Ale-Bv-Dev](https://github.com/Ale-Bv-Dev))
Contatto per ogni richiesta relativa ai dati: **magazzino.scatole.app@proton.me**

Si tratta di un progetto personale senza finalità commerciali.

## 2. Dati trattati

L'app raccoglie il minimo indispensabile al funzionamento:

| Dato | Dettaglio |
|---|---|
| Nome utente | Scelto liberamente in fase di registrazione. Non è richiesta email, nome reale o altro dato identificativo. |
| PIN | Salvato esclusivamente come hash Argon2, mai in chiaro. Non è recuperabile. |
| Dati di inventario | Contenuto, quantità, misura, posizione e note delle scatole catalogate. |
| Log tecnici | Generati automaticamente dai fornitori di hosting (indirizzo IP, orari di accesso) per sicurezza e funzionamento del servizio. |

**Raccomandazione (minimizzazione):** scegliere un nome utente che non permetta di identificarti e non inserire dati personali propri o di terzi nelle note o negli altri campi.

## 3. Finalità e base giuridica

| Finalità | Base giuridica |
|---|---|
| Registrazione, autenticazione e gestione del proprio archivio | Esecuzione del servizio richiesto (art. 6.1.b GDPR) |
| Sicurezza e prevenzione abusi (log tecnici) | Legittimo interesse (art. 6.1.f GDPR) |

Nessuna profilazione, nessun processo decisionale automatizzato, nessuna finalità di marketing, nessuna cessione a terzi.

## 4. Dove sono i dati (responsabili del trattamento)

| Fornitore | Ruolo | Riferimenti |
|---|---|---|
| Supabase Inc. | Database (dati di inventario e account) | [Privacy](https://supabase.com/privacy) · [DPA](https://supabase.com/legal/dpa) |
| Streamlit Community Cloud (Snowflake Inc.) | Hosting dell'applicazione | [Privacy](https://www.snowflake.com/privacy-policy/) |

L'infrastruttura di questi fornitori può trovarsi anche al di fuori dell'Unione Europea. Gli eventuali trasferimenti extra-UE sono disciplinati dagli strumenti previsti dal Capo V del GDPR (clausole contrattuali standard e/o EU-U.S. Data Privacy Framework), come indicato nelle rispettive DPA.

## 5. Conservazione

I dati restano finché l'account esiste. La cancellazione di una scatola la rimuove definitivamente dal database. Su richiesta a magazzino.scatole.app@proton.me l'account e tutti i dati associati vengono cancellati senza ingiustificato ritardo.

## 6. Diritti dell'interessato (artt. 15–22 GDPR)

Hai diritto di ottenere accesso, rettifica, cancellazione, limitazione, portabilità dei tuoi dati e di opporti al trattamento, scrivendo a **magazzino.scatole.app@proton.me**. Hai inoltre diritto di proporre reclamo al Garante per la protezione dei dati personali ([www.garanteprivacy.it](https://www.garanteprivacy.it)).

## 7. Cookie

L'app utilizza esclusivamente cookie tecnici di sessione necessari al funzionamento di Streamlit. Nessun cookie di profilazione o di terze parti a fini pubblicitari.

## 8. Minori

Il servizio non è destinato a minori di 14 anni.

## 9. Sicurezza

PIN salvato solo come hash Argon2; credenziali di accesso al database custodite fuori dal repository e mai pubblicate; accesso ai dati filtrato per utente a livello applicativo. Il livello di protezione è commisurato alla natura del servizio (catalogo di magazzino, senza dati sensibili): vedi anche [SECURITY.md](SECURITY.md).

## 10. Modifiche

Eventuali modifiche a questa informativa sono pubblicate in questo file; la data di ultimo aggiornamento è indicata in testa.
