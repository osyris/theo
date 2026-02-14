# ScrapingBee — Web Scraping with JS Rendering

Скилл для скрейпинга веб-страниц через ScrapingBee API. Обходит Cloudflare, рендерит JavaScript.

## API Key

Хранится в `/data/workspace/skills/scrapingbee/.env` (не коммитить в git!):
```
SCRAPINGBEE_API_KEY=your_key_here
```

## Использование

### Простой запрос (curl)
```bash
source /data/workspace/skills/scrapingbee/.env
curl -s "https://app.scrapingbee.com/api/v1?api_key=${SCRAPINGBEE_API_KEY}&url=ENCODED_URL"
```

### С JS рендерингом (для Cloudflare-защищённых сайтов)
```bash
curl -s "https://app.scrapingbee.com/api/v1?api_key=${SCRAPINGBEE_API_KEY}&url=ENCODED_URL&render_js=true"
```

### Python скрипт (рекомендуется)
Используй `/data/workspace/skills/scrapingbee/scrape.py`:
```bash
python3 /data/workspace/skills/scrapingbee/scrape.py "https://www.fragrantica.ru/perfume/Brand/Name-ID.html"
```

## Параметры API

| Параметр | Значение | Описание |
|----------|---------|----------|
| `api_key` | string | API ключ |
| `url` | encoded URL | Целевая страница |
| `render_js` | true/false | Рендерить JavaScript (5 кредитов вместо 1) |
| `premium_proxy` | true/false | Премиум прокси для сложных сайтов (10-75 кредитов) |
| `country_code` | us/de/ru/... | Геолокация прокси |
| `wait` | ms | Ждать N мс после загрузки (для динамического контента) |
| `wait_for` | CSS selector | Ждать появления элемента |
| `extract_rules` | JSON | Правила извлечения данных |

## Лимиты (бесплатный план)

- **1000 кредитов** бесплатно
- Простой запрос = 1 кредит
- JS рендеринг = 5 кредитов  
- Premium proxy = 10-75 кредитов
- **При 1000 кредитах**: ~200 запросов с JS или ~1000 без JS

## Fragrantica-специфичное

Fragrantica защищена Cloudflare → нужен `render_js=true` + `wait=3000` (подождать 3 сек для полной загрузки).

Для парсинга нот, аккордов и рейтингов используй `fragrantica_scraper.py`.

## Файлы скилла

- `SKILL.md` — эта документация
- `.env` — API ключ (в .gitignore!)
- `scrape.py` — универсальный скрейпер
- `fragrantica_scraper.py` — парсер Fragrantica (ноты, аккорды, рейтинги)
