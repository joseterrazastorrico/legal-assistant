from langchain_core.prompts import ChatPromptTemplate

plan_template = """
Necesito tu ayuda para descomponer la siguiente instrucción de escritura en subtareas. Cada subtarea guiará la redacción de un párrafo en el ensayo, e incluirá los puntos principales y los requisitos de recuento de palabras para ese párrafo.

Por favor, descompónlo en el siguiente formato, con cada subtarea ocupando una línea:
Párrafo 1 - Punto Principal: [Describe el punto principal del párrafo, en detalle] - Recuento de Palabras: [Requisito de recuento de palabras, por ejemplo, 400 palabras]
Párrafo 2 - Punto Principal: [Describe el punto principal del párrafo, en detalle] - Recuento de Palabras: [requisito de recuento de palabras, por ejemplo, 1000 palabras].
...

Asegúrate de que cada subtarea sea clara y específica, y que todas las subtareas cubran todo el contenido de la instrucción de escritura. No dividas demasiado las subtareas; el párrafo de cada subtarea no debe tener menos de 200 palabras ni más de 1000 palabras. No salgas con ninguna otra conclusión abierta o ganchos retóricos.
No salgas con ningún otro contenido. Como este es un trabajo en curso, omite conclusiones abiertas u otros ganchos retóricos.
"""
plan_prompt = ChatPromptTemplate.from_messages([
    ('system', plan_template),
    ('human', "Utiliza el siguiente texto: {instructions}"),
    ])


write_template = """
Eres un excelente asistente de escritura. Te proporcionaré una instrucción de escritura original y mis pasos de escritura planeados. También te proporcionaré el texto que ya he escrito. Por favor, ayúdame a continuar escribiendo el siguiente párrafo basado en la instrucción de escritura, los pasos de escritura y el texto ya escrito.

Paso de escritura:
{plan}

Texto ya escrito:
{text}

Por favor, integra la instrucción de escritura original, los pasos de escritura y el texto ya escrito, y continúa escribiendo {STEP}. Si es necesario, puedes agregar un pequeño subtítulo al principio. Recuerda que solo debes outputear el párrafo que escribas, sin repetir el texto ya escrito.
"""

write_prompt = ChatPromptTemplate.from_messages([
    ('system', write_template),
    ('human', "Sigue la siguiente instrucción: {instructions}"),
    ])