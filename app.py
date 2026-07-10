"""
Magazzino Scatole — catalogo scatole di ferramenta/falegnameria.
Streamlit + Supabase (free tier). Login leggero nome utente + PIN:
ogni utente vede e gestisce solo le proprie scatole.
Campi a selezione (valori già usati + '➕ Nuovo…'); solo Note a testo libero.
"""

import hashlib
import hmac
import math
import re
import time
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher, exceptions as argon2_exceptions
import streamlit as st
from supabase import create_client

# ---------------------------------------------------------------- config

st.set_page_config(page_title="Magazzino Scatole", page_icon="📦", layout="wide")

CATEGORIE = [
    "Viti", "Chiodi", "Tasselli", "Bulloni/Dadi", "Rondelle",
    "Ferramenta", "Falegnameria", "Elettrico", "Altro",
]
NUOVO = "➕ Nuovo…"
NESSUNA = "— nessuna —"

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 40
PIN_MIN_LENGTH = 6
PIN_MAX_LENGTH = 64
BOX_NUMBER_MAX = 9999
QUANTITY_MAX = 1_000_000
CONTENT_MAX_LENGTH = 120
CATEGORY_MAX_LENGTH = 40
SIZE_MAX_LENGTH = 80
LOCATION_MAX_LENGTH = 80
NOTES_MAX_LENGTH = 500
MAX_USERS = 25
MAX_BOXES_PER_USER = 1000
LOGIN_LOCK_THRESHOLD = 5
LOGIN_LOCK_MAX_MINUTES = 60

USERNAME_RE = re.compile(r"^[a-z0-9_.-]+$")
PASSWORD_HASHER = PasswordHasher()


@st.cache_resource
def get_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


sb = None


def init_client():
    global sb
    if sb is None:
        sb = get_client()

# ---------------------------------------------------------------- auth


def normalizza_username(username: str) -> str:
    return username.strip().lower()


def username_valido(username: str) -> bool:
    return (
        USERNAME_MIN_LENGTH <= len(username) <= USERNAME_MAX_LENGTH
        and bool(USERNAME_RE.fullmatch(username))
    )


def pin_registrazione_valido(pin: str) -> bool:
    return PIN_MIN_LENGTH <= len(pin) <= PIN_MAX_LENGTH and pin.isdigit()


def hash_pin(pin: str) -> str:
    return PASSWORD_HASHER.hash(pin)


def hash_pin_legacy(username: str, pin: str) -> str:
    return hashlib.sha256(f"{username}:{pin}".encode()).hexdigest()


def verifica_pin(username: str, pin: str, pin_hash: str) -> tuple[bool, bool]:
    """Ritorna (valido, va_ricalcolato). Supporta migrazione da SHA-256 legacy."""
    if pin_hash.startswith("$argon2"):
        try:
            PASSWORD_HASHER.verify(pin_hash, pin)
            return True, PASSWORD_HASHER.check_needs_rehash(pin_hash)
        except (
            argon2_exceptions.InvalidHashError,
            argon2_exceptions.VerificationError,
            argon2_exceptions.VerifyMismatchError,
        ):
            return False, False

    legacy = hash_pin_legacy(username, pin)
    if hmac.compare_digest(pin_hash, legacy):
        return True, True
    return False, False


def parse_timestamp(value) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def blocco_attivo(attempt: dict | None) -> tuple[bool, int]:
    locked_until = parse_timestamp((attempt or {}).get("locked_until"))
    if not locked_until:
        return False, 0
    now = datetime.now(timezone.utc)
    if locked_until <= now:
        return False, 0
    minutes = max(1, math.ceil((locked_until - now).total_seconds() / 60))
    return True, minutes


def minuti_blocco(failed_attempts: int) -> int | None:
    if failed_attempts < LOGIN_LOCK_THRESHOLD:
        return None
    return min(LOGIN_LOCK_MAX_MINUTES, 2 ** (failed_attempts - LOGIN_LOCK_THRESHOLD))


def carica_tentativi_login(username: str) -> dict | None:
    res = sb.table("login_attempts").select("*").eq("username", username).execute()
    return res.data[0] if res.data else None


def registra_login_fallito(username: str, attempt: dict | None):
    now = datetime.now(timezone.utc)
    failed_attempts = min(100, int((attempt or {}).get("failed_attempts") or 0) + 1)
    lock_minutes = minuti_blocco(failed_attempts)
    locked_until = now + timedelta(minutes=lock_minutes) if lock_minutes else None
    sb.table("login_attempts").upsert(
        {
            "username": username,
            "failed_attempts": failed_attempts,
            "locked_until": locked_until.isoformat() if locked_until else None,
            "last_attempt_at": now.isoformat(),
        },
        on_conflict="username",
    ).execute()


def reset_tentativi_login(username: str):
    sb.table("login_attempts").delete().eq("username", username).execute()


def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def vista_login():
    st.title("📦 Magazzino Scatole")
    st.caption("Accedi con il tuo nome utente e PIN. Ogni utente ha il proprio archivio.")
    tab_login, tab_reg = st.tabs(["🔑 Accedi", "🆕 Registrati"])

    with tab_login:
        with st.form("form_login"):
            u = normalizza_username(
                st.text_input("Nome utente", max_chars=USERNAME_MAX_LENGTH)
            )
            p = st.text_input("PIN", type="password", max_chars=PIN_MAX_LENGTH)
            if st.form_submit_button("Accedi", use_container_width=True):
                if not username_valido(u) or not p:
                    st.error("Nome utente o PIN errati.")
                    return
                try:
                    attempt = carica_tentativi_login(u)
                    locked, minutes = blocco_attivo(attempt)
                    if locked:
                        st.error(f"Troppi tentativi. Riprova tra {minutes} min.")
                        return

                    res = (
                        sb.table("users")
                        .select("id, username, pin_hash")
                        .eq("username", u)
                        .execute()
                    )
                    user = res.data[0] if res.data else None
                    valido = False
                    needs_rehash = False
                    if user:
                        valido, needs_rehash = verifica_pin(u, p, user["pin_hash"])

                    if user and valido:
                        if needs_rehash:
                            nuovo_hash = hash_pin(p)
                            sb.table("users").update({"pin_hash": nuovo_hash}).eq(
                                "id", user["id"]
                            ).execute()
                            user["pin_hash"] = nuovo_hash
                        reset_tentativi_login(u)
                        st.session_state.user = user
                        st.rerun()

                    registra_login_fallito(u, attempt)
                    st.error("Nome utente o PIN errati.")
                except Exception:
                    st.error("Accesso temporaneamente non disponibile. Riprova tra poco.")

    with tab_reg:
        with st.form("form_reg"):
            u = normalizza_username(
                st.text_input("Scegli un nome utente", max_chars=USERNAME_MAX_LENGTH)
            )
            p1 = st.text_input(
                "Scegli un PIN (min. 6 cifre)",
                type="password",
                max_chars=PIN_MAX_LENGTH,
            )
            p2 = st.text_input(
                "Ripeti il PIN",
                type="password",
                max_chars=PIN_MAX_LENGTH,
            )
            st.markdown(
                "[Informativa privacy](https://github.com/Ale-Bv-Dev/magazzino-scatole/blob/main/PRIVACY.md)"
            )
            if st.form_submit_button("Crea account", use_container_width=True):
                if not username_valido(u):
                    st.error(
                        "Nome utente: 3-40 caratteri, solo lettere, numeri, punto, trattino o underscore."
                    )
                elif not pin_registrazione_valido(p1):
                    st.error("Il PIN deve contenere almeno 6 cifre.")
                elif p1 != p2:
                    st.error("I due PIN non coincidono.")
                else:
                    try:
                        utenti = sb.table("users").select("id").execute().data or []
                        if len(utenti) >= MAX_USERS:
                            st.error("Limite account raggiunto.")
                        elif sb.table("users").select("id").eq("username", u).execute().data:
                            st.error("Nome utente già in uso.")
                        else:
                            sb.table("users").insert(
                                {"username": u, "pin_hash": hash_pin(p1)}
                            ).execute()
                            st.success("Account creato! Ora accedi dalla scheda 'Accedi'.")
                    except Exception:
                        st.error("Registrazione non riuscita. Riprova tra poco.")


# ---------------------------------------------------------------- dati


def carica_scatole(user_id: str) -> list[dict]:
    return (
        sb.table("boxes").select("*").eq("user_id", user_id)
        .order("box_number").execute().data
    )


# ---------------------------------------------------------------- form scatola


def valori_usati(scatole: list[dict], campo: str) -> list[str]:
    """Valori distinti già usati dall'utente per un campo."""
    return sorted({(x.get(campo) or "").strip() for x in scatole} - {""})


def campo_selezione(container, label, opzioni, attuale, key, con_vuoto, max_chars):
    """Selectbox (valori già usati + '➕ Nuovo…') con campo testo di supporto.

    Il testo viene considerato solo se nella selectbox è scelto '➕ Nuovo…':
    niente scrittura libera, ma resta una via controllata per i valori nuovi.
    """
    opts = ([NESSUNA] if con_vuoto else []) + list(opzioni) + [NUOVO]
    if attuale and attuale not in opts:
        opts.insert(1 if con_vuoto else 0, attuale)
    if attuale:
        idx = opts.index(attuale)
    else:
        idx = 0 if con_vuoto else len(opts) - 1
    sel = container.selectbox(label, opts, index=idx, key=f"sel_{key}")
    nuovo = container.text_input(
        f"{label} — nuovo valore", key=f"txt_{key}",
        placeholder=f"Compila solo se sopra hai scelto '{NUOVO}'",
        max_chars=max_chars,
    )
    if sel == NUOVO:
        return nuovo.strip()
    return "" if sel == NESSUNA else sel


def errori_scatola(dati: dict) -> list[str]:
    controlli = [
        ("content", "Contenuto", CONTENT_MAX_LENGTH),
        ("category", "Categoria", CATEGORY_MAX_LENGTH),
        ("size", "Dimensione/Misura", SIZE_MAX_LENGTH),
        ("location", "Posizione in magazzino", LOCATION_MAX_LENGTH),
        ("notes", "Note", NOTES_MAX_LENGTH),
    ]
    errori = []
    if not dati["content"]:
        errori.append(
            "Il campo Contenuto è obbligatorio: scegli una voce "
            f"oppure seleziona '{NUOVO}' e scrivi il nuovo valore."
        )
    if not 1 <= int(dati["box_number"]) <= BOX_NUMBER_MAX:
        errori.append(f"Numero scatola: scegli un valore tra 1 e {BOX_NUMBER_MAX}.")
    if not 0 <= int(dati["quantity"]) <= QUANTITY_MAX:
        errori.append(f"Quantità: scegli un valore tra 0 e {QUANTITY_MAX}.")
    for campo, label, limite in controlli:
        valore = dati.get(campo)
        if valore and len(valore) > limite:
            errori.append(f"{label}: massimo {limite} caratteri.")
    return errori


def form_scatola(user_id: str, scatole: list[dict], scatola: dict | None = None):
    """Form di inserimento (scatola=None) o modifica (scatola=dict)."""
    modifica = scatola is not None
    s = scatola or {}
    suff = f"edit_{s['id']}" if modifica else "new"
    with st.form(f"form_scatola_{suff}", clear_on_submit=not modifica):
        c1, c2, c3 = st.columns(3)
        box_number = c1.number_input(
            "Numero scatola *", min_value=1, max_value=BOX_NUMBER_MAX,
            value=int(s.get("box_number", 1)), key=f"num_{suff}",
        )
        quantity = c2.number_input(
            "Quantità pezzi *", min_value=0, max_value=QUANTITY_MAX,
            value=int(s.get("quantity", 0)), key=f"qta_{suff}",
        )
        cat_default = s.get("category") or "Viti"
        category = c3.selectbox(
            "Categoria", CATEGORIE,
            index=CATEGORIE.index(cat_default) if cat_default in CATEGORIE else 0,
            key=f"cat_{suff}",
        )

        content = campo_selezione(
            st, "Contenuto *", valori_usati(scatole, "content"),
            s.get("content") or "", f"content_{suff}", con_vuoto=False,
            max_chars=CONTENT_MAX_LENGTH,
        )
        c4, c5 = st.columns(2)
        size = campo_selezione(
            c4, "Dimensione/Misura", valori_usati(scatole, "size"),
            s.get("size") or "", f"size_{suff}", con_vuoto=True,
            max_chars=SIZE_MAX_LENGTH,
        )
        location = campo_selezione(
            c5, "Posizione in magazzino", valori_usati(scatole, "location"),
            s.get("location") or "", f"loc_{suff}", con_vuoto=True,
            max_chars=LOCATION_MAX_LENGTH,
        )
        notes = st.text_area(
            "Note",
            value=s.get("notes") or "",
            key=f"note_{suff}",
            max_chars=NOTES_MAX_LENGTH,
        )

        if st.form_submit_button(
            "💾 Salva modifiche" if modifica else "➕ Aggiungi scatola",
            use_container_width=True,
        ):
            if not modifica and len(scatole) >= MAX_BOXES_PER_USER:
                st.error("Limite scatole raggiunto per questo account.")
                return
            dati = {
                "user_id": user_id,
                "box_number": int(box_number),
                "content": content,
                "quantity": int(quantity),
                "category": category,
                "size": size or None,
                "location": location or None,
                "notes": notes.strip() or None,
            }
            errori = errori_scatola(dati)
            if errori:
                st.error(errori[0])
                return
            try:
                if modifica:
                    sb.table("boxes").update(dati).eq("id", s["id"]).eq(
                        "user_id", user_id
                    ).execute()
                    st.success(f"Scatola n. {box_number} aggiornata.")
                else:
                    sb.table("boxes").insert(dati).execute()
                    st.success(f"Scatola n. {box_number} aggiunta.")
                time.sleep(0.8)
                st.rerun()
            except Exception as e:
                if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                    st.error(f"Esiste già una scatola n. {box_number} nel tuo archivio.")
                else:
                    st.error("Salvataggio non riuscito. Riprova tra poco.")


# ---------------------------------------------------------------- app principale


def vista_principale():
    user = st.session_state.user
    try:
        scatole = carica_scatole(user["id"])
    except Exception:
        st.error("Archivio temporaneamente non disponibile. Riprova tra poco.")
        st.stop()

    with st.sidebar:
        st.markdown(f"### 👤 {user['username']}")
        st.metric("Scatole catalogate", len(scatole))
        st.metric("Pezzi totali", sum(x["quantity"] or 0 for x in scatole))
        st.divider()
        if st.button("🚪 Esci", use_container_width=True):
            logout()
            st.rerun()

    st.title("📦 Magazzino Scatole")
    tab_elenco, tab_nuova, tab_gestione = st.tabs(
        ["📋 Elenco", "➕ Nuova", "✏️ Gestisci"]
    )

    # ---- elenco e ricerca
    with tab_elenco:
        c1, c2, c3 = st.columns([2, 1, 1])
        testo = c1.text_input(
            "🔎 Cerca (contenuto, note, misura...)",
            max_chars=CONTENT_MAX_LENGTH,
        )
        f_cat = c2.multiselect("Categoria", CATEGORIE)
        posizioni = sorted({x["location"] for x in scatole if x["location"]})
        f_pos = c3.multiselect("Posizione", posizioni)

        filtrate = scatole
        if testo:
            t = testo.lower()
            filtrate = [
                x for x in filtrate
                if t in " ".join(
                    str(x.get(k) or "") for k in ("content", "notes", "size", "category", "location")
                ).lower()
                or t == str(x["box_number"])
            ]
        if f_cat:
            filtrate = [x for x in filtrate if x.get("category") in f_cat]
        if f_pos:
            filtrate = [x for x in filtrate if x.get("location") in f_pos]

        if not filtrate:
            st.info("Nessuna scatola trovata. Aggiungine una dalla scheda '➕ Nuova scatola'.")
        else:
            st.dataframe(
                [
                    {
                        "N°": x["box_number"],
                        "Contenuto": x["content"],
                        "Quantità": x["quantity"],
                        "Categoria": x.get("category") or "",
                        "Misura": x.get("size") or "",
                        "Posizione": x.get("location") or "",
                        "Note": x.get("notes") or "",
                    }
                    for x in filtrate
                ],
                use_container_width=True,
                hide_index=True,
            )

    # ---- nuova scatola
    with tab_nuova:
        num_usati = {x["box_number"] for x in scatole}
        prossimo = next(
            (i for i in range(1, BOX_NUMBER_MAX + 1) if i not in num_usati),
            None,
        )
        if len(scatole) >= MAX_BOXES_PER_USER:
            st.warning("Limite scatole raggiunto per questo account.")
        elif prossimo is None:
            st.warning("Non ci sono numeri scatola liberi.")
        else:
            st.caption(f"Suggerimento: il primo numero libero è **{prossimo}**.")
            form_scatola(user["id"], scatole)

    # ---- modifica / elimina
    with tab_gestione:
        if not scatole:
            st.info("Non hai ancora scatole da modificare.")
        else:
            sel = st.selectbox(
                "Scegli la scatola",
                scatole,
                format_func=lambda x: f"N° {x['box_number']} — {x['content']} ({x['quantity']} pz)",
            )
            form_scatola(user["id"], scatole, sel)
            st.divider()
            with st.expander("🗑️ Elimina questa scatola"):
                st.warning(f"Stai per eliminare la scatola n. {sel['box_number']}: {sel['content']}")
                if st.button("Conferma eliminazione", type="primary"):
                    try:
                        sb.table("boxes").delete().eq("id", sel["id"]).eq(
                            "user_id", user["id"]
                        ).execute()
                        st.success("Scatola eliminata.")
                        time.sleep(0.8)
                        st.rerun()
                    except Exception:
                        st.error("Eliminazione non riuscita. Riprova tra poco.")


def main():
    init_client()
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user is None:
        vista_login()
    else:
        vista_principale()


# ---------------------------------------------------------------- entry point

if __name__ == "__main__":
    main()
