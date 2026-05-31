from pathlib import Path
from playwright.sync_api import sync_playwright

out_dir = Path('tmp/playwright')
out_dir.mkdir(parents=True, exist_ok=True)
results = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for name, size in [('desktop', (1440, 900)), ('mobile', (390, 844))]:
        page = browser.new_page(viewport={'width': size[0], 'height': size[1]}, device_scale_factor=1)
        console_errors = []
        page.on('console', lambda msg: console_errors.append(msg.text) if msg.type == 'error' else None)
        page.goto('http://localhost:3000', wait_until='networkidle')
        page.wait_for_timeout(900)
        screenshot = out_dir / f'home-{name}.png'
        page.screenshot(path=str(screenshot), full_page=True)
        metrics = page.evaluate("""
        () => {
          const canvas = document.querySelector('.layer-graph');
          const title = document.querySelector('.cosmic-title');
          const header = document.querySelector('.app-header');
          const search = document.querySelector('.search-bar');
          const signature = document.querySelector('.deerflow-signature');
          const boxes = [header, title, search, signature].map((el) => {
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return { left: r.left, top: r.top, right: r.right, bottom: r.bottom, width: r.width, height: r.height };
          });
          let nonBlank = 0;
          if (canvas) {
            const ctx = canvas.getContext('2d');
            const w = canvas.width;
            const h = canvas.height;
            const data = ctx.getImageData(0, 0, w, h).data;
            for (let i = 0; i < data.length; i += 16) {
              if (data[i] || data[i + 1] || data[i + 2] || data[i + 3]) nonBlank += 1;
            }
          }
          return {
            titleText: title ? title.textContent : null,
            headerText: header ? header.textContent : null,
            signatureText: signature ? signature.textContent : null,
            canvasNonBlankSample: nonBlank,
            boxes,
            bodyWidth: document.body.scrollWidth,
            viewportWidth: window.innerWidth,
            bodyHeight: document.body.scrollHeight,
            viewportHeight: window.innerHeight
          }
        }
        """)
        results.append({
            'name': name,
            'screenshot': str(screenshot),
            'console_errors': console_errors,
            'metrics': metrics,
        })
        page.close()
    browser.close()

for item in results:
    print(item)
