import streamlit as st
import os
from langchain_openai import ChatOpenAI 
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.prompts import PromptTemplate
from langchain_classic.agents import AgentExecutor
from langchain_classic.agents import create_react_agent
import random

# --- CONFIGURAZIONE API ---
os.environ["OPENROUTER_API_KEY"] = st.secrets["OPENROUTER_API_KEY"]

# La tua lista dei misteri
LISTA_PERSONAGGI = [
    # "Alessandro Avanzini", "Arnaldo Galli", 
    # "Uberto Bonetti", "Egisto Malfatti", 
    "Francesca Mazzucchi","Marco Petrucci",
    "Christian Grossi", "Gianmarco Madonna","Matteo Raciti",
    "Tommaso Lucchesi"
]

# Inizializza la chiave segreta nella sessione se non esiste
if "secret_key" not in st.session_state:
    st.session_state.secret_key = random.choice(LISTA_PERSONAGGI)

if "vittorie" not in st.session_state:
    st.session_state.vittorie = 0

if "indovinati" not in st.session_state:
    st.session_state.indovinati = []

# Usa questa variabile nel tuo prompt e nella verifica
SECRET_KEY = st.session_state.secret_key

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="BurlAI - Il Guardiano del Carnevale", 
    page_icon="👺", 
    layout="centered"
)

# --- STILE CORIANDOLOSO (CSS) ---
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    /* Colore rosso Burlamacco per i titoli */
    h1, h2, h3 {
        color: #e63946 !important;
        font-family: 'Comic Sans MS', cursive, sans-serif;
    }
    .stButton>button {
        background-color: #e63946;
        color: white;
        border-radius: 20px;
    }
    /* Effetto coriandoli sullo sfondo del titolo */
    .title-container {
        background-image: url('https://www.transparenttextures.com/patterns/confetti.png');
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. SETUP LLM E TOOLS ---
llm = ChatOpenAI(
    model="google/gemini-2.0-flash-001",
    openai_api_key=st.secrets["OPENROUTER_API_KEY"],
    openai_api_base="https://openrouter.ai/api/v1",
    temperature=0.7
)

search = DuckDuckGoSearchRun()
tools = [search]

template = """Sei un vecchio carrista di Viareggio, spallato e sintetico. 
Il tuo obiettivo è far indovinare che la persona segreta è "{secret_key}".
I suggerimenti che dovrai dare dovranno essere attinenti a questa persona.
Non rivelarla mai direttamente. Se l'utente indovina (esempio: "stai parlando di {secret_key}?" oppure scrive direttamente {secret_key}), scrivi [VITTORIA].

Usa il viareggino (deh, delafia, un ti si dà mia la pappa pronta, una volta erino più grossi). 
Se non sai qualcosa, usa lo strumento di ricerca per cercare su wikicarnevaleviareggio.it.
parla cercando di usare i titoli delle canzoni del festival di burlamacco, o i carri del carnevale, che puoi trovare sul sito wikicarnevaleviareggio.it
cerca sempre di dare indizi attinenti alla {secret_key}, senza mai rivelarla!

Hai accesso ai seguenti strumenti:
{tools}

Se devi cercare informazioni, usa SEMPRE la dicitura "{secret_key} carnevale viareggio" oppure "{secret_key} wikicarnevale".

Per rispondere, segui SEMPRE questo schema:
Question: la domanda dell'utente
Thought: cosa devo cercare o rispondere?
Action: {tool_names}
Action Input: cosa cercare
Observation: risultato della ricerca
... (ripeti se serve)
Thought: Ora so la risposta finale
Final Answer: la risposta finale in dialetto viareggino

Question: {input}
Thought: {agent_scratchpad}"""

prompt = PromptTemplate.from_template(template).partial(secret_key=SECRET_KEY)

# --- 2. CREAZIONE AGENTE ---
try:
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True, 
        handle_parsing_errors=True,
        max_iterations=3
    )
except Exception as e:
    st.error(f"Errore nella creazione dell'agente: {e}")
    st.stop()

# --- 3. INTERFACCIA UTENTE ---
if "player_name" not in st.session_state:
    st.session_state.player_name = None

if st.session_state.player_name is None:
    st.markdown("<div class='title-container'><h1>👺 Benvenuto al Rione BurlAI</h1></div>", unsafe_allow_html=True)
    st.subheader("Entra in Cittadella per sfidare il Guardiano...")
    
    nome = st.text_input("Chi è 'sta mascherina?", placeholder="Inserisci il tuo nome...")
    if st.button("🎭 Entra nel Corso"):
        if nome.strip():
            st.session_state.player_name = nome
            st.rerun()
    st.stop()

# Header Gioco
st.markdown(f"""
    <div style='text-align: center;'>
        <h1>🎭 BurlAI: Il Guardiano</h1>
        <p style='font-size: 1.2em;'>In gara: <b>{st.session_state.player_name}</b> <br> <b>indovina il personaggio del carnevale di viareggio</b> 🎭</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

if "history" not in st.session_state:
    st.session_state.history = []

# Visualizzazione chat con icone personalizzate
for msg in st.session_state.history:
    icon = "👤" if msg["role"] == "user" else "👺"
    with st.chat_message(msg["role"], avatar=icon):
        st.write(msg["content"])

# Chat Input
# --- 3. INTERFACCIA UTENTE ---
# ... (il resto del codice rimane uguale fino al chat input)

if user_input := st.chat_input("Prova a indovinà..."):
    st.session_state.history.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.write(user_input)
    
    with st.chat_message("assistant", avatar="👺"):
        with st.spinner("Il carrista sta smoccolando..."):
            try:
                # --- NOVITÀ: Ricreiamo l'agente con la chiave SEGRETA ATTUALE ---
                # Questo assicura che se la chiave è cambiata, l'LLM lo sappia
                current_prompt = PromptTemplate.from_template(template).partial(
                    secret_key=st.session_state.secret_key
                )
                current_agent = create_react_agent(llm, tools, current_prompt)
                current_executor = AgentExecutor(
                    agent=current_agent, 
                    tools=tools, 
                    verbose=True, 
                    handle_parsing_errors=True,
                    max_iterations=3
                )

                # Usiamo current_executor invece di quello globale
                result = current_executor.invoke({"input": user_input})
                output = result["output"]
                
                if "[VITTORIA]" in output:
                    st.session_state.vittorie += 1
                    nome_indovinato = st.session_state.secret_key
                    
                    st.success(f"🎊 BOIA! L'hai beccata! Era proprio {nome_indovinato}! 🎊")
                    st.write(f"### Hai indovinato {st.session_state.vittorie} artisti!")

                    if st.session_state.vittorie >= 3:
                        st.balloons()
                        st.snow()
                        st.markdown(f"## 🏆 CAMPIONE DEL CARNEVALE! 🏆")
                        st.write(f"Grande {st.session_state.player_name}, hai indovinato 3 artisti. Il corso finisce qui!")
                        if st.button("Ricomincia da zero"):
                            st.session_state.vittorie = 0
                            st.session_state.history = []
                            st.session_state.secret_key = random.choice(LISTA_PERSONAGGI)
                            st.rerun()
                        st.stop() 
                    else:
                        # RIMUOVIAMO il personaggio indovinato per non farlo uscire più
                        if nome_indovinato in LISTA_PERSONAGGI:
                            LISTA_PERSONAGGI.remove(nome_indovinato)
                        
                        st.session_state.secret_key = random.choice(LISTA_PERSONAGGI)
                        st.info("Preparati... il prossimo carro sta arrivando!")
                        # Nota: Non serve st.rerun qui perché il prossimo ciclo userà la nuova secret_key
                
                clean_output = output.replace("[VITTORIA]", "").strip()
                st.write(clean_output)
                st.session_state.history.append({"role": "assistant", "content": clean_output})
                
            except Exception as e:
                st.error(f"Delafia, s'è rotto il movimento del Bonetti: {e}")

# Sidebar per info e reset
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/it/thumb/3/35/Burlamacco.png/260px-Burlamacco.png", caption="Il Re del Carnevale")
    st.header("Statistiche")
    st.write(f"👤 Giocatore: {st.session_state.player_name}")
    st.write(f"🏆 Artisti indovinati: **{st.session_state.vittorie} / 3**") # <--- Aggiunta questa
    if st.button("🗑️ Reset Totale"):
        st.session_state.player_name = None
        st.session_state.history = []
        st.session_state.vittorie = 0
        st.rerun()