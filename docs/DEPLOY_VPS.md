# Выгрузка Instagram Viral Bot на VPS

## Что нужно на VPS

- **ОС:** Linux (Ubuntu 22.04 / Debian 12 удобнее всего)
- **Docker** и **Docker Compose** (v2)
- Доступ по **SSH** (логин + ключ или пароль)

---

## 1. Подготовка VPS (один раз)

Подключись по SSH и установи Docker, если ещё не установлен:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
# Выйди из SSH и зайди снова, чтобы группа docker применилась
```

Проверка:

```bash
docker --version
docker compose version
```

---

## 2. Выгрузка проекта на VPS

### Вариант A: с твоего ПК (Windows PowerShell)

Замени `USER` и `VPS_IP` на свои данные (например `root@123.45.67.89`).

```powershell
cd c:\Users\Admin\.cursor\instagram_bot

# Папка на сервере (создай при первом разе)
$REMOTE = "USER@VPS_IP:~/instagram_bot"

# Выгрузка кода (без .env и лишнего)
scp -r app docker-compose.yml Dockerfile requirements.txt .dockerignore .env.example $REMOTE/

# .env с секретами — отдельно (не в git)
scp .env $REMOTE/
```

Или используй готовый скрипт (см. ниже): отредактируй в нём `$VPS_HOST` и `$VPS_USER`, затем запусти `scripts/deploy-to-vps.ps1`.

### Вариант B: через Git (если проект в репозитории)

На VPS:

```bash
cd ~
git clone https://github.com/YOUR_USER/instagram_bot.git
cd instagram_bot
```

Файл `.env` в репозиторий не попадает — создай его на сервере вручную или скопируй с ПК:

```bash
# На ПК (PowerShell)
scp c:\Users\Admin\.cursor\instagram_bot\.env USER@VPS_IP:~/instagram_bot/.env
```

---

## 3. Настройка .env на сервере

На VPS в папке проекта должен быть файл `.env` с теми же переменными, что и локально. Можно скопировать с ПК (см. выше) или создать вручную:

```bash
cd ~/instagram_bot
nano .env
```

Обязательные переменные: `BOT_TOKEN`, `ADMIN_CHAT_ID`, `OPENROUTER_API_KEY`, `ORSHOT_API_KEY`, `APIFY_API_KEY`. Остальное можно скопировать из `.env.example`.

Для работы с Docker **не нужно** менять `DATABASE_URL` и `REDIS_URL` — они переопределяются в `docker-compose.yml` для контейнеров.

---

## 4. Запуск на VPS

На сервере:

```bash
cd ~/instagram_bot
docker compose up -d --build
```

Проверка контейнеров:

```bash
docker compose ps
```

Логи бота:

```bash
docker compose logs -f bot
```

Остановка:

```bash
docker compose down
```

Перезапуск после изменений:

```bash
docker compose up -d --build
```

---

## 5. Проверка и тест

1. В Telegram открой своего бота и отправь `/start`.
2. Должно прийти приветствие и меню (доступ только у пользователя с `ADMIN_CHAT_ID`).
3. Можно проверить парсинг: `/parse username` (подставь реальный Instagram username).

---

## 6. Безопасность (рекомендации)

- Смени пароль PostgreSQL в `docker-compose.yml` и в переменной `DATABASE_URL` в `environment` сервисов (вместо `secret_password_change_me`).
- Не открывай порты 5432 и 6379 в файрволе наружу — они нужны только внутри сервера для Docker.
- Храни `.env` только на сервере и не коммить его в git.

---

## 7. Обновление проекта на VPS

После изменений в коде:

```bash
# С ПК снова выгрузи файлы (scp или git pull на сервере)
# Затем на VPS:
cd ~/instagram_bot
docker compose up -d --build
```

Если менялся только код в `app/`, пересборка образа и перезапуск контейнеров подхватят изменения.
