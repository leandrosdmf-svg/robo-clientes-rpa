import threading
from config.settings import CREDENCIAIS, URL_PORTO
from src.login_porto import realizar_login
from src.extrator import (
    navegar_para_gestao_oportunidades,
    extrair_dados_tabela,
    processar_cards_clientes,
)
from playwright.sync_api import sync_playwright


def iniciar_robo(headless: bool = False, limite: int = 0,
                 stop_event: threading.Event = None,
                 credenciais: list = None):
    """
    Inicia o robô de extração de dados da Porto Seguro.
    
    Args:
        headless: Se True, não mostra o navegador
        limite: Quantidade máxima de clientes a processar (0 = todos)
        stop_event: Evento para interromper execução
        credenciais: Lista de credenciais (usa padrão de settings.py se None)
    """
    print("🤖 Iniciando o robô...")

    if credenciais is None:
        credenciais = CREDENCIAIS

    with sync_playwright() as p:
        launch_args = ["--disable-blink-features=AutomationControlled", "--disable-infobars"]
        if not headless:
            launch_args.append("--start-maximized")
        
        try:
            browser = p.chromium.launch(headless=headless, channel="chrome", args=launch_args)
            print("🌐 Usando Google Chrome instalado.")
        except Exception:
            browser = p.chromium.launch(headless=headless, args=launch_args)
            print("🌐 Usando Chromium padrão.")

        for index, credencial in enumerate(credenciais):
            if stop_event and stop_event.is_set():
                print("🛑 Execução interrompida pelo usuário.")
                break

            cpf = credencial.get("cpf")
            senha = credencial.get("senha")

            if not cpf or not senha:
                print(f"⚠️ Credencial {index + 1} está incompleta no .env. Pulando...")
                continue

            context_kwargs = dict(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            )
            if headless:
                context_kwargs["viewport"] = {"width": 1366, "height": 768}
            else:
                context_kwargs["no_viewport"] = True

            context = browser.new_context(**context_kwargs)
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR','pt','en-US','en']});
                Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
                Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
                window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}, app: {}};
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) =>
                    parameters.name === 'notifications'
                        ? Promise.resolve({state: Notification.permission})
                        : originalQuery(parameters);
            """)
            page = context.new_page()

            print(f"\n--- [Acesso {index + 1}/{len(credenciais)}] CPF: {cpf} ---")

            try:
                page.goto(URL_PORTO)
                realizar_login(page, cpf, senha)
                navegar_para_gestao_oportunidades(page, URL_PORTO, cpf, senha)

                df_clientes = extrair_dados_tabela(page, cpf, limite, stop_event)

                if df_clientes is not None and not df_clientes.empty:
                    processar_cards_clientes(page, df_clientes, cpf, stop_event)

                print(f"✅ O processamento do CPF {cpf} foi concluído com sucesso!")

            except Exception as e:
                print(f"❌ Ocorreu um erro durante o processo do CPF {cpf}: {e}")

            finally:
                context.close()

        print("\n🏁 Processamento de todos os CPFs concluído.")
        browser.close()
