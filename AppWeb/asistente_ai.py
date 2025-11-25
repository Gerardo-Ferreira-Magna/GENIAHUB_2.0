# --- IMPORTACIONES NECESARIAS ---
import openai
from django.conf import settings

openai.api_key = settings.OPENAI_API_KEY


# ----- Función para probar y validar la API -----
def verificar_api_key():
    if not openai.api_key:
        return "⚠ API KEY VACÍA o no cargada desde .env"

    try:
        openai.models.list()  # Test directo a OpenAI
        return "🟢 API Key válida y funcionando"
    except Exception as e:
        return f"🚫 Error al probar API Key: {e}"


# ---------- Construir prompt contextual ----------
def construir_prompt_contextual(mensaje, proyecto=None, historial=None):
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
        for h in historial[-5:]:
            contexto += f"- {h}\n"

    prompt_final = contexto + f"\n---\nUsuario: {mensaje}\nAsistente:"
    return prompt_final


# ---------- Consultar OpenAI ----------
def consultar_openai(texto, proyecto=None, historial=None):
    try:
        # ⚠ Agregamos VALIDACIÓN PREVIA
        validacion = verificar_api_key()
        print(validacion)  # Esto se verá en consola o logs Django

        if "Error" in validacion or "VACÍA" in validacion:
            return validacion  # No llamar a OpenAI si la KEY está mal

        prompt = construir_prompt_contextual(texto, proyecto, historial)

        respuesta = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # CAMBIAR a gpt-4o si tienes acceso
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )

        return respuesta.choices[0].message.content.strip()

    except Exception as e:
        # Detectamos tipo de error específico
        error_text = str(e)
        if "401" in error_text:
            return "🚫 Error 401: API KEY inválida o bloqueada"
        if "429" in error_text:
            return "⛔ Error 429: Superaste el límite de uso de la API (rate limit)"
        if "billing" in error_text.lower():
            return "💳 Error de facturación: necesitas agregar método de pago"

        return f"⚠ Error con IA: {error_text}"



