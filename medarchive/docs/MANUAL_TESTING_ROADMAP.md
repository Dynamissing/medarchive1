# Manual Testing Roadmap

## 1. Purpose

Этот документ - ручная QA-дорожная карта и чеклист demo-readiness для MedPrice. В репозитории также встречаются названия MedArchive / MedPartners; в этом документе они считаются частями одного hackathon-проекта: backend отвечает за импорт, парсинг, нормализацию, matching и API, frontend - за публичный поиск и демонстрационные admin-экраны.

Цель проверки - убедиться, что перед демо команда может:

- поднять проект с чистого состояния;
- импортировать или сгенерировать тестовые данные;
- проверить backend API, базу данных и worker-процессинг;
- пройти публичный пользовательский сценарий поиска цен;
- пройти admin-сценарий импорта, статусов, качества и проверки;
- честно понимать, какие P0-части уже работают на live backend API, а какие остаются P1/P2 и показывают пустое состояние без fake data.

### Актуальный статус frontend-backend wiring

После P0-подключения следующие страницы используют реальные backend endpoints через `NEXT_PUBLIC_API_BASE_URL`:

| Страница | Endpoint | Статус |
|---|---|---|
| `/ru/search`, `/kz/search`, `/en/search` | `GET /search` | подключено для непустого `q`; `city` сохраняется в URL, но backend-фильтр города пока отсутствует |
| `/login` | `POST /admin/login` | подключено, bearer token сохраняется в `localStorage` |
| `/dashboard` | `GET /admin/dashboard` | подключено, требует bearer token |
| `/documents` | `GET /admin/documents` | подключено, требует bearer token |
| `/imports` | `POST /admin/import/archive`, `GET /admin/import-batches` | подключено, ZIP отправляется multipart-полем `file`, fake success не используется |
| `/quality` | `GET /admin/reports/quality` | подключено, требует bearer token |
| `/unmatched` | `GET /unmatched` | подключено, требует bearer token |
| `/verification` | `GET /admin/verification` | подключено, показывает реальные action/anomaly поля |

Остаются P1/P2: публичные каталоги `/services`, `/partners`, service/clinic detail страницы на реальных id/slug, preview/reprocess/match/verify/reject действия. Эти места не должны показывать вымышленные данные.

## 2. Project startup checklist

### 2.1. Открытие проекта

```bash
cd medarchive
```

Если проект только что получен из Git:

```bash
git clone <repo-url>
cd medarchive
```

### 2.2. Подготовка окружения

```bash
cp .env.example .env
```

Проверить в `.env`:

- `DATABASE_URL`;
- `REDIS_URL`;
- `ADMIN_USERNAME`;
- `ADMIN_PASSWORD`;
- `ADMIN_TOKEN_SECRET`;
- `NEXT_PUBLIC_SITE_URL`.

Для локального демо значения по умолчанию из `.env.example` подходят, но пароль `admin/admin` нельзя использовать для общего стенда.

### 2.3. Запуск Docker-сервисов

Основной путь:

```bash
make up
make migrate
```

Прямые команды без Make:

```bash
docker compose up -d --build
docker compose run --rm backend alembic upgrade head
```

Ожидаемые локальные адреса:

| Сервис | URL |
|---|---|
| Frontend | `http://localhost:3000` |
| Backend | `http://localhost:8000` |
| Swagger/OpenAPI | `http://localhost:8000/docs` |
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |

### 2.4. Проверка backend health

```bash
curl http://localhost:8000/health
```

Ожидаемый результат: HTTP 200 и JSON со статусом `ok`.

### 2.5. Генерация и импорт synthetic demo data

Сгенерировать маленький синтетический набор данных:

```bash
python scripts/seed_demo_data.py
```

Импорт справочника услуг:

```bash
make import-services FILE=/app/data/samples/services.json
```

Импорт ZIP-архива:

```bash
make import-archive FILE=/app/data/samples/archive.zip
```

Важно: путь `FILE` используется внутри backend-контейнера. Файл `data/samples/archive.zip` на host-машине соответствует `/app/data/samples/archive.zip` внутри контейнера.

### 2.6. Запуск backend без Docker, если нужно

Использовать только если зависимости установлены локально:

```bash
cd backend
python -m uvicorn app.main:app --reload
```

Предпочтительный demo-путь - Docker Compose, потому что он поднимает Postgres, Redis, backend, worker и frontend вместе.

### 2.7. Запуск frontend отдельно, если нужно

```bash
cd frontend
npm install
npm run dev
```

Для production-like проверки frontend в проекте используется static export и Nginx-контейнер через Docker Compose.

## 3. Test accounts and credentials

Admin-доступ backend API использует переменные окружения:

| Переменная | Назначение | Значение по умолчанию в `.env.example` |
|---|---|---|
| `ADMIN_USERNAME` | логин администратора | `admin` |
| `ADMIN_PASSWORD` | пароль администратора | `admin` |
| `ADMIN_TOKEN_SECRET` | секрет подписи bearer-токена | `change-me-for-demo` |
| `ADMIN_TOKEN_TTL_SECONDS` | срок действия токена | `3600` |

Frontend `/login` отправляет учетные данные в backend `POST /admin/login` через `NEXT_PUBLIC_API_BASE_URL` и сохраняет bearer token в `localStorage`. Для тестирования защищенных backend admin endpoints можно также получить bearer token напрямую через Swagger или curl и передавать его в `Authorization: Bearer <token>`.

## 4. Test data checklist

Перед демо нужно подтвердить, что данных достаточно не только для красивых экранов, но и для live API.

| Что проверить | Как проверить | Ожидаемо |
|---|---|---|
| Услуги импортированы | `curl "http://localhost:8000/services?page=1&page_size=10"` | список не пустой |
| Синонимы услуг есть | SQL `select count(*) from service_synonyms;` | больше 0 после импорта справочника |
| Архив импортирован | `GET /admin/import-batches` с bearer token | есть хотя бы один batch |
| Файлы зарегистрированы | SQL `select count(*) from file_assets;` | больше 0 после импорта ZIP |
| Документы созданы | SQL `select count(*) from price_documents;` | больше 0 после импорта ZIP |
| Документы обработаны | `GET /admin/documents?status=parsed` | есть parsed-документы после process/reprocess |
| Активные цены есть | SQL `select count(*) from price_item_versions where is_active = true;` | больше 0 после обработки |
| Поиск работает | `curl "http://localhost:8000/search?q=blood&type=service"` | есть результаты на demo data |

Рекомендуемые demo-запросы для UI и API:

- `МРТ головы`;
- `УЗИ сердца`;
- `прием терапевта`;
- `Общий анализ крови`;
- `стоматолог`;
- `анализ крови`;
- `Astana`;
- `Астана`;
- `Almaty`;
- `Алматы`.

Важно: текущий synthetic demo data малый и может лучше отвечать на английские API-запросы вроде `blood`, `x-ray`, `consultation`, `MRI`. Русские медицинские запросы нужно проверить заранее на реальной или расширенной демо-базе.

## 5. Public frontend pages testing

Frontend содержит статичный Next.js export за Nginx. Экраны без live API wiring теперь показывают пустые состояния вместо демонстрационных данных.

| URL/path | Что должно быть | Ручной тест | Ожидаемый результат | Признаки ошибки |
|---|---|---|---|---|
| `/` | публичная поисковая главная | открыть страницу, проверить поисковый input, категории, карточки/таблицу результатов | страница открывается без 404, темная тема выглядит стабильно | пустой белый экран, 404, ошибки hydration, сломанные карточки |
| `/ru` | русская локализованная главная | открыть `/ru`, проверить язык UI | русский UI, URL остается `/ru` | русский текст на `/en` или английский на `/ru` |
| `/kz` | казахская локализованная главная | открыть `/kz` | казахский UI, route остается `/kz`, HTML lang после hydration должен быть `kk-KZ` | route сам меняется на `/kk`, metadata/язык остаются русскими |
| `/en` | английская локализованная главная | открыть `/en` | английский UI | смешанные языки в navigation/search |
| `/ru/search?q=МРТ&city=astana` | shareable search page | открыть URL напрямую | input восстанавливает `МРТ`, city сохраняется в query/state если фильтр доступен | query теряется после refresh |
| `/kz/search?q=МРТ&city=astana` | казахский search route | открыть URL напрямую, переключить язык | казахский UI, query params сохранены | переключатель языка теряет `q`/`city` |
| `/en/search?q=MRI&city=astana` | английский search route | открыть URL напрямую | английский UI, search state восстановлен | поиск не подхватывает URL |
| `/services/complete-blood-count` | service detail demo page | открыть страницу | таблица партнерских цен для услуги | 404 из-за Nginx static routing |
| `/partners/clinic-07` | partner detail placeholder page | открыть страницу | честное пустое состояние до P1-подключения live partner endpoint | 404 или fake-данные |
| `/ru/services/complete-blood-count` | localized service page | открыть и проверить title/UI | русские шаблоны вокруг названия услуги | metadata на русском отсутствует |
| `/kz/services/complete-blood-count` | localized service page | открыть | казахские шаблоны, route `/kz` | route `/kk`, русский metadata |
| `/en/services/complete-blood-count` | localized service page | открыть | английские шаблоны | смешанный UI |
| `/ru/clinics/clinic-07` | localized clinic page | открыть | страница клиники/партнера в русской локали | 404 |
| `/kz/clinics/clinic-07` | localized clinic page | открыть | казахская локаль | route/metadata не совпадают |
| `/en/clinics/clinic-07` | localized clinic page | открыть | английская локаль | route/metadata не совпадают |
| `/unknown-route` | not-found/fallback | открыть несуществующий путь | либо корректная SPA/static fallback-страница, либо понятный 404 | Nginx отдает неверный файл или бесконечный redirect |

Для Nginx static routing отдельно проверить:

```bash
curl -I http://localhost:3000/login
curl -I http://localhost:3000/services/complete-blood-count
curl -I http://localhost:3000/partners/clinic-07
```

Ожидаемо: HTTP 200 без редиректа. Запросы `/favicon.ico` и `/.well-known/appspecific/com.chrome.devtools.json` могут давать 404 и не являются критичной ошибкой.

## 6. Search testing roadmap

Проверять нужно отдельно frontend search UI и backend `/search`, потому что frontend пока не полностью подключен ко всем live API.

| Test case | Steps | Expected result | Priority |
|---|---|---|---|
| Точный запрос | Ввести `blood` на `/ru/search` или открыть `/ru/search?q=blood` | UI читает `q` из URL, вызывает `GET /search`, показывает реальные результаты или честное empty/error state | High |
| Частичный запрос | Ввести `blo` или часть названия услуги | есть результаты или понятное empty state | High |
| Опечатка | Ввести `blod test` | если fuzzy доступен через matching/API - есть близкий результат; иначе empty state без ошибки | Medium |
| Русский запрос | Ввести `Общий анализ крови` | результат появляется при наличии русских данных; иначе понятное no results | High |
| Казахский запрос | Открыть `/kz/search`, ввести казахский термин | UI не ломается; результаты зависят от данных | Medium |
| Английский запрос | Открыть `/en/search?q=MRI&city=astana` | query восстанавливается, UI на английском | High |
| Пустой запрос | Очистить input и отправить | не должно быть crash; показывается стартовое состояние или список | High |
| Нет результатов | Ввести бессмысленный запрос `zzzz-no-medical` | no results/empty state без backend 500 | High |
| City filter | Открыть `/ru/search?q=МРТ&city=astana` | city param сохраняется в URL; если фильтр есть, выбран Astana | High |
| Sort/filter | Использовать доступные сортировки/фильтры | URL или состояние обновляется без full reload, back/forward работает | Medium |
| Copy/share link | Нажать copy link/share action | clipboard получает текущий URL с query params; видно краткое success-состояние | High |
| Price comparison | Открыть service detail page | таблица показывает партнеров и цены; длинные значения не ломают layout | High |

Backend API search smoke:

```bash
curl "http://localhost:8000/search?q=blood&type=service&page=1&page_size=10"
curl "http://localhost:8000/search?q=clinic&type=partner&page=1&page_size=10"
```

Common failure signs:

- HTTP 500 на обычном поиске;
- query params исчезают из URL после refresh;
- на `/kz` или `/en` UI меняется, но metadata/title остаются русскими;
- пустая база выглядит как поломка, а не как empty state;
- поиск дергает API в бесконечном цикле.

## 7. Admin panel testing

Admin frontend pages в текущем проекте являются демонстрационными UI-экранами. Backend admin API реально защищен bearer-токеном.

### 7.1. Получение backend admin token

```bash
curl -X POST http://localhost:8000/admin/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"admin\"}"
```

Сохранить `access_token` и использовать:

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/admin/dashboard
```

### 7.2. Frontend admin pages

| URL/path | Auth | Manual test steps | Expected result | Risks |
|---|---|---|---|---|
| `/login` | backend auth через frontend | ввести неверные данные, затем реальные credentials из `.env` | неверные данные показывают error; валидный backend token сохраняется и переводит на `/dashboard` | нужен backend и CORS |
| `/dashboard` | UI route открыт | открыть после login | KPI cards с нулями и пустые состояния до подключения live API | counts не обновляются без frontend API adapter |
| `/imports` | UI route открыт | проверить drag-and-drop, file picker, submit | файл выбирается; submit честно сообщает, что frontend upload API не подключен | реальный импорт делать через Swagger/CLI |
| `/documents` | UI route открыт | проверить таблицу, фильтры status/format, actions | readable empty state, status/filter controls | live documents не подтягиваются без adapter |
| `/verification` | UI route открыт | открыть страницу | empty queue/detail state | live verification не подтягивается без adapter |
| `/unmatched` | UI route открыт | поискать service candidate, заполнить notes | manual matching flow понятен | может не вызывать backend `/match` |
| `/quality` | UI route открыт | открыть отчет | empty quality state, export disabled | live quality report не подтягивается без adapter |

### 7.3. Backend admin API pages/endpoints

| Endpoint | Auth | Manual test steps | Expected result | Risks |
|---|---|---|---|---|
| `GET /admin/dashboard` | bearer required | вызвать curl с token | counts по batches/documents/anomalies/price items | пустая база даст нули |
| `GET /admin/import-batches` | bearer required | после import archive вызвать endpoint | latest batch отображается | если ZIP не импортирован, список пуст |
| `GET /admin/documents` | bearer required | фильтровать по `status=pending/parsed/failed` | список документов и статусы | worker может быть выключен |
| `GET /admin/documents/{id}` | bearer required | открыть конкретный document id | document detail + processing events | неверный UUID -> 404 |
| `POST /admin/import/batches/{id}/process` | bearer required | отправить latest batch на процессинг | task id возвращается | Redis/worker down -> processing не пойдет |
| `POST /admin/documents/{id}/reprocess` | bearer required | reprocess одного документа | task id возвращается | документ может остаться pending без worker |
| `GET /admin/verification` | bearer required | открыть список | verification actions/anomalies | может быть пусто без anomaly data |
| `GET /unmatched` | bearer required | открыть список unmatched | candidates для ручной проверки | endpoint лежит без `/admin`, но защищен router dependency |
| `POST /match` | bearer required | отправить normalized row payload | top candidates с reasons/scores | формат payload нужно брать из Swagger |
| `POST /admin/price-items/{id}/verify` | bearer required | verify price item | action записан, flags resolved | нужен реальный price_item_id |
| `POST /admin/price-items/{id}/reject` | bearer required | reject price item | item inactive/action recorded | необратимое для демо действие, делать на synthetic data |
| `GET /admin/reports/quality` | bearer required | вызвать после обработки | aggregate quality metrics | без processed docs метрики нулевые |
| `GET /admin/files/{id}/preview` | bearer required | открыть known file_asset_id | файл stream/download | path safety и mime надо проверить |

## 8. Import and parser testing

### 8.1. Service directory import

Поддерживается XLSX и JSON импорт справочника услуг. Реальная organizer XLSX-форма должна содержать колонки вроде `ID`, `Специальность`, `Code`, `Name_ru`, `TarificatrCode`.

Команды:

```bash
python scripts/seed_demo_data.py
make import-services FILE=/app/data/samples/services.json
```

Проверка:

```bash
curl "http://localhost:8000/services?page=1&page_size=20"
```

SQL:

```sql
select count(*) from services;
select count(*) from service_synonyms;
select code, name_ru, category, tariff_code from services order by created_at desc limit 10;
```

Ожидаемо:

- импорт не падает на дубликатах;
- услуги и synonyms появились;
- broken rows дают warnings, а не полный crash;
- повторный запуск не создает хаотичные дубли.

### 8.2. ZIP archive import

Команда:

```bash
make import-archive FILE=/app/data/samples/archive.zip
```

Проверка API:

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/admin/import-batches
curl -H "Authorization: Bearer <token>" http://localhost:8000/admin/documents
```

SQL:

```sql
select count(*) from import_batches;
select count(*) from file_assets;
select count(*) from price_documents;
select status, count(*) from price_documents group by status order by status;
```

Ожидаемо:

- оригинальный ZIP сохранен;
- member files сохранены;
- `file_assets` имеют sha256;
- `price_documents` созданы в pending/registered состоянии;
- повторный импорт duplicate hashes обрабатывает безопасно.

### 8.3. Запуск process/reprocess

Через Swagger:

1. `POST /admin/login`;
2. Authorize bearer token;
3. `GET /admin/import-batches`;
4. `POST /admin/import/batches/{import_batch_id}/process`;
5. смотреть `GET /admin/documents`.

Fallback без worker:

```bash
docker compose run --rm backend python ../scripts/reprocess_document.py <price_document_id>
```

Quality report:

```bash
docker compose run --rm backend python ../scripts/generate_quality_report.py
```

### 8.4. Parser coverage

Из кода и тестов доступны:

| Формат | Что проверить | Ограничения |
|---|---|---|
| XLSX | multiple sheets, headers не на первой строке, category rows, merged cells, multi-price columns | matching отдельно, не часть parser test |
| XLS | LibreOffice conversion to XLSX | требует установленного LibreOffice в окружении |
| DOCX | таблицы, параграфы, raw text, row locator, tracked changes detection | fallback через LibreOffice практический, зависит от окружения |
| PDF text | PyMuPDF/pdfplumber text extraction, page locators, fragmented lines | OCR не запускается в этом path |
| PDF OCR candidate | pdf2image + Tesseract `rus+kaz+eng`, confidence, low-confidence rows | нужны системные зависимости Tesseract/poppler |

Признаки проблем:

- документ остается `failed` без понятной ошибки в `processing_events`;
- `parsed_summary` пустой для файла, который должен содержать таблицу цен;
- нет source locators;
- raw audit output отсутствует;
- повторный reprocess создает неконтролируемые дубли.

## 9. API manual testing

### Public endpoints

| Method/path | Purpose | Sample curl | Expected response |
|---|---|---|---|
| `GET /health` | healthcheck | `curl http://localhost:8000/health` | `{ "status": "ok", ... }` |
| `GET /services` | список услуг | `curl "http://localhost:8000/services?page=1&page_size=10"` | items + pagination |
| `GET /services/{id}/partners` | партнеры по услуге | `curl "http://localhost:8000/services/<service_id>/partners"` | partners/items for active price versions |
| `GET /partners` | список партнеров | `curl "http://localhost:8000/partners?page=1&page_size=10"` | derived partners |
| `GET /partners/{id}/services` | услуги партнера | `curl "http://localhost:8000/partners/<partner_id>/services"` | services/prices |
| `GET /search` | поиск услуг/партнеров | `curl "http://localhost:8000/search?q=blood&type=service"` | search results |

### Admin endpoints

Сначала получить token:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/admin/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"admin\"}" | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

PowerShell-вариант:

```powershell
$login = Invoke-RestMethod -Method Post -Uri http://localhost:8000/admin/login -ContentType "application/json" -Body '{"username":"admin","password":"admin"}'
$token = $login.access_token
```

| Method/path | Purpose | Sample curl | Common failure signs |
|---|---|---|---|
| `POST /admin/login` | получить bearer token | см. выше | 401 при неверных env credentials |
| `POST /admin/import/services` | upload XLSX/JSON service directory | использовать Swagger или multipart curl | 422 при неверном поле файла |
| `POST /admin/import/archive` | upload ZIP archive | использовать Swagger или multipart curl | 400/422 если не ZIP |
| `GET /admin/import-batches` | список batches | `curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/admin/import-batches` | 401 без token |
| `GET /admin/documents` | список документов | `curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/admin/documents` | пусто без import |
| `POST /admin/import/batches/{id}/process` | enqueue batch processing | Swagger удобнее | task есть, но worker может не обработать |
| `POST /admin/documents/{id}/reprocess` | enqueue one document | Swagger удобнее | 404 на неверный id |
| `GET /admin/dashboard` | операционные counts | `curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/admin/dashboard` | нули без данных |
| `GET /admin/reports/quality` | quality metrics | `curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/admin/reports/quality` | нули без processed data |
| `GET /admin/files/{id}/preview` | preview stored file | открыть в браузере с auth сложнее; Swagger/curl удобнее | 404 если file id не найден |

## 10. Database verification checklist

Подключение через Docker:

```bash
docker compose exec postgres psql -U medarchive -d medarchive
```

Полезные SQL-проверки:

```sql
-- Услуги и synonyms
select count(*) as services_count from services;
select count(*) as synonyms_count from service_synonyms;
select code, name_ru, category, tariff_code from services order by created_at desc limit 10;

-- Импортированные архивы и файлы
select count(*) as batches_count from import_batches;
select count(*) as files_count from file_assets;
select count(*) as documents_count from price_documents;
select status, count(*) from price_documents group by status order by status;

-- События обработки
select event_type, count(*) from processing_events group by event_type order by event_type;
select price_document_id, event_type, message, created_at
from processing_events
order by created_at desc
limit 20;

-- Matching и review
select decision, count(*) from matching_candidates group by decision order by decision;
select status, count(*) from verification_actions group by status order by status;
select flag_type, status, count(*) from anomaly_flags group by flag_type, status order by flag_type, status;

-- История цен
select count(*) as active_prices from price_item_versions where is_active = true;
select partner_name, service_id, effective_date, count(*)
from price_item_versions
where is_active = true
group by partner_name, service_id, effective_date
having count(*) > 1
order by count(*) desc;

-- Покрытие городов/регионов, если данные заполнены
select partner_region, count(*)
from price_item_versions
where partner_region is not null
group by partner_region
order by count(*) desc;
```

Если SQL падает из-за отсутствующей таблицы, сначала проверить миграции:

```bash
make migrate
```

## 11. Multilingual testing

Проект поддерживает public locale routes:

- `/ru`;
- `/kz`;
- `/en`.

Важно: URL для казахского языка остается `/kz`, но HTML language должен быть `kk-KZ` после клиентской инициализации. Не переименовывать route в `/kk`.

### Что проверить

| Проверка | Steps | Expected |
|---|---|---|
| RU default | открыть `/ru` | русский UI и русские SEO-шаблоны |
| KZ route | открыть `/kz` | казахский UI, URL `/kz`, HTML lang `kk-KZ` после hydration |
| EN route | открыть `/en` | английский UI |
| Search params | открыть `/ru/search?q=МРТ&city=astana` | input/query восстановлены |
| Language switcher | переключить `/ru/search?q=МРТ&city=astana` на KZ/EN | path locale меняется, `q` и `city` сохраняются |
| Metadata | открыть exported/static HTML после build | localized title/description/canonical/OG/Twitter для `/ru/search.html`, `/kz/search.html`, `/en/search.html` |
| Missing keys | временно проверить console/build warnings через `npm run i18n:check` | структуры ru/kz/en совпадают |

Команды frontend validation:

```bash
cd frontend
npm run i18n:check
npm run typecheck
npm run lint
npm run build
```

Проверка static export:

```bash
cd frontend
dir out
```

Проверить вручную файлы:

- `out/ru/search.html`;
- `out/kz/search.html`;
- `out/en/search.html`;
- `out/robots.txt`;
- `out/sitemap.xml`.

Known limitation: при `output: "export"` query-specific metadata для произвольных `?q=...&city=...` не может быть полноценно сгенерирована в static HTML. Search state должен восстанавливаться на клиенте, а базовая metadata локализуется на уровне route.

## 12. Responsive and visual QA

Проверять в Chrome DevTools или Playwright/browser:

| Viewport | Что смотреть |
|---|---|
| Desktop 1920px | широкие таблицы, side panels, dashboard cards, search layout |
| Laptop 1366px | основной demo-размер; ничего не должно вылезать за экран |
| Tablet 768px | sidebar/topbar, таблицы, карточки, фильтры |
| Mobile 390px | search input, buttons, cards, admin tables, detail pages |

Чеклист:

- темная тема единая на public/admin страницах;
- таблицы не ломают layout;
- длинные названия услуг переносятся;
- длинные названия клиник не перекрывают цены/кнопки;
- status badges одинакового стиля;
- empty/loading/error states выглядят как часть UI;
- кнопки имеют понятную иерархию;
- язык KZ/EN не ломает ширину кнопок;
- форма login удобна на mobile;
- copy/share button не перекрывает контент;
- нет горизонтального scroll там, где его не ожидает пользователь.

## 13. Error-state testing

| Сценарий | Как проверить | Expected |
|---|---|---|
| Backend down | остановить backend container, открыть frontend | frontend не падает полностью; live/API-зависимые части показывают error/empty если подключены |
| Empty database | поднять clean DB без imports | public API возвращает пустые списки без 500; UI показывает no data |
| No search results | поиск `zzzz-no-medical` | no results state |
| Invalid route | открыть `/not-existing-page` | понятный 404/fallback, не Nginx raw error |
| Invalid admin password | `/login` и `POST /admin/login` с неверными данными | UI error и API 401 |
| Missing bearer token | вызвать `/admin/dashboard` без token | 401/403 |
| Malformed service file | загрузить не JSON/XLSX в `/admin/import/services` | 400/422, без падения backend |
| Malformed ZIP | загрузить txt как archive | ошибка валидации, batch не создается |
| Worker down | остановить worker и enqueue processing | task может быть создан, документы не переходят в parsed; это нужно объяснить судьям |
| OCR dependencies missing | обработать OCR PDF без Tesseract/poppler | документ должен уйти в failed/warning, backend не падает |
| Duplicate import | импортировать один и тот же archive/service file дважды | дубликаты не должны ломать процесс |

## 14. Demo readiness script

### 2-minute judge demo checklist

1. Открыть `http://localhost:3000/ru`.
2. Показать, что это MedPrice: поиск цен по медицинским услугам и клиникам.
3. Ввести быстрый запрос из подготовленной backend-базы; frontend search должен вызвать `GET /search` и показать реальные результаты либо честное empty/error state.
4. Открыть service detail: `/ru/services/complete-blood-count`.
5. Показать сравнение партнеров и цен.
6. Открыть clinic detail: `/ru/clinics/clinic-07` или `/partners/clinic-07`.
7. Показать прозрачность источника: дата документа, история, партнерская информация.
8. Переключить язык RU -> KZ -> EN и показать, что URL и UI меняются.
9. Открыть `/login`, ввести `admin/admin`, перейти на `/dashboard`.
10. Показать admin dashboard, затем `/imports`, `/documents`, `/verification`, `/unmatched`, `/quality`.
11. Если backend live data готова: открыть Swagger `http://localhost:8000/docs`, показать `GET /admin/dashboard` или `GET /admin/reports/quality` с token.
12. Если import/parser не проверены на real data: не обещать полный production import; говорить, что synthetic happy path есть, real approved data требует финальной проверки.

Что не показывать, если не готово:

- реальные медицинские персональные данные;
- непроверенный большой ZIP;
- admin action reject/verify на единственной демо-записи;
- OCR demo без заранее проверенных системных зависимостей;
- пустые live API без объяснения, что frontend пока показывает честные empty states.

## 15. Critical bugs and risks checklist

| Area | What to check | Why it matters | Risk level | Fix priority |
|---|---|---|---|---|
| Docker startup | `make up`, `make migrate`, health | без этого demo не стартует | Critical | P0 |
| Nginx static routing | `/login`, `/services/complete-blood-count`, `/partners/clinic-07` | static export pages должны открываться без `.html` | High | P0 |
| Admin login | frontend `admin/admin`, backend `POST /admin/login` | judges могут попросить admin flow | High | P0 |
| Demo data | services/documents/prices counts > 0 | поиск без данных выглядит сломанным | Critical | P0 |
| Worker processing | batch process меняет statuses | end-to-end import зависит от worker | High | P1 |
| Search API | `/search?q=...` без 500 | основной value proposition | Critical | P0 |
| Frontend/live gap | empty UI vs backend data | frontend может не показывать live API без adapter | High | P1 |
| i18n metadata | `/kz` и `/en` metadata не русские | SEO/localization acceptance | Medium | P1 |
| Mobile layout | 390px responsive | demo могут смотреть с ноутбука/телефона | Medium | P2 |
| Parser dependencies | LibreOffice, Tesseract, poppler | XLS/OCR paths зависят от system tools | Medium | P2 |
| Real attached files | импорт real XLSX/ZIP | docs говорят, что real approved data еще не проверена | High | P1 |
| Security | default `admin/admin` | нельзя использовать на общем стенде | Medium | P1 |

## 16. Final go/no-go checklist

Перед отправкой/демо отметить:

- [ ] проект стартует из clean clone;
- [ ] `.env` создан из `.env.example`;
- [ ] `make up` проходит;
- [ ] `make migrate` проходит;
- [ ] `curl http://localhost:8000/health` возвращает 200;
- [ ] frontend открывается на `http://localhost:3000`;
- [ ] backend Swagger открывается на `http://localhost:8000/docs`;
- [ ] synthetic demo data сгенерирована;
- [ ] service directory импортирован;
- [ ] archive ZIP импортирован;
- [ ] batch/document processing выполнен или fallback reprocess проверен;
- [ ] база содержит services, documents, active price versions;
- [ ] `/search` API работает;
- [ ] минимум 5 demo-запросов проверены;
- [ ] `/login` переводит на `/dashboard` при `admin/admin`;
- [ ] backend `POST /admin/login` возвращает bearer token;
- [ ] admin dashboard API возвращает counts;
- [ ] quality report API возвращает metrics;
- [ ] public service page открывается;
- [ ] public clinic/partner page открывается;
- [ ] `/ru`, `/kz`, `/en` открываются;
- [ ] language switcher сохраняет query params;
- [ ] нет явных console errors в основных страницах;
- [ ] mobile layout приемлем;
- [ ] README quickstart команды соответствуют реальности;
- [ ] GitHub repository не содержит sensitive medical data;
- [ ] demo path отрепетирован за 2 минуты.

Go: все P0 пункты зеленые, demo data есть, search работает, frontend открывается.

No-go: не стартует Docker/backend, пустая база без fallback, search API падает, frontend routes дают 404.

## 17. Known limitations

- В README и docs проект называется MedArchive / MedPartners, а часть последних требований использует MedPrice. Перед демо нужно договориться о едином публичном названии.
- P0 frontend admin/public экраны подключены к live API, но P1 service/partner detail страницы и action-кнопки preview/reprocess/match/verify/reject пока остаются неподключенными.
- Partner APIs сейчас выводятся из active price item versions; отдельной production-таблицы партнеров нет.
- Real attached service directory и real archive ZIP в документации отмечены как еще не проверенные в PostgreSQL.
- Static export не может генерировать полноценную SEO metadata для бесконечного количества query URLs; search params восстанавливаются клиентом.
- `/kz` должен оставаться route convention, а HTML lang `kk-KZ` может выставляться клиентом после hydration, если root static HTML общий.
- OCR path зависит от локальных Tesseract/poppler и языков `rus+kaz+eng`.
- XLS conversion path зависит от LibreOffice.
- Simple admin auth подходит для hackathon demo, но не заменяет production RBAC/multi-user auth.
- Default `admin/admin` годится только для локального демо.
- External LLM, embeddings и currency conversion отключены по умолчанию и не обязательны для baseline.
- Synthetic demo data маленькая и не покрывает все русские/казахские медицинские запросы.

## 18. Recommended next testing improvements

Рекомендуемые автоматические проверки после ручного QA:

- backend API tests для всех public/admin endpoints с реальными fixture imports;
- Playwright smoke tests для `/`, `/ru/search`, `/kz/search`, `/en/search`, `/login`, `/dashboard`;
- Playwright test на language switcher с сохранением query params;
- static export test для `out/ru/search.html`, `out/kz/search.html`, `out/en/search.html`, `robots.txt`, `sitemap.xml`;
- parser fixture tests на маленькие golden XLSX, XLS, DOCX, PDF text, OCR PDF;
- duplicate import tests для service directory и archive ZIP;
- worker integration test с real Redis в Compose;
- visual regression screenshots для laptop 1366px и mobile 390px;
- i18n key structure check в CI через `npm run i18n:check`;
- manual-to-automated demo script, который поднимает стек, seed/import/process и проверяет 5 запросов.
