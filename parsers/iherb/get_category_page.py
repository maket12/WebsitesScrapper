from playwright.sync_api import sync_playwright
import time

url = "https://ru.iherb.com/c/supplements?cids=101072"
category = "supplements"

def main():
  with sync_playwright() as p:
    browser = p.chromium.launch(
      headless=False,
      args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(
      user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    page = context.new_page()
    page.goto(url)
    print("Waiting a bit")
    time.sleep(10)

    data = page.content()
    with open(f"data/iherb_{category}.html", "w", encoding="utf-8") as f:
      f.write(data)

    print("done")
    browser.close()


if __name__ == "__main__":
  main()
