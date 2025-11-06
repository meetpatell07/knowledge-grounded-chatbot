# graph_logic.py
from langgraph.graph import StateGraph, END, START
from typing import TypedDict, Optional
from app.retrieve import retrieve
from app.db import get_conn
import google.generativeai as genai
import os
import requests

PRISMA_API_URL = "http://localhost:4000"

# Load your Gemini API key from env
GOOGLE_GEN_AI_API_KEY = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not GOOGLE_GEN_AI_API_KEY:
    raise ValueError("Missing GOOGLE_GENERATIVE_AI_API_KEY or GOOGLE_API_KEY in environment variables.")

# Configure the Gemini client
genai.configure(api_key=GOOGLE_GEN_AI_API_KEY)

# Use Gemini Flash for speed (you can also use gemini-1.5-pro for more reasoning)
MODEL = genai.GenerativeModel("gemini-2.5-flash")

# --- Define chat state ---
class ChatState(TypedDict):
    session_id: str
    query: str
    context: str
    best_distance: Optional[float]  # Fixed: can be None
    reply: str
    source: str


# --- Save chat messages in DB ---
# def save_message(session_id, role, content, source=None):
#     conn = get_conn()
#     try:
#         with conn.cursor() as cur:
#             cur.execute(
#                 "INSERT INTO messages (session_id, role, content, source) VALUES (%s,%s,%s,%s)",
#                 (session_id, role, content, source),
#             )
#         conn.commit()
#     except Exception as e:
#         conn.rollback()
#         raise e
#     finally:
#         conn.close()

# Instead of using psycopg2, we use the Prisma API to save the message
def save_message(session_id, role, content, source=None):
    """Save message using Prisma API, ensuring session exists"""
    try:
        data = {
            "sessionId": session_id,  # Note: Prisma uses camelCase
            "role": role,
            "content": content,
            "source": source
        }
        resp = requests.post(f"{PRISMA_API_URL}/messages", json=data, timeout=5)
        if resp.status_code != 200:
            error_text = resp.text
            print(f"⚠️ Failed to save message (status {resp.status_code}): {error_text}")
            # Try to log more details
            try:
                error_json = resp.json()
                print(f"   Error details: {error_json}")
            except:
                pass
        else:
            print(f"✓ Saved {role} message for session {session_id[:8]}...")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Network error saving message: {str(e)}")
    except Exception as e:
        print(f"⚠️ Unexpected error saving message: {str(e)}")


# --- Graph nodes ---
def retrieve_node(state: ChatState):
    docs = retrieve(state["query"], top_k=3)
    context = "\n\n---\n\n".join(
        [f"Title: {d['title']}\n{d['content']}" for d in docs]
    )
    state["context"] = context
    state["best_distance"] = min([d["distance"] for d in docs]) if docs else None
    return state


def evaluate_node(state: ChatState) -> str:
    """Routing function - returns string, not dict!"""
    # Decide if we trust the KB or need LLM help
    if state["best_distance"] is not None and state["best_distance"] < 0.35:
        return "kb_only"
    else:
        return "llm_augmented"


def kb_only_node(state: ChatState):
    if not state["context"]:
        reply = "I couldn't find an answer in internal docs."
    else:
        reply = "Based on internal docs:\n\n" + state["context"]
    state["reply"] = reply
    state["source"] = "KB"
    save_message(state["session_id"], "assistant", reply, source=state["source"])
    return state


def llm_augmented_node(state: ChatState):
    # Build a clear context + question prompt
    prompt = f"""You are an assistant. Use the CONTEXT below to answer the QUESTION.
If the context doesn't contain the answer, say "I don't know based on internal docs." and then add a short general suggestion.

CONTEXT:
{state['context']}

QUESTION:
{state['query']}
"""

    try:
        response = MODEL.generate_content(prompt)
        # Handle response safely
        if hasattr(response, 'text') and response.text:
            answer = response.text.strip()
        elif hasattr(response, 'candidates') and response.candidates:
            answer = response.candidates[0].content.parts[0].text.strip()
        else:
            answer = "⚠️ Gemini API returned an unexpected response format."
    except Exception as e:
        answer = f"⚠️ Gemini API error: {str(e)}"

    # Label the response source
    state["reply"] = answer
    state["source"] = "KB+LLM" if state["context"] else "LLM"
    save_message(state["session_id"], "assistant", answer, source=state["source"])
    return state


# --- Build the StateGraph ---
graph = StateGraph(ChatState)
graph.add_node("retrieve", retrieve_node)
# NOTE: evaluate_node is NOT a node - it's only a routing function
#graph.add_node("evaluate", evaluate_node)
graph.add_node("kb_only", kb_only_node)
graph.add_node("llm_augmented", llm_augmented_node)

#graph.add_edge(START, "retrieve")
#graph.add_edge("retrieve", "evaluate")
graph.add_edge(START, "retrieve")
graph.add_conditional_edges(
    "retrieve", 
    evaluate_node, 
    {"kb_only": "kb_only", "llm_augmented": "llm_augmented"}
)
graph.add_edge("kb_only", END)
graph.add_edge("llm_augmented", END)

chatbot_graph = graph.compile()


# --- Chat handler ---
def handle_chat(session_id: str, message: str):
    save_message(session_id, "user", message)
    initial_state = {
        "session_id": session_id,
        "query": message,
        "context": "",
        "best_distance": None,
        "reply": "",
        "source": "",
    }
    result = chatbot_graph.invoke(initial_state)
    return {"reply": result["reply"], "source": result["source"]}
