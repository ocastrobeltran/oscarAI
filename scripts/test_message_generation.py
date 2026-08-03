import sys
import os

# Add root directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.search import is_communication_request, synthesize_agent_response

def main():
    prompt = (
        "para el proyecto de L3835 - Landing Seguridad Vial Autogermana, necesito poner en contexto a Julio, "
        "que este proyecto ya llegó a su tope de horas que estimamos para el proyecto, sin embargo el cliente está "
        "retrasado enviar el contenido, haciendo entregas parciales e integrandolas poco a poco... "
        "1. podriamos desplegar a produccion ocultos, entregarle un manual de administracion... "
        "o 2. Solicitamos un extension de horas en la cotizacion..."
    )

    print("--- TEST 1: Detection of communication request ---")
    detected = is_communication_request(prompt)
    print(f"Prompt: {prompt[:60]}...")
    print(f"Is Communication Request: {detected}")
    assert detected == True, "Failed to detect communication prompt!"

    print("\n--- TEST 2: Synthesis of agent response ---")
    mock_sources = [
        {
            "score": 0.85,
            "knowledge_item": {
                "title": "Base de Conocimiento L3835",
                "content": "Proyecto L3835 Autogermana Landing Seguridad Vial."
            }
        }
    ]
    response = synthesize_agent_response(prompt, "PM Agent", mock_sources)
    print("Generated Answer:")
    print("=" * 60)
    print(response)
    print("=" * 60)

    assert "Asunto:" in response, "Response must include an 'Asunto:' line!"
    assert "Julio" in response, "Response must address Julio!"
    print("\nSUCCESS: All tests passed successfully!")

if __name__ == "__main__":
    main()
