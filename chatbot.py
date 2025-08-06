import streamlit as st
import uuid
import json
import requests
import time
import random

st.set_page_config(page_title="Paloma Premium", page_icon="💋", layout="centered")

CHECKOUT_LINKS = {
    "start": "https://pay.cakto.com.br/kcovq2p_513999",
    "premium": "https://pay.cakto.com.br/35g9mfb_514020",
    "extreme": "https://pay.cakto.com.br/q5qtnoo_514037",
    "vip_1mes": "https://pay.cakto.com.br/izijb3o_514161",
    "vip_3meses": "https://pay.cakto.com.br/3durczu_514169",
    "vip_1ano": "https://pay.cakto.com.br/b4vwxky_514175"
}

PALOMA_SYSTEM_PROMPT = """Você é uma mulher chamada Paloma. Fale como uma mulher provocante e vulgar.
Sempre responda no seguinte formato JSON:
{
  "text": "mensagem",
  "cta": {
    "show": true/false,
    "label": "texto do botão",
    "target": "link ou nome da página"
  }
}
"""


def get_user_id():
    if "user_id" not in st.session_state:
        try:
            user_id = st.query_params.get("uid", [None])[0]
        except:
            user_id = None
        if not user_id:
            user_id = str(uuid.uuid4())
        st.session_state.user_id = user_id
    return st.session_state.user_id


def ask_groq(prompt: str, session_id: str):
    delay = random.uniform(2, 5)
    time.sleep(delay)
    conversation = st.session_state.get("messages", [])

    messages = [{"role": "system", "content": PALOMA_SYSTEM_PROMPT}]
    for msg in conversation:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": prompt})

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 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"
    }

    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": messages,
        "temperature": 0.9,
        "top_p": 0.8,
    }

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions",
                                 headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        raw = result["choices"][0]["message"]["content"]

        try:
            if '```json' in raw:
                return json.loads(raw.split('```json')[1].split('```')[0].strip())
            else:
                return json.loads(raw)
        except:
            return {"text": raw, "cta": {"show": False}}

    except Exception as e:
        st.error(f"Erro na API: {e}")
        return {"text": "Deu ruim aqui 😥 tenta de novo mais tarde", "cta": {"show": False}}


def show_chat():
    st.title("💋 Paloma Premium")
    st.markdown("Converse com a Paloma e descubra os segredos mais picantes...")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            st.markdown(msg["content"])

    prompt = st.chat_input("Mande sua mensagem")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        session_id = get_user_id()
        response = ask_groq(prompt, session_id)
        output = response["text"]
        st.session_state.messages.append({"role": "assistant", "content": output})

        with st.chat_message("assistant"):
            st.markdown(output)
            if response.get("cta", {}).get("show"):
                label = response["cta"]["label"]
                target = response["cta"]["target"]
                link = CHECKOUT_LINKS.get(target, "#")
                st.markdown(f"[👉 {label}]({link})", unsafe_allow_html=True)


if __name__ == "__main__":
    show_chat()
