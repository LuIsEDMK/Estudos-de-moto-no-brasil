import re
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8000"

def test_home_page_and_theme_toggle(page: Page):
    page.goto(BASE_URL)
    expect(page).to_have_title(re.compile("MotoExpert AI"))

    # Locate theme toggle button
    theme_btn = page.locator("#theme-toggle")
    expect(theme_btn).to_be_visible()
    
    # Check if html has 'dark' class initially
    html = page.locator("html")
    initial_class = html.get_attribute("class") or ""
    is_dark_initially = "dark" in initial_class.split()
    
    # Toggle theme
    theme_btn.click()
    page.wait_for_timeout(300) 
    
    new_class = html.get_attribute("class") or ""
    is_dark_now = "dark" in new_class.split()
    
    assert is_dark_initially != is_dark_now, "Theme did not toggle on click"

def test_search_journey_and_free_limit(page: Page):
    page.goto(BASE_URL)
    
    # Select Marca "HONDA"
    marca_select = page.locator("select[x-model='marcaSelecionada']")
    marca_select.select_option("HONDA")
    
    # Wait for Modelos to load (since it fetches from API)
    modelo_select = page.locator("select[x-model='modeloSelecionado']")
    # In Playwright, selecting options will wait until the option is available
    modelo_select.select_option("BIZ 110I")
    
    # Click Analyze
    page.get_by_role("button", name="Analisar Moto").click()
    
    # Wait for result card to appear
    result_heading = page.locator("h2:has-text('Análise de Risco: HONDA BIZ 110I')")
    expect(result_heading).to_be_visible(timeout=5000)
    
    # Check if price constraints are locked
    expect(page.get_by_text("🔒 R$ *** (VIP)")).to_be_visible()

def test_vip_login(page: Page):
    page.goto(BASE_URL)
    
    # Try invalid password
    password_input = page.locator("input[placeholder='Senha VIP']")
    password_input.fill("WRONG_PASSWORD")
    page.get_by_role("button", name="Entrar").click()
    
    # For alert dialogs, we need a handler but alpine uses alert()
    # Playwright auto-dismisses dialogs but we can listen for them
    
    # Let's try correct password "MOTO990_MASTER"
    page.on("dialog", lambda dialog: dialog.accept()) # Auto accept alerts
    
    password_input.fill("MOTO990_MASTER")
    page.get_by_role("button", name="Entrar").click()
    
    # Wait to see VIP status indicator
    expect(page.get_by_text("👑 Usuário VIP")).to_be_visible(timeout=5000)
    
    # The VIP tabs should unlock now!
    page.get_by_role("button", name="Relatórios VIP").click()
    
    # Check if we see the unlocked VIP reports page
    expect(page.get_by_text("Bem-vindo à Área VIP!")).to_be_visible()
