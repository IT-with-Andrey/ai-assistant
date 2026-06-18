import sys
import os

# Добавляем корень проекта в sys.path, чтобы тесты могли импортировать backend
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))