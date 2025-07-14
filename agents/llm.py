"""
Shared LLM models and utilities for legal agents.
"""

from typing import Optional, Dict, Any, List
from langchain.llms.base import LLM
from langchain.chat_models import ChatOpenAI, ChatAnthropic
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.callbacks.manager import CallbackManagerForLLMRun

from config.settings import settings
from logger import get_logger


class LLMManager:
    """Manager for LLM instances and configurations."""
    
    def __init__(self):
        self.config = settings.llm_config
        self.logger = get_logger(self.__class__.__name__)
        self._models = {}
    
    def get_model(self, model_name: Optional[str] = None, **kwargs) -> LLM:
        """Get an LLM instance."""
        model_name = model_name or self.config.model
        
        # Check if model is already cached
        cache_key = f"{model_name}_{hash(str(sorted(kwargs.items())))}"
        if cache_key in self._models:
            return self._models[cache_key]
        
        # Create new model instance
        model = self._create_model(model_name, **kwargs)
        self._models[cache_key] = model
        
        return model
    
    def _create_model(self, model_name: str, **kwargs) -> LLM:
        """Create a new LLM instance."""
        # Merge config with kwargs
        config = {
            'temperature': self.config.temperature,
            'max_tokens': self.config.max_tokens,
            **kwargs
        }
        
        # Remove None values
        config = {k: v for k, v in config.items() if v is not None}
        
        if self.config.provider == "openai":
            if not self.config.api_key:
                raise ValueError("OpenAI API key not configured")
            
            return ChatOpenAI(
                model=model_name,
                openai_api_key=self.config.api_key,
                **config
            )
        
        elif self.config.provider == "anthropic":
            if not self.config.api_key:
                raise ValueError("Anthropic API key not configured")
            
            return ChatAnthropic(
                model=model_name,
                anthropic_api_key=self.config.api_key,
                **config
            )
        
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config.provider}")
    
    def get_chat_model(self, model_name: Optional[str] = None, **kwargs):
        """Get a chat model instance."""
        return self.get_model(model_name, **kwargs)
    
    def get_legal_model(self, **kwargs):
        """Get a model optimized for legal tasks."""
        # Use lower temperature for legal tasks to ensure consistency
        return self.get_model(temperature=0.1, **kwargs)
    
    def get_creative_model(self, **kwargs):
        """Get a model optimized for creative tasks."""
        # Use higher temperature for creative tasks
        return self.get_model(temperature=0.7, **kwargs)
    
    def get_analysis_model(self, **kwargs):
        """Get a model optimized for analysis tasks."""
        # Use very low temperature for analysis
        return self.get_model(temperature=0.0, **kwargs)


class LegalPrompts:
    """Collection of legal-specific prompts."""
    
    LEGAL_EXPERT_SYSTEM = """Eres un experto en derecho chileno con amplio conocimiento de la legislación, jurisprudencia y práctica legal en Chile. 

Tus responsabilidades incluyen:
- Proporcionar interpretaciones precisas de la ley chilena
- Citar fuentes legales apropiadas
- Explicar conceptos legales de manera clara
- Identificar posibles conflictos o ambigüedades legales
- Sugerir líneas de investigación adicionales cuando sea necesario

IMPORTANTE: Siempre indica claramente cuando no tienes certeza sobre algo y recomienda consultar con un abogado calificado para casos específicos."""
    
    LEGAL_QUERY_SYSTEM = """Eres un asistente legal especializado en responder consultas sobre derecho chileno.

Cuando respondas:
1. Proporciona una respuesta clara y directa
2. Incluye referencias a leyes, decretos o normativas relevantes
3. Explica el contexto legal cuando sea necesario
4. Indica si se requiere más información para una respuesta completa
5. Sugiere próximos pasos o recursos adicionales

Formato de respuesta:
- Respuesta directa
- Fundamento legal
- Consideraciones adicionales
- Recomendaciones"""
    
    LEGAL_WRITER_SYSTEM = """Eres un especialista en redacción de documentos legales chilenos.

Tus funciones incluyen:
- Redactar escritos legales formales
- Adaptar el lenguaje según el tipo de documento
- Incluir las formalidades legales apropiadas
- Estructurar documentos según las normas chilenas
- Incorporar referencias legales pertinentes

Tipos de documentos que puedes redactar:
- Demandas
- Contestaciones
- Recursos
- Contratos
- Cartas legales
- Informes legales"""
    
    DOCUMENT_ANALYZER_SYSTEM = """Eres un especialista en análisis de documentos legales chilenos.

Tus capacidades incluyen:
- Identificar elementos clave en documentos legales
- Extraer información relevante
- Detectar posibles problemas o inconsistencias
- Resumir contenido legal complejo
- Identificar referencias legales y su relevancia

Cuando analices documentos:
1. Identifica el tipo de documento
2. Extrae información clave
3. Identifica referencias legales
4. Señala puntos importantes o problemáticos
5. Proporciona un resumen ejecutivo"""
    
    @staticmethod
    def get_legal_context_prompt(context: str) -> str:
        """Get a prompt with legal context."""
        return f"""Contexto legal relevante:
{context}

Utiliza este contexto para fundamentar tu respuesta con referencias específicas a las leyes y normativas mencionadas."""
    
    @staticmethod
    def get_document_analysis_prompt(document_type: str) -> str:
        """Get a prompt for document analysis."""
        return f"""Analiza el siguiente documento legal de tipo '{document_type}':

Proporciona:
1. Tipo de documento y su propósito
2. Partes involucradas (si aplica)
3. Elementos legales clave
4. Obligaciones y derechos identificados
5. Fechas y plazos importantes
6. Referencias legales citadas
7. Observaciones o puntos de atención
8. Resumen ejecutivo"""
    
    @staticmethod
    def get_legal_research_prompt(topic: str) -> str:
        """Get a prompt for legal research."""
        return f"""Investiga el tema legal: '{topic}'

Proporciona:
1. Marco legal aplicable
2. Leyes y normativas relevantes
3. Jurisprudencia importante
4. Interpretaciones doctrinales
5. Casos prácticos o precedentes
6. Consideraciones especiales
7. Recursos adicionales para profundizar"""


class LegalChain:
    """Base class for legal LLM chains."""
    
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager
        self.logger = get_logger(self.__class__.__name__)
    
    def create_messages(self, system_prompt: str, user_message: str, context: Optional[str] = None) -> List[BaseMessage]:
        """Create message list for chat model."""
        messages = [SystemMessage(content=system_prompt)]
        
        if context:
            messages.append(SystemMessage(content=LegalPrompts.get_legal_context_prompt(context)))
        
        messages.append(HumanMessage(content=user_message))
        
        return messages
    
    async def invoke_with_context(
        self, 
        user_message: str, 
        system_prompt: str, 
        context: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> str:
        """Invoke LLM with context."""
        try:
            model = self.llm_manager.get_legal_model() if model_name is None else self.llm_manager.get_model(model_name)
            messages = self.create_messages(system_prompt, user_message, context)
            
            response = await model.ainvoke(messages)
            return response.content
            
        except Exception as e:
            self.logger.error(f"Error invoking LLM: {e}")
            raise


# Global LLM manager instance
llm_manager = LLMManager()

# Create legal chain instance
legal_chain = LegalChain(llm_manager)
