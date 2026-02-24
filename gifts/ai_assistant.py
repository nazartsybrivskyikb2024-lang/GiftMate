import google.generativeai as genai
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class GiftAIAssistant:
    """AI помічник для рекомендацій подарунків"""
    
    def __init__(self):
        # Налаштування API (замініть на ваш ключ)
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            logger.warning("GEMINI_API_KEY не встановлено в settings.py")
            raise ValueError("GEMINI_API_KEY не знайдено")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def get_gift_recommendation(self, user_profile=None, occasion=None, budget=None):
        """
        Отримати рекомендацію подарунку на основі вподобань користувача
        
        Args:
            user_profile: Profile об'єкт з інформацією про користувача
            occasion: Нагода (день народження, річниця тощо)
            budget: Бюджет у гривнях
        
        Returns:
            str: Рекомендація від AI
        """
        try:
            # Формуємо промпт на основі даних користувача
            prompt = self._build_prompt(user_profile, occasion, budget)
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.95,
                    max_output_tokens=500,
                ),
            )
            
            return response.text
        
        except Exception as e:
            logger.error(f"Помилка AI помічника: {e}")
            return "Вибачте, я не можу дати рекомендацію прямо зараз. Спробуйте пізніше."
    
    def get_gift_ideas(self, interests=None, count=3):
        """
        Отримати список ідей подарунків на основі інтересів
        
        Args:
            interests: Список або текст з інтересами (хобі)
            count: Кількість ідей
        
        Returns:
            str: Ідеї подарунків
        """
        try:
            interests_text = ", ".join(interests) if isinstance(interests, list) else (interests or "загальні интереси")
            
            prompt = f"""
Дай мені {count} ідей для подарунків людині, яка цікавиться: {interests_text}

Вимоги:
- Короткі, практичні ідеї (1-2 речення кожна)
- Від дешевих до дорогих
- Сучасні та популярні
- На українській мові

Формат: просто перелік нумерований 1, 2, 3...
            """
            
            response = self.model.generate_content(prompt)
            return response.text
        
        except Exception as e:
            logger.error(f"Помилка при отриманні ідей: {e}")
            return "Не удалось отримати ідеї. Спробуйте пізніше."
    
    def suggest_for_occasion(self, occasion, budget_min=None, budget_max=None):
        """
        Рекомендація подарунку для конкретної нагоди
        
        Args:
            occasion: Нагода (день народження, 8 березня, Новий рік тощо)
            budget_min: Мінімальний бюджет
            budget_max: Максимальний бюджет
        
        Returns:
            str: Рекомендація
        """
        try:
            budget_text = f"від {budget_min} до {budget_max} грн" if budget_max else f"до {budget_max} грн" if budget_max else "без обмежень"
            
            prompt = f"""
Порекомендуй 3-5 хороших подарунків для {occasion}.
Бюджет: {budget_text}

Вимоги:
- Практичні та популярні варіанти
- На українській мові
- Коротко (2-3 речення максимум)
- Зазначи приблизну ціну для кожного
            """
            
            response = self.model.generate_content(prompt)
            return response.text
        
        except Exception as e:
            logger.error(f"Помилка при рекомендації для нагоди: {e}")
            return "Не удалось дати рекомендацію. Спробуйте пізніше."
    
    def _build_prompt(self, user_profile, occasion, budget):
        """Формування промпту на основі даних профіля"""
        
        profile_info = ""
        if user_profile:
            profile_info = f"""
Інформація про користувача:
- Інтереси: {user_profile.interests or "не вказані"}
- Місцезнаходження: {user_profile.location or "не вказано"}
- День народження: {user_profile.birthday or "не вказано"}
            """
        
        occasion_info = f"Нагода: {occasion}" if occasion else ""
        budget_info = f"Бюджет: {budget} грн" if budget else ""
        
        prompt = f"""
Ти - експерт з підбору подарунків. Дай одну найкращу рекомендацію подарунку.

{profile_info}

{occasion_info}
{budget_info}

Вимоги:
- Будь конкретним
- На українській мові
- 2-3 речення максимум
- Зазначи приблизну ціну
- Обґрунтуй чому це буде гарним подарунком
        """
        
        return prompt


# Глобальний екземпляр помічника
_assistant = None


def get_ai_assistant():
    """Отримати екземпляр AI асистента (lazy loading)"""
    global _assistant
    if _assistant is None:
        try:
            _assistant = GiftAIAssistant()
        except Exception as e:
            logger.error(f"Не вдалося ініціалізувати AI асистента: {e}")
            return None
    return _assistant
