#!/usr/bin/env python3
"""
Konfiguracja AI dla KislistScraper
Zawiera ustawienia dla różnych providerów AI
"""

import os

# Domyślne ustawienia AI
AI_CONFIG = {
    'default_provider': 'ollama',  # ollama lub openai
    'ollama': {
        'model': 'llama3.2:latest',
        'base_url': 'http://localhost:11434',
        'temperature': 0.7,
    },
    'openai': {
        'model': 'gpt-4o-mini',
        'temperature': 0.7,
        'max_tokens': 2000,
    }
}

def get_ai_config():
    """
    Pobiera konfigurację AI z zmiennych środowiskowych lub używa domyślnych wartości
    """
    provider = os.getenv('KISLIST_AI_PROVIDER', AI_CONFIG['default_provider'])

    if provider == 'openai':
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("[BŁĄD] OPENAI_API_KEY nie jest ustawiony w zmiennych środowiskowych!")

        return {
            'provider': 'openai',
            'model': os.getenv('KISLIST_AI_MODEL', AI_CONFIG['openai']['model']),
            'api_key': api_key,
            'temperature': AI_CONFIG['openai']['temperature'],
            'max_tokens': AI_CONFIG['openai']['max_tokens'],
        }

    elif provider == 'ollama':
        return {
            'provider': 'ollama',
            'model': os.getenv('KISLIST_AI_MODEL', AI_CONFIG['ollama']['model']),
            'base_url': os.getenv('OLLAMA_BASE_URL', AI_CONFIG['ollama']['base_url']),
            'temperature': AI_CONFIG['ollama']['temperature'],
        }

    else:
        raise ValueError(f"[BŁĄD] Nieobsługiwany provider AI: {provider}")

def check_ai_availability():
    """
    Sprawdza czy AI jest dostępne i skonfigurowane
    """
    try:
        config = get_ai_config()

        if config['provider'] == 'openai':
            if not config.get('api_key'):
                return False, "Brak klucza API dla OpenAI"
            return True, f"OpenAI ({config['model']}) gotowy do użycia"

        elif config['provider'] == 'ollama':
            import requests
            try:
                response = requests.get(f"{config['base_url']}/api/tags", timeout=5)
                if response.status_code == 200:
                    return True, f"Ollama ({config['model']}) gotowy do użycia"
                else:
                    return False, f"Ollama nie odpowiada (status {response.status_code})"
            except requests.exceptions.RequestException as e:
                return False, f"Nie można połączyć z Ollama: {e}"

        return False, "Nieznany provider AI"

    except Exception as e:
        return False, f"Błąd konfiguracji AI: {e}"

def setup_ai_environment():
    """
    Interaktywne ustawienie środowiska AI
    """
    print("[INFO] Konfiguracja AI dla KislistScraper")
    print("=" * 40)

    print("\n1. Wybierz provider AI:")
    print("   1) Ollama (lokalny, darmowy)")
    print("   2) OpenAI (płatny, wymaga API key)")

    while True:
        choice = input("\nWybór (1 lub 2): ").strip()
        if choice == "1":
            provider = "ollama"
            break
        elif choice == "2":
            provider = "openai"
            break
        else:
            print("[OSTRZEŻENIE] Nieprawidłowy wybór!")

    if provider == "ollama":
        print("\n[INFO] Konfiguracja Ollama:")
        model = input(f"Model (domyślnie {AI_CONFIG['ollama']['model']}): ").strip()
        if not model:
            model = AI_CONFIG['ollama']['model']

        base_url = input(f"Base URL (domyślnie {AI_CONFIG['ollama']['base_url']}): ").strip()
        if not base_url:
            base_url = AI_CONFIG['ollama']['base_url']

        print(f"\n[INFO] Ustawianie zmiennych środowiskowych:")
        print(f"export KISLIST_AI_PROVIDER=ollama")
        print(f"export KISLIST_AI_MODEL={model}")
        print(f"export OLLAMA_BASE_URL={base_url}")

    elif provider == "openai":
        print("\n[INFO] Konfiguracja OpenAI:")
        model = input(f"Model (domyślnie {AI_CONFIG['openai']['model']}): ").strip()
        if not model:
            model = AI_CONFIG['openai']['model']

        api_key = input("API Key: ").strip()
        if not api_key:
            print("[BŁĄD] API Key jest wymagany dla OpenAI!")
            return

        print(f"\n[INFO] Ustawianie zmiennych środowiskowych:")
        print(f"export KISLIST_AI_PROVIDER=openai")
        print(f"export KISLIST_AI_MODEL={model}")
        print(f"export OPENAI_API_KEY={api_key}")

    print("\n[OK] Konfiguracja gotowa!")
    print("   Uruchom ponownie terminal aby zastosować zmiany.")

if __name__ == "__main__":
    try:
        config = get_ai_config()
        print(f"[OK] Konfiguracja AI: {config}")

        available, message = check_ai_availability()
        print(f"[INFO] Dostępność AI: {'[OK]' if available else '[BŁĄD]'} {message}")

    except Exception as e:
        print(f"[BŁĄD] {e}")
        print("\nUruchom setup_ai_environment() aby skonfigurować AI")
        setup_ai_environment()
