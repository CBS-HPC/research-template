from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

from .deps import DK_UNI_MAP, load_from_env, save_to_env
from .utils import DATAVERSE_SITE_CHOICES, ZENODO_API_CHOICES, is_empty_alias


TOKENS_STATE = {
    "zenodo": {"env_key": "ZENODO_TOKEN", "state_key": "__token_zenodo__"},
    "dataverse": {"env_key": "DATAVERSE_TOKEN", "state_key": "__token_dataverse__"},
}


def _get_env_or_secret(key: str, default: str = "") -> str:
    val = ""
    try:
        val = st.secrets[key]  # type: ignore[index]
    except Exception:
        val = ""
    if not val:
        val = load_from_env(key) or ""
    return val or default


def _extract_domain_candidates_from_context(dmp_data: dict[str, Any] | None) -> list[str]:
    candidates: list[str] = []
    try:
        mbox = (dmp_data or {}).get("dmp", {}).get("contact", {}).get("mbox", "")
        if isinstance(mbox, str) and "@" in mbox:
            candidates.append(mbox.split("@", 1)[1].lower())
    except Exception:
        pass

    normalized: list[str] = []
    for dom in candidates:
        for key in DK_UNI_MAP.keys():
            if dom == key or dom.endswith("." + key):
                normalized.append(key)
                break
        else:
            normalized.append(dom)
    uniq: list[str] = []
    for d in normalized:
        if d not in uniq:
            uniq.append(d)
    return uniq


def guess_dataverse_defaults_from_university(dmp_data: dict[str, Any] | None) -> tuple[str | None, str | None]:
    for dom in _extract_domain_candidates_from_context(dmp_data):
        info = DK_UNI_MAP.get(dom)
        if info:
            return info.get("dataverse_default_base_url"), info.get("dataverse_alias")
    return None, None


def _safe_get_json(url: str, params: dict | None = None, headers: dict | None = None, timeout: int = 8):
    try:
        r = requests.get(url, params=params or {}, headers=headers or {}, timeout=timeout)
        ctype = r.headers.get("Content-Type", "")
        if "application/json" in ctype:
            return r.status_code, r.json()
        return r.status_code, r.text
    except requests.exceptions.RequestException as e:
        return None, str(e)


def test_zenodo_connection(api_base: str, token: str, community: str | None = None) -> tuple[bool, str]:
    if not api_base:
        return False, "No Zenodo API base URL configured."

    status, _ = _safe_get_json(api_base.rstrip("/") + "/records", timeout=6)
    if status != 200:
        return False, f"Cannot reach Zenodo at {api_base} (HTTP {status})."

    if token:
        status, body = _safe_get_json(
            api_base.rstrip("/") + "/deposit/depositions", params={"access_token": token}, timeout=8
        )
        if status == 200:
            token_ok = True
        elif status in (401, 403):
            return False, "Zenodo reachable, but the token was rejected (401/403)."
        else:
            return False, f"Zenodo token check returned HTTP {status}: {body}"
    else:
        token_ok = False

    community = (community or "").strip()
    if community:
        status_c, body_c = _safe_get_json(api_base.rstrip("/") + f"/communities/{community}", timeout=8)
        found = False
        if status_c == 200:
            found = True
        elif status_c == 404:
            status_s, body_s = _safe_get_json(api_base.rstrip("/") + "/communities", params={"q": community, "page": 1}, timeout=8)
            if status_s == 200 and isinstance(body_s, dict):
                hits = body_s.get("hits", {})
                items = hits.get("hits", []) if isinstance(hits, dict) else hits
                for it in items or []:
                    cand = str((it or {}).get("id") or (it or {}).get("slug") or "")
                    if cand.lower() == community.lower():
                        found = True
                        break
        elif status_c in (401, 403):
            return False, f"Zenodo reachable, but access denied when checking community '{community}' (HTTP {status_c})."
        else:
            return False, f"Community check returned HTTP {status_c}."

        if not found:
            return False, f"Zenodo reachable{', token OK' if token_ok else ''}, but community '{community}' was not found."

        if token_ok:
            return True, f"Zenodo reachable ✅, token OK, and community '{community}' found."
        return True, f"Zenodo reachable ✅ and community '{community}' found (no token check)."

    if token_ok:
        return True, "Zenodo reachable ✅ and token looks valid."
    return True, "Zenodo reachable ✅ (no token provided, skipped token check)."


def test_dataverse_connection(base_url: str, token: str, alias: str) -> tuple[bool, str]:
    if not base_url:
        return False, "No Dataverse base URL configured."

    status, _ = _safe_get_json(base_url.rstrip("/") + "/api/info/version", timeout=6)
    if status != 200:
        return False, f"Cannot reach Dataverse at {base_url} (HTTP {status})."

    if token:
        status_me, _ = _safe_get_json(base_url.rstrip("/") + "/api/users/:me", params={"key": token}, timeout=8)
        if status_me != 200:
            if status_me in (401, 403):
                return False, "Dataverse reachable, but the API token was rejected (401/403)."
            return False, f"Dataverse '/users/:me' returned HTTP {status_me}."

    if alias:
        status_alias, _ = _safe_get_json(
            base_url.rstrip("/") + f"/api/dataverses/{alias}",
            params={"key": token} if token else None,
            timeout=8,
        )
        if status_alias == 200:
            if token:
                return True, "Dataverse reachable ✅, token OK, and collection (alias) found."
            return True, "Dataverse reachable ✅ and collection (alias) found (no token check)."
        elif status_alias == 404:
            return False, f"Dataverse reachable, but collection (alias '{alias}') was not found (404)."
        elif status_alias in (401, 403):
            return False, "Dataverse reachable, alias provided, but access denied (401/403)."
        else:
            return False, f"Dataverse alias check returned HTTP {status_alias}."

    if token:
        return True, "Dataverse reachable ✅ and token looks valid (no alias provided)."
    return True, "Dataverse reachable ✅ (no token or alias provided)."


def get_token_from_state(service: str) -> str:
    service = service.lower().strip()
    env_key = TOKENS_STATE[service]["env_key"]
    state_key = TOKENS_STATE[service]["state_key"]

    val = st.session_state.get(state_key, "")
    if val:
        return val
    try:
        val = st.secrets[env_key]  # type: ignore[index]
        if val:
            return val
    except Exception:
        pass
    return os.environ.get(env_key) or (load_from_env(env_key) or "")


def get_zenodo_api_base() -> str:
    return st.session_state.get("zenodo_api_base") or _get_env_or_secret("ZENODO_API_BASE", "https://sandbox.zenodo.org/api")


def get_zenodo_community() -> str:
    return (st.session_state.get("zenodo_community") or _get_env_or_secret("ZENODO_COMMUNITY", "")).strip()


def get_dataverse_config() -> tuple[str, str]:
    base = st.session_state.get("dataverse_base_url") or _get_env_or_secret("DATAVERSE_BASE_URL", "")
    alias = st.session_state.get("dataverse_alias") or _get_env_or_secret("DATAVERSE_ALIAS", "")

    if not base or not alias:
        guess_base, guess_alias = guess_dataverse_defaults_from_university(st.session_state.get("data"))
        base = base or guess_base or "https://demo.dataverse.deic.dk"
        alias = alias or guess_alias or ""
    return base, alias


def render_token_controls() -> None:
    with st.sidebar:
        st.header("Repositories & tokens")

        # --------------- Zenodo ---------------
        st.subheader("Zenodo")

        z_api_default = _get_env_or_secret("ZENODO_API_BASE", "https://sandbox.zenodo.org/api")
        if "zenodo_api_base" not in st.session_state:
            st.session_state["zenodo_api_base"] = z_api_default

        z_comm_default = _get_env_or_secret("ZENODO_COMMUNITY", "")
        if "zenodo_community" not in st.session_state:
            st.session_state["zenodo_community"] = z_comm_default

        z_token_default = _get_env_or_secret(TOKENS_STATE["zenodo"]["env_key"], "")
        if TOKENS_STATE["zenodo"]["state_key"] not in st.session_state:
            st.session_state[TOKENS_STATE["zenodo"]["state_key"]] = z_token_default

        zenodo_options = [u for (u, _label) in ZENODO_API_CHOICES]
        try:
            z_index = zenodo_options.index(st.session_state["zenodo_api_base"])
        except ValueError:
            z_index = 0

        with st.form("zenodo_settings_form", clear_on_submit=False):
            z_api = st.selectbox(
                "Site",
                options=zenodo_options,
                index=z_index,
                format_func=lambda u: dict(ZENODO_API_CHOICES)[u],
                help="Sandbox is highly recommended for testing.",
            )
            z_comm = st.text_input(
                "Community (optional)",
                value=st.session_state["zenodo_community"],
                placeholder="e.g. cbs, ku, sdu…",
                help="Community identifier (slug). Leave blank to omit.",
                key="__zen_comm__",
            )
            z_token = st.text_input(
                "API token",
                type="password",
                value=st.session_state[TOKENS_STATE["zenodo"]["state_key"]],
                help="Click Save to write to .env and update session.",
                key="__zen_token__",
            )
            z_submit = st.form_submit_button("Save settings")
            if z_submit:
                save_to_env(z_api, "ZENODO_API_BASE")
                os.environ["ZENODO_API_BASE"] = z_api
                st.session_state["zenodo_api_base"] = z_api

                if z_token.strip():
                    save_to_env(z_token.strip(), TOKENS_STATE["zenodo"]["env_key"])
                    os.environ[TOKENS_STATE["zenodo"]["env_key"]] = z_token.strip()
                    st.session_state[TOKENS_STATE["zenodo"]["state_key"]] = z_token.strip()

                st.session_state["zenodo_community"] = z_comm.strip()
                if z_comm.strip():
                    save_to_env(z_comm.strip(), "ZENODO_COMMUNITY")
                    os.environ["ZENODO_COMMUNITY"] = z_comm.strip()

                eff_api = st.session_state.get("zenodo_api_base", z_api)
                eff_token = st.session_state.get(TOKENS_STATE["zenodo"]["state_key"], z_token.strip())
                eff_comm = (st.session_state.get("zenodo_community") or "").strip()

                ok, msg = test_zenodo_connection(eff_api, eff_token, eff_comm)
                (st.success if ok else st.error)(msg)

        # --------------- Dataverse ---------------
        st.subheader("Dataverse")

        dv_base_default = _get_env_or_secret("DATAVERSE_BASE_URL", "")
        dv_alias_default = _get_env_or_secret("DATAVERSE_ALIAS", "")

        if not dv_base_default or not dv_alias_default:
            guess_base, guess_alias = guess_dataverse_defaults_from_university(st.session_state.get("data"))
            if not dv_base_default:
                dv_base_default = guess_base or "https://demo.dataverse.deic.dk"
            if not dv_alias_default:
                dv_alias_default = guess_alias or ""

        dv_token_default = _get_env_or_secret(TOKENS_STATE["dataverse"]["env_key"], "")

        if "dataverse_base_url" not in st.session_state:
            st.session_state["dataverse_base_url"] = dv_base_default
        if "dataverse_site_choice" not in st.session_state:
            if "demo.dataverse.deic.dk" in dv_base_default:
                st.session_state["dataverse_site_choice"] = "https://demo.dataverse.deic.dk"
            elif "dataverse.deic.dk" in dv_base_default:
                st.session_state["dataverse_site_choice"] = "https://dataverse.deic.dk"
            else:
                st.session_state["dataverse_site_choice"] = "other"
        if "dataverse_alias" not in st.session_state:
            st.session_state["dataverse_alias"] = dv_alias_default
        if TOKENS_STATE["dataverse"]["state_key"] not in st.session_state:
            st.session_state[TOKENS_STATE["dataverse"]["state_key"]] = dv_token_default

        dv_options = [v for (v, _label) in DATAVERSE_SITE_CHOICES]
        try:
            dv_idx = dv_options.index(st.session_state["dataverse_site_choice"])
        except ValueError:
            dv_idx = 0

        with st.form("dataverse_settings_form", clear_on_submit=False):
            dv_choice = st.selectbox(
                "Site",
                options=dv_options,
                index=dv_idx,
                format_func=lambda v: dict(DATAVERSE_SITE_CHOICES)[v],
                help="Pick demo or production. Choose 'Other…' to enter a custom base URL.",
                key="__dv_site__",
            )

            if dv_choice == "other":
                custom_url = st.text_input(
                    "Custom Dataverse base URL",
                    value=st.session_state["dataverse_base_url"] if st.session_state["dataverse_site_choice"] == "other" else "",
                    placeholder="https://your.dataverse.org",
                    key="__dv_custom_base__",
                )
                dv_base = custom_url.strip()
            else:
                dv_base = dv_choice

            guess_alias_for_ui = ""
            if dv_choice != "other":
                _gb_ui, _ga_ui = guess_dataverse_defaults_from_university(st.session_state.get("data"))
                guess_alias_for_ui = _ga_ui or ""

            if dv_choice != "other":
                if not st.session_state.get("__dv_alias_input__") and not st.session_state.get("dataverse_alias"):
                    if guess_alias_for_ui:
                        st.session_state["__dv_alias_input__"] = guess_alias_for_ui

            dv_alias = st.text_input(
                "Collection (alias)",
                value=st.session_state.get("__dv_alias_input__", st.session_state.get("dataverse_alias", "") or guess_alias_for_ui or ""),
                placeholder=(guess_alias_for_ui or "e.g. your-collection-alias"),
                help="Alias (URL-friendly identifier) of the target Dataverse collection.",
                key="__dv_alias_input__",
            )

            dv_token = st.text_input(
                "API token",
                type="password",
                value=st.session_state[TOKENS_STATE["dataverse"]["state_key"]],
                help="Click Save to write to .env and update session.",
                key="__dv_token__",
            )

            dv_submit = st.form_submit_button("Save settings")
            if dv_submit:
                alias_to_save = st.session_state.get("__dv_alias_input__", "").strip()
                if dv_choice != "other" and alias_to_save == "":
                    _gb, guess_alias = guess_dataverse_defaults_from_university(st.session_state.get("data"))
                    if guess_alias:
                        alias_to_save = guess_alias

                if dv_choice == "other" and not dv_base:
                    st.warning("Please enter a custom Dataverse base URL.")
                else:
                    st.session_state["dataverse_site_choice"] = dv_choice
                    st.session_state["dataverse_base_url"] = dv_base
                    save_to_env(dv_base, "DATAVERSE_BASE_URL")
                    os.environ["DATAVERSE_BASE_URL"] = dv_base

                    st.session_state["dataverse_alias"] = alias_to_save
                    save_to_env(alias_to_save, "DATAVERSE_ALIAS")

                    if dv_token.strip():
                        save_to_env(dv_token.strip(), TOKENS_STATE["dataverse"]["env_key"])
                        os.environ[TOKENS_STATE["dataverse"]["env_key"]] = dv_token.strip()
                        st.session_state[TOKENS_STATE["dataverse"]["state_key"]] = dv_token.strip()

                    eff_base = st.session_state.get("dataverse_base_url", dv_base)
                    eff_token = st.session_state.get(TOKENS_STATE["dataverse"]["state_key"], dv_token.strip())
                    eff_alias = st.session_state.get("dataverse_alias", alias_to_save)
                    ok, msg = test_dataverse_connection(eff_base, eff_token, eff_alias)
                    (st.success if ok else st.error)(msg)
