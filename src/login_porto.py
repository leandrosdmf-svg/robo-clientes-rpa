from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


def realizar_login(page: Page, cpf: str, senha: str):
    """
    Realiza login no portal da Porto Seguro.
    
    Args:
        page: Objeto da página Playwright
        cpf: CPF do corretor
        senha: Senha do corretor
    """
    print(f"Preenchendo formulário de login para: {cpf}")
    
    # 1. Clica no botão para acessar o corretor online
    page.get_by_role("button", name="ACESSAR O CORRETOR ONLINE").click()
    
    # 2. Preenche o CPF
    page.locator("#logonPrincipal").fill(cpf) 
    
    # 3. Preenche a Senha
    page.locator('input[name="password"]').fill(senha)
    
    # 4. Confirma a primeira tela de login
    page.keyboard.press("Enter")
    
    print("Aguardando a segunda etapa de autenticação (SUSEP)...")

    # --- TRATAMENTO DO POP-UP DE SESSÃO ATIVA ---
    try:
        # Tenta encontrar o botão "Continuar" (sessão ativa)
        btn_continuar = page.get_by_role("button", name="Continuar")
        btn_continuar.wait_for(state="visible", timeout=4000)
        
        print("⚠️ Sessão anterior detectada! Clicando em 'Continuar'...")
        btn_continuar.click(force=True)
        page.wait_for_timeout(3000)
        
    except Exception:
        # Se não encontrar, segue normal para SUSEP
        pass
        
    # 5. Preenche o código SUSEP 
    page.locator("#susepsAutocomplete").fill("CMF00J")
    
    # 6. Clica no botão Avançar do modal SUSEP
    page.locator("#btnAvancarSusep").click()
    
    print("Login concluído! Verificando pop-ups de propaganda...")
    
    # 7. Tratamento de até 2 pop-ups de propaganda em sequência
    for num_popup in range(1, 3):
        try:
            timeout = 15000 if num_popup == 1 else 4000
            page.locator(".news-icon-close").click(timeout=timeout)
            print(f"Pop-up #{num_popup} detectado e fechado!")
            page.wait_for_timeout(1500)
        except PlaywrightTimeoutError:
            if num_popup == 1:
                print("Nenhum pop-up detectado. Seguindo em frente!")
            break
