import os
import random
import pandas as pd
from io import StringIO
import re
import threading
from playwright.sync_api import Page
from config.settings import OUTPUT_DIR, OUTPUT_FILE


def _aguardar(page: Page, ms: int, stop_event: threading.Event = None):
    """Espera ms milissegundos em fatias de 200ms, abortando se stop_event for sinalizado."""
    restante = ms
    while restante > 0:
        if stop_event and stop_event.is_set():
            return
        fatia = min(200, restante)
        page.wait_for_timeout(fatia)
        restante -= fatia


def _mover_mouse_aleatoriamente(page: Page):
    """Simula movimentos humanos de mouse para evitar detecção de bot."""
    try:
        size = page.viewport_size or {"width": 1280, "height": 720}
        for _ in range(random.randint(3, 6)):
            x = random.randint(100, size["width"] - 100)
            y = random.randint(100, size["height"] - 100)
            page.mouse.move(x, y)
            page.wait_for_timeout(random.randint(150, 400))
    except Exception:
        pass


def navegar_para_gestao_oportunidades(page: Page, url_portal: str = None, cpf: str = None, senha: str = None):
    """
    Navega até a tela de Gestão de Oportunidades com retry automático.
    
    Args:
        page: Objeto da página Playwright
        url_portal: URL do portal (para refazer login se necessário)
        cpf: CPF do corretor (para refazer login)
        senha: Senha do corretor (para refazer login)
    """
    from src.login_porto import realizar_login

    MAX_TENTATIVAS_NAV = 3

    for tentativa_nav in range(1, MAX_TENTATIVAS_NAV + 1):
        print(f"Iniciando navegação para Gestão de Oportunidades (tentativa {tentativa_nav}/{MAX_TENTATIVAS_NAV})...")
        
        if tentativa_nav > 1 and url_portal:
            print("↩️ Refazendo login para recuperar a sessão...")
            page.goto(url_portal)
            page.wait_for_timeout(random.randint(4000, 6000))
            try:
                realizar_login(page, cpf, senha)
                page.wait_for_timeout(random.randint(3000, 5000))
            except Exception as e:
                print(f"⚠️ Erro ao refazer login: {e}")
        
        try:
            _mover_mouse_aleatoriamente(page)
            page.wait_for_timeout(random.randint(800, 1800))
            page.locator(".menu-toggle-button-container").first.click()
            page.wait_for_timeout(random.randint(1500, 2500))

            menu_desktop = page.locator(".content-menu-desktop")
            menu_desktop.locator("#COL-02VD5").first.click()
            page.wait_for_timeout(random.randint(1000, 2000))
            menu_desktop.locator("#COL-04HB0").first.click()
            page.wait_for_timeout(random.randint(1000, 2000))
            menu_desktop.locator("#COL-04EJ5").first.click()
            print("Página acionada. Aguardando o portal...")
        except Exception as e:
            print(f"⚠️ Erro ao clicar no menu: {e}. Tentando novamente...")
            page.wait_for_timeout(3000)
            continue

        page.wait_for_timeout(5000)
        
        # Detecta e trata erros de Iframe ou Token
        for tentativa_token in range(3):
            erro_iframe = page.get_by_text("Erro ao carregar aplicação Iframe").is_visible()
            erro_token  = page.get_by_text("erro ao setar o Token Authorize").is_visible()
            if erro_iframe or erro_token:
                motivo = "Token Authorize" if erro_token else "Iframe"
                print(f"⚠️ Erro de {motivo} detectado. Recarregando...")
                page.reload()
                page.wait_for_timeout(8000)
            else:
                break

        # Trata pop-ups de diálogo
        try:
            page.wait_for_timeout(10000)
            tamanho_tela = page.viewport_size
            if tamanho_tela:
                meio_x = tamanho_tela['width'] / 2
                meio_y = tamanho_tela['height'] / 2
                page.mouse.click(meio_x, meio_y)
                page.wait_for_timeout(500)
            page.keyboard.press("Escape")
            page.wait_for_timeout(2000)
        except Exception as e:
            print(f"Detalhe no tratamento: {e}")

        print("Aguardando estabilização...")
        page.wait_for_timeout(3000)

        # Procura e clica no ícone de visualização em lista
        icone_clicado = False
        for frame in page.frames:
            try:
                icone_visualizacao = frame.locator("app-leads-management .results img").first
                icone_visualizacao.wait_for(state="visible", timeout=5000)
                icone_visualizacao.click(force=True)
                print("✅ Ícone de visualização clicado!")
                icone_clicado = True
                page.wait_for_timeout(2000)
                break
            except Exception:
                continue

        if icone_clicado:
            return

        print(f"⚠️ Ícone não encontrado na tentativa {tentativa_nav}. Voltando ao topo...")
        try:
            page.keyboard.press("Escape")
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(2000)
        except Exception:
            pass

    print("❌ Não foi possível abrir a tela de Gestão de Oportunidades.")


def extrair_dados_tabela(page, cpf, limite=0, stop_event: threading.Event = None):
    """
    Extrai dados de clientes da tabela com paginação automática.
    
    Args:
        page: Objeto da página Playwright
        cpf: CPF do corretor (para logs)
        limite: Quantidade máxima de clientes (0 = todos)
        stop_event: Evento para interromper
        
    Returns:
        DataFrame com dados extraídos ou None em caso de erro
    """
    print(f"\n[{cpf}] Iniciando a extração com paginação...")
    
    frame_correto = None
    for tentativa in range(4):
        page.wait_for_timeout(4000)
        for frame in page.frames:
            try:
                if frame.locator("table").first.is_visible(timeout=3000):
                    frame_correto = frame
                    break
            except Exception:
                continue
        if frame_correto:
            break
        print(f"⏳ Tabela ainda não carregou (tentativa {tentativa + 1}/4)")
    
    if not frame_correto:
        print("❌ Tabela não encontrada nos frames.")
        return None

    todas_tabelas = []
    pagina_atual = 1
    html_anterior = ""

    while True:
        if stop_event and stop_event.is_set():
            print("🛑 Extração interrompida pelo usuário.")
            break

        print(f"Lendo dados da página {pagina_atual}...")
        tabela_html = frame_correto.locator("table").first.evaluate("el => el.outerHTML")

        if tabela_html == html_anterior:
            print("🏁 Fim das páginas alcançado!")
            break
        html_anterior = tabela_html

        df_temp = pd.read_html(StringIO(tabela_html))[0]
        todas_tabelas.append(df_temp)

        df_consolidado = pd.concat(todas_tabelas, ignore_index=True)
        if limite > 0 and len(df_consolidado) >= limite:
            print(f"🎯 Limite de {limite} clientes atingido!")
            break

        botao_proximo = frame_correto.locator("img.next-page").first
        if botao_proximo.is_visible():
            botao_proximo.click(force=True)
            pagina_atual += 1
            page.wait_for_timeout(3000)
        else:
            print("🏁 Fim das páginas alcançado!")
            break

    df_final = pd.concat(todas_tabelas, ignore_index=True)

    if limite > 0:
        df_final = df_final.head(limite)

    coluna_alvo = df_final.columns[0]

    def extrair_cpf_texto(texto):
        match = re.search(r'\d{3}\.\d{3}\.\d{3}-\d{2}', str(texto))
        return match.group(0) if match else None

    def extrair_nome_texto(texto):
        cpf_encontrado = extrair_cpf_texto(texto)
        texto_str = str(texto)
        if cpf_encontrado:
            nome = texto_str.replace(cpf_encontrado, "").strip()
            nome = re.sub(r'MC$', '', nome).strip()
            return nome
        return texto_str

    df_limpo = pd.DataFrame()
    df_limpo['Nome'] = df_final[coluna_alvo].apply(extrair_nome_texto)
    df_limpo['CPF'] = df_final[coluna_alvo].apply(extrair_cpf_texto)
    df_limpo = df_limpo.dropna(subset=['CPF'])

    print(f"📊 Extração concluída: {len(df_limpo)} clientes para processamento.\n")
    return df_limpo


def _get_frame(page: Page):
    """Re-busca o frame correto para evitar referências obsoletas."""
    for frame in page.frames:
        try:
            if frame.locator("app-leads-management").is_visible(timeout=2000):
                return frame
        except Exception:
            continue
    return None


def processar_cards_clientes(page: Page, df_clientes: pd.DataFrame, cpf_login: str,
                              stop_event: threading.Event = None):
    """
    Processa cada cliente, extrai dados do card e salva em Excel.
    
    Args:
        page: Objeto da página Playwright
        df_clientes: DataFrame com lista de clientes
        cpf_login: CPF do corretor (para identificar aba no Excel)
        stop_event: Evento para interromper
    """
    print(f"\n🔍 Iniciando o processamento de {len(df_clientes)} clientes...")

    if not _get_frame(page):
        print("❌ Iframe de busca não encontrado.")
        return

    dados_extraidos = []

    for index, row in df_clientes.iterrows():
        if stop_event and stop_event.is_set():
            print("🛑 Processamento interrompido pelo usuário.")
            break

        nome_cliente = row['Nome']
        cpf_cliente = row['CPF']

        print(f"\n[{index + 1}/{len(df_clientes)}] Processando: {nome_cliente} | {cpf_cliente}")

        frame_correto = _get_frame(page)
        if not frame_correto:
            print(f"❌ Frame perdido ao processar {nome_cliente}. Pulando...")
            continue

        try:
            frame_correto.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(500)
        except Exception:
            pass

        # Busca pelo CPF
        campo_busca = frame_correto.locator("app-leads-management .filter input").first
        campo_busca.scroll_into_view_if_needed()
        campo_busca.fill("")
        page.wait_for_timeout(300)
        campo_busca.fill(cpf_cliente)
        _aguardar(page, 1000, stop_event)
        if stop_event and stop_event.is_set():
            break

        botao_buscar = frame_correto.locator("app-leads-management").get_by_role("button", name="Buscar").first
        if botao_buscar.is_visible():
            botao_buscar.click(force=True)
        else:
            campo_busca.press("Enter")

        _aguardar(page, 3000, stop_event)
        if stop_event and stop_event.is_set():
            break

        # Verifica se há oportunidades
        msg_sem_oportunidade = frame_correto.get_by_text("Não há oportunidades disponíveis")
        if msg_sem_oportunidade.is_visible(timeout=2000):
            print("⚠️ Sem oportunidades. Pulando...")
            campo_busca.fill("")
            continue

        try:
            seletor_link = "app-leads-management .opportunity-list table tr td:nth-child(1) div div:nth-child(1) a"
            celula_nome = frame_correto.locator(seletor_link).first
            celula_nome.wait_for(state="visible", timeout=8000)

            # Captura data/hora do HUB da tabela
            hubsimulador = "NÃO INFORMADO"
            try:
                hub_elem = frame_correto.locator("app-leads-management .opportunity-list table tr td:nth-child(3) p").first
                if hub_elem.is_visible(timeout=2000):
                    hubsimulador = hub_elem.inner_text().strip() or "NÃO INFORMADO"
            except Exception:
                pass

            celula_nome.click(force=True)
            try:
                frame_correto.locator("#clickbox app-opportunity-info").wait_for(state="visible", timeout=8000)
            except Exception:
                pass
            _aguardar(page, 2000, stop_event)
            if stop_event and stop_event.is_set():
                break
        except Exception as e:
            print(f"❌ Erro ao abrir card de {nome_cliente}. Pulando... Erro: {e}")
            continue

        print("Extraindo informações...")

        def extrair_campo(seletor, eh_input=False):
            try:
                elemento = frame_correto.locator(seletor).first
                if elemento.is_visible(timeout=1000):
                    valor = elemento.input_value() if eh_input else elemento.inner_text()
                    return valor.strip() if valor else "NÃO INFORMADO"
            except Exception:
                pass
            return "NÃO INFORMADO"

        telefone = extrair_campo("#clickbox input[name='phoneNumber']", eh_input=True)
        email    = extrair_campo("#clickbox input[name='email']",       eh_input=True)
        cep      = extrair_campo("#clickbox input[name='contatoCep']",  eh_input=True)
        produto = extrair_campo("#clickbox input[name='produto']", eh_input=True)
        
        if produto == "NÃO INFORMADO":
            produto = extrair_campo("#clickbox .chip p")

        status = extrair_campo("#clickbox app-client-data .nova")
        if status == "NÃO INFORMADO":
            status = extrair_campo("#clickbox app-client-data .opportunity-data .nova")

        modelo = extrair_campo(
            "#clickbox > app-opportunity-info > main > div > div.dashboard-content-cards > container-element > app-client-data > main > div.opportunity-data > div > form > div:nth-child(3) > input[type=text]",
            eh_input=True
        )
        placa = extrair_campo(
            "#clickbox > app-opportunity-info > main > div > div.dashboard-content-cards > container-element > app-client-data > main > div.opportunity-data > div > form > div:nth-child(4) > input[type=text]",
            eh_input=True
        )

        observacao = extrair_campo("#clickbox app-client-data p.text-small")

        linha_cliente = {
            "CPF/CNPJ": cpf_cliente,
            "Nome completo": nome_cliente,
            "Nome Social": "NÃO INFORMADO",
            "Telefone": telefone,
            "E-mail": email,
            "Cep": cep,
            "Produto de interesse": produto,
            "Status": status,
            "Modelo": modelo,
            "Placa": placa,
            "Observação": observacao,
            "Hubsimulador": hubsimulador,
        }

        dados_extraidos.append(linha_cliente)
        print(f"✅ Dados salvos! (Produto: {produto})")

        page.keyboard.press("Escape")
        _aguardar(page, 1000, stop_event)
        campo_busca.fill("")
        _aguardar(page, 500, stop_event)

    # Salvar na planilha master
    if dados_extraidos:
        print("\n💾 Salvando dados no Excel...")
        caminho_pasta = OUTPUT_DIR
        caminho_arquivo = OUTPUT_FILE

        if not os.path.exists(caminho_pasta):
            os.makedirs(caminho_pasta)

        df_novo = pd.DataFrame(dados_extraidos)
        salvo_com_sucesso = False

        while not salvo_com_sucesso:
            try:
                if os.path.exists(caminho_arquivo):
                    with pd.ExcelWriter(caminho_arquivo, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                        try:
                            df_existente = pd.read_excel(caminho_arquivo, sheet_name=cpf_login)
                            df_final_excel = pd.concat([df_existente, df_novo], ignore_index=True)
                        except ValueError:
                            df_final_excel = df_novo
                        df_final_excel.to_excel(writer, sheet_name=cpf_login, index=False)
                else:
                    df_novo.to_excel(caminho_arquivo, sheet_name=cpf_login, index=False)

                print(f"🎉 Excel atualizado: {caminho_arquivo} (Aba: {cpf_login})")
                salvo_com_sucesso = True

            except PermissionError:
                print(f"\n❌ ERRO: Arquivo Excel '{caminho_arquivo}' está ABERTO!")
                input("👉 Feche a planilha e pressione ENTER para tentar novamente...")

            except Exception as e:
                print(f"❌ Erro ao salvar Excel: {e}")
                break
