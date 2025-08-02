from logger.logger import get_logger

logger = get_logger(__name__)

import gradio as gr
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import os

# Importar el workflow del supervisor
from agents.supervisor_agent.graph import workflow
from langgraph.checkpoint.memory import MemorySaver


checkpointer = MemorySaver()
workflow = workflow.compile(checkpointer=checkpointer)

class ChatManager:
    """Maneja las sesiones de chat y el historial."""
    
    def __init__(self, storage_path: str = "data/chat_history"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.current_chat_id: Optional[str] = None
        self.chats: Dict[str, Dict] = {}
        self.load_existing_chats()
    
    def load_existing_chats(self):
        """Carga chats existentes desde el almacenamiento."""
        for chat_file in self.storage_path.glob("*.json"):
            try:
                with open(chat_file, 'r', encoding='utf-8') as f:
                    chat_data = json.load(f)
                    self.chats[chat_data['id']] = chat_data
            except Exception as e:
                print(f"Error loading chat {chat_file}: {e}")
    
    def create_new_chat(self, title: str = None) -> str:
        """Crea un nuevo chat."""
        chat_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        if not title:
            title = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        chat_data = {
            'id': chat_id,
            'title': title,
            'created_at': timestamp,
            'updated_at': timestamp,
            'messages': []
        }
        
        self.chats[chat_id] = chat_data
        self.current_chat_id = chat_id
        self.save_chat(chat_id)
        
        return chat_id
    
    def save_chat(self, chat_id: str):
        """Guarda un chat específico."""
        if chat_id in self.chats:
            chat_file = self.storage_path / f"{chat_id}.json"
            with open(chat_file, 'w', encoding='utf-8') as f:
                json.dump(self.chats[chat_id], f, ensure_ascii=False, indent=2)
    
    def add_message(self, chat_id: str, role: str, content: str):
        """Añade un mensaje al chat."""
        if chat_id in self.chats:
            message = {
                'role': role,
                'content': content,
                'timestamp': datetime.now().isoformat()
            }
            self.chats[chat_id]['messages'].append(message)
            self.chats[chat_id]['updated_at'] = datetime.now().isoformat()
            self.save_chat(chat_id)
    
    def get_chat_history(self, chat_id: str) -> List[Tuple[str, str]]:
        """Obtiene el historial de chat en formato Gradio."""
        if chat_id not in self.chats:
            return []
        
        history = []
        messages = self.chats[chat_id]['messages']
        
        for i in range(0, len(messages), 2):
            user_msg = messages[i]['content'] if i < len(messages) else ""
            bot_msg = messages[i + 1]['content'] if i + 1 < len(messages) else ""
            history.append([user_msg, bot_msg])
        
        return history
    
    def get_chat_list(self) -> List[Tuple[str, str]]:
        """Obtiene la lista de chats para el sidebar."""
        chat_list = []
        for chat_id, chat_data in self.chats.items():
            title = chat_data['title']
            chat_list.append((title, chat_id))
        
        # Ordenar por fecha de actualización (más reciente primero)
        chat_list.sort(key=lambda x: self.chats[x[1]]['updated_at'], reverse=True)
        return chat_list


# Inicializar el manager de chats
logger.info("Inicializando ChatManager...")
chat_manager = ChatManager()


def process_message(message: str, history: List[Tuple[str, str]], chat_id: str) -> Tuple[List[Tuple[str, str]], str]:
    """Procesa un mensaje con el agente supervisor."""
    try:
        # Si no hay chat_id, crear uno nuevo
        if not chat_id:
            chat_id = chat_manager.create_new_chat()
        
        # Añadir mensaje del usuario
        chat_manager.add_message(chat_id, "user", message)
        
        # Procesar con el workflow del supervisor
        response = workflow.invoke(
            {'messages': message},
            config={'thread_id': chat_id}
        )
        
        # Extraer la respuesta del agente
        if 'messages' in response and response['messages']:
            bot_response = response['messages'][-1].content
        else:
            bot_response = "Lo siento, no pude procesar tu mensaje."
        
        # Añadir respuesta del bot
        chat_manager.add_message(chat_id, "assistant", bot_response)
        
        # Actualizar historial
        history.append([message, bot_response])
        
        return history, ""
        
    except Exception as e:
        error_msg = f"Error procesando mensaje: {str(e)}"
        history.append([message, error_msg])
        return history, ""


def load_chat(chat_selection: str) -> Tuple[List[Tuple[str, str]], str]:
    """Carga un chat seleccionado."""
    if not chat_selection:
        return [], ""
    
    # chat_selection viene como "titulo" pero necesitamos el ID
    # Buscar el chat por título
    for chat_id, chat_data in chat_manager.chats.items():
        if chat_data['title'] == chat_selection:
            chat_manager.current_chat_id = chat_id
            history = chat_manager.get_chat_history(chat_id)
            return history, chat_id
    
    return [], ""


def create_new_chat() -> Tuple[List[Tuple[str, str]], str, gr.Dropdown]:
    """Crea un nuevo chat."""
    chat_id = chat_manager.create_new_chat()
    chat_list = chat_manager.get_chat_list()
    
    # Actualizar dropdown
    choices = [title for title, _ in chat_list]
    
    return [], chat_id, gr.Dropdown(choices=choices, value=chat_list[0][0] if chat_list else "")


def get_chat_choices():
    """Obtiene las opciones para el dropdown de chats."""
    chat_list = chat_manager.get_chat_list()
    return [title for title, _ in chat_list]


# Crear la interfaz
def create_interface():
    """Crea la interfaz de Gradio."""
    
    with gr.Blocks(title="Legal Assistant Chat", theme=gr.themes.Soft()) as demo:
        
        # Estado para tracking del chat actual
        current_chat_id = gr.State("")
        
        gr.Markdown("# 🏛️ Legal Assistant Chat")
        gr.Markdown("Interactúa con tu asistente legal especializado")
        
        with gr.Row():
            # Sidebar con lista de chats
            with gr.Column(scale=1, min_width=250):
                gr.Markdown("### 💬 Chats")
                
                new_chat_btn = gr.Button("➕ Nuevo Chat", variant="primary")
                
                chat_dropdown = gr.Dropdown(
                    label="Seleccionar Chat",
                    choices=get_chat_choices(),
                    value=get_chat_choices()[0] if get_chat_choices() else "",
                    interactive=True
                )
            
            # Área principal de chat
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="Conversación",
                    height=500,
                    show_label=False
                )
                
                with gr.Row():
                    msg_input = gr.Textbox(
                        label="",
                        placeholder="Escribe tu pregunta legal aquí...",
                        scale=4,
                        lines=1
                    )
                    send_btn = gr.Button("Enviar", variant="primary", scale=1)
        
        # Información del sistema
        with gr.Accordion("ℹ️ Información del Sistema", open=False):
            gr.Markdown("""
            ### Características:
            - 🤖 **Agente Supervisor**: Coordina múltiples agentes especializados
            - 📚 **RAG**: Búsqueda en documentos legales
            - ✍️ **Escritura**: Generación de documentos legales
            - 💾 **Historial**: Chats guardados automáticamente
            
            ### Instrucciones:
            1. Selecciona un chat existente o crea uno nuevo
            2. Escribe tu consulta legal
            3. El sistema coordinará los agentes necesarios para responder
            """)
        
        # Event handlers
        def submit_message(message, history, chat_id):
            if message.strip():
                return process_message(message, history, chat_id)
            return history, message
        
        # Enviar mensaje
        send_btn.click(
            fn=submit_message,
            inputs=[msg_input, chatbot, current_chat_id],
            outputs=[chatbot, msg_input]
        )
        
        msg_input.submit(
            fn=submit_message,
            inputs=[msg_input, chatbot, current_chat_id],
            outputs=[chatbot, msg_input]
        )
        
        # Crear nuevo chat
        new_chat_btn.click(
            fn=create_new_chat,
            outputs=[chatbot, current_chat_id, chat_dropdown]
        )
        
        # Cargar chat seleccionado
        chat_dropdown.change(
            fn=load_chat,
            inputs=[chat_dropdown],
            outputs=[chatbot, current_chat_id]
        )
        
        # Cargar el primer chat al inicio si existe
        demo.load(
            fn=lambda: (
                chat_manager.get_chat_history(list(chat_manager.chats.keys())[0]) 
                if chat_manager.chats else [],
                list(chat_manager.chats.keys())[0] if chat_manager.chats else ""
            ),
            outputs=[chatbot, current_chat_id]
        )
    
    return demo


def launch_app():
    """Lanza la aplicación."""
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True
    )


if __name__ == "__main__":
    launch_app()