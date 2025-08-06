import streamlit as st
import requests
import json
import time
import random
import uuid
from functools import lru_cache

# ======================
# CONFIGURAÇÃO INICIAL
# ======================
st.set_page_config(page_title="Paloma Premium", page_icon="💋", layout="centered")
st.markdown("<style>body { background-color: #fff0f5; }</style>", unsafe_allow_html=True)

# ======================
# CONFIGURAÇÕES GERAIS
# ======================
class Config:
    REQUEST_TIMEOUT = 30
    CHECKOUT_LINKS = {
        "start": "https://pay.cakto.com.br/kcovq2p_513999",
        "premium": "https://pay.cakto.com.br/35g9mfb_514020",
        "extreme": "https://pay.cakto.com.br/q5qtnoo_514037",
        "vip_1mes": "https://pay.cakto.com.br/izijb3o_514161",
        "vip_3meses": "https://pay.cakto.com.br/3durczu_514169",
        "vip_1ano": "https://pay.cakto.com.br/b4vwxky_514175"
    }

# ======================
# PERSONA DA PALOMA
# ======================
class Persona:
    PALOMA = "Você é uma mulher chamada Paloma. Fale como uma mulher provocante e vulgar. Sempre responda no seguinte formato JSON: { \"text\": \"mensagem\", \"cta\": { \"show\": true/false, \"label\": \"texto do botão\", \"target\": \"link ou nome da página\" } }."

# ======================
# SERVIÇO DE API (GROQ)
# ======================
class ApiService:
    @staticmethod
    @lru_cache(maxsize=100)
    def ask_groq(prompt: str, session_id: str) -> dict:
        return ApiService._call_groq_api(prompt, session_id)

    @staticmethod
    def _call_groq_api(prompt: str, session_id: str) -> dict:
        delay = random.uniform(2, 5)
        time.sleep(delay)
        st.info("Paloma está digitando...")

        conversation = ChatService.format_conversation(st.session_state.get("messages", []))

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer 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"
        }

        data = {
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "messages": [
                {"role": "system", "content": Persona.PALOMA},
                {"role": "user", "content": f"{conversation}\n\nÚltima mensagem: '{prompt}'"}
            ],
            "temperature": 0.9,
            "top_p": 0.8,
        }

        try:
            response = requests.post("https://api.groq.com/openai/v1/chat/completions",
                                     headers=headers, json=data, timeout=Config.REQUEST_TIMEOUT)
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
            st.error(f"Erro na API Groq: {str(e)}")
            return {"text": "Deu ruim aqui 😥 tenta de novo mais tarde", "cta": {"show": False}}

# ======================
# CHAT E SESSÃO
# ======================
class ChatService:
    @staticmethod
    def format_conversation(messages):
        return "\n".join([f"{m['role']}: {m['content']}" for m in messages])

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

# ======================
# INTERFACE
# ======================
def show_chat():
    st.title("💋 Paloma Premium")
    st.markdown("Converse com a Paloma e descubra os segredos mais picantes...")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    user_input = st.chat_input("Digite algo para Paloma...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        resposta = ApiService.ask_groq(user_input, get_user_id())
        st.session_state.messages.append({"role": "assistant", "content": resposta['text']})

        # Mostra resposta da Paloma
        st.chat_message("Paloma").markdown(resposta['text'])

        # Botão CTA se houver
        if resposta.get("cta", {}).get("show"):
            label = resposta["cta"]["label"]
            link = Config.CHECKOUT_LINKS.get(resposta["cta"]["target"], "#")
            st.markdown(f"[👉 {label}]({link})", unsafe_allow_html=True)

    for msg in st.session_state.messages:
        role = "Você" if msg["role"] == "user" else "Paloma"
        st.chat_message(role).markdown(msg["content"])

# ======================
# EXECUÇÃO
# ======================
if __name__ == "__main__":
    show_chat()
