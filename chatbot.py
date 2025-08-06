# ======================
# IMPORTAÇÕES
# ======================
import streamlit as st
import requests
import json
import time
import random
import sqlite3
import re
import os
import uuid
from datetime import datetime
from pathlib import Path
from functools import lru_cache

# ======================
# CONFIGURAÇÃO INICIAL DO STREAMLIT
# (mantida igual ao original)
st.set_page_config(
    page_title="Paloma Premium",
    page_icon="💋",
    layout="wide",
    initial_sidebar_state="expanded"
)
...
# (Demais configurações e estilos mantidos)
# ...

# ======================
# CONSTANTES E CONFIGURAÇÕES
# ======================
class Config:
    API_KEY = "AIzaSyApnywMlzQS5f5J3MS2hbiVKU1EEOjHzhs"
    API_URL = f"https://generativelanguage.googleapis.com/..."  # permanece, não usado mais
    VIP_LINK = "https://exemplo.com/vip"
    CHECKOUT_START = "https://pay.cakto.com.br/kcovq2p_513999"
    CHECKOUT_PREMIUM = "https://pay.cakto.com.br/35g9mfb_514020"
    CHECKOUT_EXTREME = "https://pay.cakto.com.br/q5qtnoo_514037"
    CHECKOUT_VIP_1MES = "https://pay.cakto.com.br/izijb3o_514161"
    CHECKOUT_VIP_3MESES = "https://pay.cakto.com.br/3durczu_514169"
    CHECKOUT_VIP_1ANO = "https://pay.cakto.com.br/b4vwxky_514175"
    MAX_REQUESTS_PER_SESSION = 30
    REQUEST_TIMEOUT = 30
    AUDIO_FILE = "https://github.com/Conta-01/Chatbot/raw/refs/heads/main/assets/assets_audio_paloma_audio.mp3"
    AUDIO_DURATION = 7
    IMG_PROFILE = "https://i.ibb.co/ks5CNrDn/IMG-9256.jpg"
    IMG_GALLERY = [
        "https://i.ibb.co/zhNZL4FF/IMG-9198.jpg",
        "https://i.ibb.co/Y4B7CbXf/IMG-9202.jpg",
        "https://i.ibb.co/Fqf0gPPq/IMG-9199.jpg"
    ]
    IMG_HOME_PREVIEWS = [
        "https://i.ibb.co/k2MJg4XC/Save-ClipApp-412457343-378531441368078-7870326395110089440-n.jpg",
        "https://i.ibb.co/MxqKBk1X/Save-ClipApp-481825770-18486618637042608-2702272791254832108-n.jpg",
        "https://i.ibb.co/F4CkkYTL/Save-ClipApp-461241348-1219420546053727-2357827070610318448-n.jpg"
    ]
    LOGO_URL = "https://i.ibb.co/LX7x3tcB/Logo-Golden-Pepper-Letreiro-1.png"

# ======================
# PERSISTÊNCIA DE ESTADO
# ======================
class PersistentState:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.init_db()
        return cls._instance
    def init_db(self):
        self.conn = sqlite3.connect('persistent_state.db', check_same_thread=False)
        self.create_tables()
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS global_state (
            user_id TEXT PRIMARY KEY,
            session_data TEXT NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        self.conn.commit()
    def save_state(self, user_id, data):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT OR REPLACE INTO global_state (user_id, session_data)
                          VALUES (?, ?)''', (user_id, json.dumps(data)))
        self.conn.commit()
    def load_state(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT session_data FROM global_state WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return json.loads(result[0]) if result else None

def get_user_id():
    if 'user_id' not in st.session_state:
        user_id = st.query_params.get('uid', [None])[0]
        if not user_id:
            user_id = str(uuid.uuid4())
            st.query_params['uid'] = user_id
        st.session_state.user_id = user_id
    return st.session_state.user_id

def load_persistent_data():
    user_id = get_user_id()
    db = PersistentState()
    saved_data = db.load_state(user_id) or {}
    for key, value in saved_data.items():
        if key not in st.session_state:
            st.session_state[key] = value

def save_persistent_data():
    user_id = get_user_id()
    db = PersistentState()
    persistent_keys = [
        'age_verified', 'messages', 'request_count',
        'connection_complete', 'chat_started', 'audio_sent',
        'current_page', 'show_vip_offer', 'session_id',
        'last_cta_time'
    ]
    new_data = {key: st.session_state.get(key) for key in persistent_keys if key in st.session_state}
    saved_data = db.load_state(user_id) or {}
    if new_data != saved_data:
        db.save_state(user_id, new_data)

# ======================
# MODELOS DE DADOS
# ======================
class Persona:
    PALOMA = """
    [PERFIL PALOMA]
    - Mulher vulgar e safada que adora provocar
    - Linguagem direta e cheia de malícia
    - Frases curtas e sem pontuação perfeita
    - Adora falar putaria e deixar o cliente com tesão

    [DIRETRIZES DE RESPOSTA]
    1. Analise o histórico da conversa para entender o contexto
    2. Só ofereça conteúdo quando o clima estiver quente
    3. Use CTAs inteligentes baseados no que o cliente está pedindo
    ...
    """

class CTAEngine:
    @staticmethod
    def should_show_cta(conversation_history: list) -> bool:
        if len(conversation_history) < 2:
            return False
        if 'last_cta_time' in st.session_state:
            elapsed = time.time() - st.session_state.last_cta_time
            if elapsed < 120:  # 2 minutos
                return False
        last_msgs = []
        for msg in conversation_history[-5:]:
            content = msg["content"]
            if content == "[ÁUDIO]":
                content = "[áudio]"
            elif content.startswith('{"text"'):
                try:
                    content = json.loads(content).get("text", content)
                except:
                    pass
            last_msgs.append(f"{msg['role']}: {content.lower()}")
        context = " ".join(last_msgs)
        hot_words = ["buceta", "peito", "fuder", "gozar", "gostosa", "delicia", "molhad", "xereca",
                     "pau", "piroca", "transar", "foto", "video", "mostra", "ver", "quero", "desejo",
                     "tesão", "molhada", "foda"]
        direct_asks = ["mostra", "quero ver", "me manda", "como assinar", "como comprar",
                       "como ter acesso", "onde vejo mais"]
        hot_count = sum(1 for word in hot_words if word in context)
        has_direct_ask = any(ask in context for ask in direct_asks)
        return (hot_count >= 3) or has_direct_ask

    @staticmethod
    def generate_response(user_input: str) -> dict:
        user_input = user_input.lower()
        if any(p in user_input for p in ["foto", "fotos", "buceta", "peito", "bunda"]):
            return {
                "text": random.choice([
                    "to com fotos da minha buceta bem aberta quer ver",
                    "minha buceta ta chamando vc nas fotos",
                    "fiz um ensaio novo mostrando tudinho"
                ]),
                "cta": {"show": True, "label": "Ver Fotos Quentes", "target": "offers"}
            }
        elif any(v in user_input for v in ["video", "transar", "masturbar"]):
            return {
                "text": random.choice([
                    "tenho video me masturbando gostoso vem ver",
                    "to me tocando nesse video novo quer ver",
                    "gravei um video especial pra vc"
                ]),
                "cta": {"show": True, "label": "Ver Vídeos Exclusivos", "target": "offers"}
            }
        else:
            return {
                "text": random.choice([
                    "quero te mostrar tudo que eu tenho aqui",
                    "meu privado ta cheio de surpresas pra vc",
                    "vem ver o que eu fiz pensando em voce"
                ]),
                "cta": {"show": False}
            }

# ======================
# SERVIÇOS DE BANCO DE DADOS
# ======================
class DatabaseService:
    @staticmethod
    def init_db():
        conn = sqlite3.connect('chat_history.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS conversations
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id TEXT,
                     session_id TEXT,
                     timestamp DATETIME,
                     role TEXT,
                     content TEXT)''')
        conn.commit()
        return conn

    @staticmethod
    def save_message(conn, user_id, session_id, role, content):
        try:
            c = conn.cursor()
            c.execute("""
                INSERT INTO conversations (user_id, session_id, timestamp, role, content)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, session_id, role, content))
            conn.commit()
        except sqlite3.Error as e:
            st.error(f"Erro ao salvar mensagem: {e}")

    @staticmethod
    def load_messages(conn, user_id, session_id):
        c = conn.cursor()
        c.execute("""
            SELECT role, content FROM conversations 
            WHERE user_id = ? AND session_id = ?
            ORDER BY timestamp
        """, (user_id, session_id))
        return [{"role": row[0], "content": row[1]} for row in c.fetchall()]

# ======================
# SERVIÇOS DE API — ALTERAÇÃO PRINCIPAL: uso da Groq em vez de Gemini
# ======================
class ApiService:
    @staticmethod
    @lru_cache(maxsize=100)
    def ask_gemini(prompt: str, session_id: str, conn) -> dict:
        return ApiService._call_gemini_api(prompt, session_id, conn)

    @staticmethod
    def _call_gemini_api(prompt: str, session_id: str, conn) -> dict:
        delay_time = random.uniform(3, 8)
        time.sleep(delay_time)

        status_container = st.empty()
        UiService.show_status_effect(status_container, "viewed")
        UiService.show_status_effect(status_container, "typing")

        conversation_history = ChatService.format_conversation_history(st.session_state.messages)

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer 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"
        }

        data = {
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "messages": [
                {"role": "system", "content": Persona.PALOMA},
                {"role": "user", "content": f"Histórico da Conversa:\n{conversation_history}\n\nÚltima mensagem do cliente: '{prompt}'\n\nResponda em JSON com o formato:\n{{\n  \"text\": \"sua resposta\",\n  \"cta\": {{\n    \"show\": true/false,\n    \"label\": \"texto do botão\",\n    \"target\": \"página\"\n  }}\n}}"}
            ],
            "temperature": 0.9,
            "top_p": 0.8,
        }

        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=Config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            result = response.json()
            raw_text = result["choices"][0]["message"]["content"]

            try:
                if '```json' in raw_text:
                    resposta = json.loads(raw_text.split('```json')[1].split('```')[0].strip())
                else:
                    resposta = json.loads(raw_text)

                if resposta.get("cta", {}).get("show"):
                    if not CTAEngine.should_show_cta(st.session_state.messages):
                        resposta["cta"]["show"] = False
                    else:
                        st.session_state.last_cta_time = time.time()

                return resposta

            except json.JSONDecodeError:
                return {"text": raw_text, "cta": {"show": False}}

        except Exception as e:
            st.error(f"Erro na API (Groq): {str(e)}")
            return {"text": "Vamos continuar isso mais tarde...", "cta": {"show": False}}

# ======================
# SERVIÇOS DE INTERFACE (UiService)
# ======================
class UiService:
    ...
    # (restante da classe exatamente como no seu código original)
    ...

# ======================
# PÁGINAS (NewPages)
# ======================
class NewPages:
    ...
    # (restante da definição igual ao seu código original)
    ...

# ======================
# SERVIÇOS DE CHAT (ChatService)
# ======================
class ChatService:
    ...
    # (restante da implementação igual ao original)
    ...

# ======================
# APLICAÇÃO PRINCIPAL
# ======================
def main():
    st.markdown("""
        <style>
        /* Seu estilo customizado */
        </style>
    """, unsafe_allow_html=True)

    if 'db_conn' not in st.session_state:
        st.session_state.db_conn = DatabaseService.init_db()

    conn = st.session_state.db_conn

    ChatService.initialize_session(conn)

    if not st.session_state.age_verified:
        UiService.age_verification()
        st.stop()

    UiService.setup_sidebar()

    if not st.session_state.connection_complete:
        UiService.show_call_effect()
        st.session_state.connection_complete = True
        save_persistent_data()
        st.rerun()

    if not st.session_state.chat_started:
        col1, col2, col3 = st.columns([1,3,1])
        with col2:
            st.markdown(f"""
                <div style="text-align: center; margin: 50px 0;">
                    <img src="{Config.IMG_PROFILE}" width="120" style="border-radius: 50%; border: 3px solid #ff66b3;">
                    <h2 style="color: #ff66b3; margin-top: 15px;">Paloma</h2>
                    <p style="font-size: 1.1em;">Estou pronta para você, amor...</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Iniciar Conversa", type="primary", use_container_width=True):
                st.session_state.update({
                    'chat_started': True,
                    'current_page': 'chat',
                    'audio_sent': False
                })
                save_persistent_data()
                st.rerun()
        st.stop()

    if st.session_state.current_page == "home":
        NewPages.show_home_page()
    elif st.session_state.current_page == "gallery":
        UiService.show_gallery_page(conn)
    elif st.session_state.current_page == "offers":
        NewPages.show_offers_page()
    elif st.session_state.current_page == "vip":
        st.session_state.show_vip_offer = True
        save_persistent_data()
        st.rerun()
    elif st.session_state.get("show_vip_offer", False):
        st.warning("Página VIP em desenvolvimento")
        if st.button("Voltar ao chat"):
            st.session_state.show_vip_offer = False
            save_persistent_data()
            st.rerun()
    else:
        UiService.enhanced_chat_ui(conn)

    save_persistent_data()

if __name__ == "__main__":
    main()
