### START #### 
uvicorn backend.app.services.main:app --reload --port 8000

npm start

.venv\Scripts\activate.bat

repomix


pip install -r requirements.txt

python -m backend.app.services.cli


Stop-Process -Name "ollama*" -Force -ErrorAction SilentlyContinue

$env:OLLAMA_MODELS = "C:\ollama_models"

ollama serve

ollama run qwen2.5-coder:7b


Proxom

sensors

watch -n 1 sensors

ssh Andrey@192.168.0.5





Bash
# 1. Создаем новое виртуальное окружение (папка .venv)
python -m venv .venv

# 2. Активируем его
# Если OS Windows (Command Prompt / cmd):
.venv\Scripts\activate
# Или если OS Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Если OS Linux / macOS:
source .venv/bin/activate

# 3. Обновляем pip (рекомендуется)
python -m pip install --upgrade pip

# 4. Устанавливаем зависимости из файла
pip install -r requirements.txt