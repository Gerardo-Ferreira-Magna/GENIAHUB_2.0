# --- IMPORTACIONES NECESARIAS ---
import openai
from django.conf import settings

openai.api_key = settings.OPENAI_API_KEY


# ---------- Construir prompt contextual ----------
def construir_prompt_contextual(mensaje, proyecto=None, historial=None):
    """
    Construye un prompt más inteligente usando datos del proyecto
    y el historial de preguntas del usuario.
    """

    contexto = "Eres un asistente experto en proyectos académicos y empresariales.\n"

    if proyecto:
        contexto += f"""
        📌 PROYECTO:
        - Título: {proyecto.titulo}
        - Resumen: {proyecto.resumen}
        - Palabras Clave: {proyecto.palabras_clave}
        """

    if historial:
        contexto += "\n🔁 Historial de conversación:\n"
        for h in historial[-5:]:   # lee solo los últimos 5 mensajes
            contexto += f"- {h}\n"

    prompt_final = contexto + f"\n---\nUsuario: {mensaje}\nAsistente:"
    return prompt_final


# ---------- Consultar OpenAI ----------
def consultar_openai(texto, proyecto=None, historial=None):
    try:
        prompt = construir_prompt_contextual(texto, proyecto, historial)

        respuesta = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # CAMBIA a gpt-4o si tienes acceso
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )

        return respuesta.choices[0].message.content.strip()

    except Exception as e:
        return f"⚠ Error con IA: {str(e)}"


