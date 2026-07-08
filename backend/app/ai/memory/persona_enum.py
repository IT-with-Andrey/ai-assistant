from enum import Enum

class PersonaEnum(str, Enum):
    DEFAULT = "default"
    HEALTH = "health_agent"
    PYTHON_TEACHER = "python_teacher"
    FITNESS_TRAINER = "fitness_trainer"
    ENGLISH_TEACHER = "english_teacher"