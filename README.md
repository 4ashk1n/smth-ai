# SMTH AI
ИИ часть проекта **SMTH**

## Установка
1. `git clone https://github.com/4ashk1n/smth-ai.git`
2. `cd smth-ai`
3. `cp .env.example .env`
4. Настроить переменные окружения в `.env`
5. `python -m venv venv`
6. `source venv/bin/activate` (Mac/Linux) / `./venv/Scripts/activate` (Windows)
7. `pip install -r requirements.txt`

## Запуск
1. Рекомендации
* Полный пересчет рекомендаций всех пользователей - Подключить cron к `python -m ai_module.features.recommendations.jobs.recompute_user_feed`
* Пересчет рекомендаций пользователя при получении новой метрики - `python -m ai_module.features.recommendations.jobs.poll_dirty_user_feed`
2. Подсказки ИИ GigaChat: `python -m ai_module.app.run_server --reload`
