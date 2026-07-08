from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True, args=['--no-sandbox','--disable-dev-shm-usage'])
        page = browser.new_page(viewport={'width': 1400, 'height': 900})
        page.goto('http://localhost:8501', timeout=20000)
        page.wait_for_selector('h3:has-text("Dashboard")')
        page.wait_for_timeout(2000)
        
        print("Initial URL:", page.url)
        
        # Resize to mobile
        page.set_viewport_size({'width': 400, 'height': 800})
        page.wait_for_timeout(3000)
        print("Mobile URL:", page.url)
        
        # Check if the single column layout rendered
        # We can look for the number of st.columns
        content = page.content()
        if 'vw=sm' in page.url:
            print("URL updated to vw=sm")
        else:
            print("URL NOT updated to vw=sm")
            
        page.screenshot(path='/home/keyral/.gemini/antigravity/brain/988d6a04-c322-4ff8-8bb3-aface919cac0/mobile.png')
        browser.close()

if __name__ == '__main__':
    test()
