#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Агент для генерации персонализированных рекомендаций студентам
Использует обученные модели и GigaChat API
"""

import sys
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from database.db_connector import DatabaseConnector
from config import GIGACHAT_CREDENTIALS

try:
    from gigachat import GigaChat

    GIGACHAT_AVAILABLE = True
except ImportError:
    GIGACHAT_AVAILABLE = False
    print("[WARN] GigaChat не установлен. Рекомендации будут генерироваться по шаблонам.")


class RecommendationAgent:
    """Агент для генерации персонализированных рекомендаций"""

    def __init__(self):
        self.db = DatabaseConnector()
        self.classifier = None
        self.regressor = None
        self.scaler = None
        self.feature_names = None
        self.client = None
        self.load_models()

        if GIGACHAT_AVAILABLE and GIGACHAT_CREDENTIALS:
            try:
                self.client = GigaChat(
                    credentials=GIGACHAT_CREDENTIALS,
                    verify_ssl_certs=False
                )
                print("[OK] GigaChat инициализирован")
            except Exception as e:
                print(f"[WARN] Не удалось инициализировать GigaChat: {e}")

    def load_models(self):
        """Загрузка обученных моделей"""
        models_dir = Path(__file__).parent.parent / 'models' / 'saved'

        try:
            self.classifier = joblib.load(models_dir / 'classifier.pkl')
            self.regressor = joblib.load(models_dir / 'regressor.pkl')
            self.scaler = joblib.load(models_dir / 'scaler.pkl')

            with open(models_dir / 'feature_names.txt', 'r', encoding='utf-8') as f:
                self.feature_names = [line.strip() for line in f.readlines()]

            print("[OK] Модели загружены")
            return True
        except Exception as e:
            print(f"[ERROR] Ошибка загрузки моделей: {e}")
            return False

    def get_student_data(self, student_id):
        """Получение данных студента из БД"""
        if not self.db.connect():
            return None

        student = self.db.get_student_by_id(student_id)
        attendance = pd.DataFrame(self.db.get_attendance(student_id))
        session = pd.DataFrame(self.db.get_session_results(student_id))

        self.db.disconnect()

        return {
            'student': student,
            'attendance': attendance,
            'session': session
        }

    def prepare_features_for_student(self, student_id):
        """Подготовка признаков для конкретного студента"""
        features_path = Path(__file__).parent.parent / 'data' / 'features.csv'
        df = pd.read_csv(features_path)

        student_features = df[df['student_id'] == student_id]

        if len(student_features) == 0:
            return None

        feature_values = student_features[self.feature_names].values
        feature_df = pd.DataFrame(feature_values, columns=self.feature_names)
        feature_values_scaled = self.scaler.transform(feature_df)

        return feature_values_scaled[0], student_features.iloc[0]

    def predict_student(self, student_id):
        """Прогнозирование для конкретного студента"""
        try:
            features_scaled, features_raw = self.prepare_features_for_student(student_id)

            if features_scaled is None:
                return None

            feature_df = pd.DataFrame([features_scaled], columns=self.feature_names)

            class_pred = self.classifier.predict(feature_df)[0]

            class_proba = self.classifier.predict_proba(feature_df)[0]

            full_proba = {}
            if hasattr(self.classifier, 'classes_'):
                for i, class_idx in enumerate(self.classifier.classes_):
                    full_proba[int(class_idx)] = float(class_proba[i])
            else:
                for i in range(len(class_proba)):
                    full_proba[i] = float(class_proba[i])

            for i in range(4):
                if i not in full_proba:
                    full_proba[i] = 0.0

            grade_pred = self.regressor.predict(feature_df)[0]

            class_names = ['сдал', 'пересдача', 'комиссия', 'отчислен']

            result = {
                'student_id': student_id,
                'predicted_class': int(class_pred),
                'predicted_class_name': class_names[int(class_pred)] if int(class_pred) < 4 else 'неизвестно',
                'class_probabilities': full_proba,  # Теперь это словарь с ключами 0,1,2,3
                'predicted_grade': float(grade_pred),
                'features': features_raw.to_dict()
            }

            return result

        except Exception as e:
            print(f"Ошибка прогноза для студента {student_id}: {e}")
            return None

    def get_risk_factors(self, features):
        """Выявление ключевых факторов риска"""
        risk_factors = []

        # Количество пересдач
        retakes = features.get('retakes_count', 0)
        if retakes > 5:
            risk_factors.append(f"Критическое количество пересдач ({retakes:.0f})")
        elif retakes > 3:
            risk_factors.append(f"Многократные пересдачи ({retakes:.0f})")
        elif retakes > 1:
            risk_factors.append(f"Есть пересдачи ({retakes:.0f})")

        # Посещаемость
        attendance = features.get('total_attendance_rate', 0)
        if attendance < 0.5:
            risk_factors.append(f"Критически низкая посещаемость ({attendance * 100:.1f}%)")
        elif attendance < 0.7:
            risk_factors.append(f"Низкая посещаемость ({attendance * 100:.1f}%)")
        elif attendance < 0.8:
            risk_factors.append(f"Посещаемость ниже среднего ({attendance * 100:.1f}%)")

        # Посещаемость лабораторных
        lab_attendance = features.get('lab_attendance_rate', 0)
        if lab_attendance < 0.5:
            risk_factors.append(f"Критические пропуски лабораторных ({lab_attendance * 100:.1f}%)")
        elif lab_attendance < 0.7:
            risk_factors.append(f"Пропуски лабораторных работ ({lab_attendance * 100:.1f}%)")

        # Текущие оценки
        avg_grade = features.get('avg_grade', 0)
        if avg_grade < 3:
            risk_factors.append(f"Критически низкие оценки ({avg_grade:.2f})")
        elif avg_grade < 3.5:
            risk_factors.append(f"Низкие текущие оценки ({avg_grade:.2f})")
        elif avg_grade < 4:
            risk_factors.append(f"Средние оценки ({avg_grade:.2f})")

        # Несданные предметы
        failed = features.get('failed_subjects', 0)
        if failed > 3:
            risk_factors.append(f"Множественные несданные предметы ({failed:.0f})")
        elif failed > 1:
            risk_factors.append(f"Есть несданные предметы ({failed:.0f})")

        return risk_factors

    def generate_recommendations(self, student_id, use_gigachat=True):
        """Генерация персонализированных рекомендаций"""

        prediction = self.predict_student(student_id)

        if prediction is None:
            return f"❌ Студент с ID {student_id} не найден"

        risk_factors = self.get_risk_factors(prediction['features'])

        if use_gigachat and self.client:
            return self._generate_with_gigachat(student_id, prediction, risk_factors)
        else:
            return self._generate_fallback(student_id, prediction, risk_factors)

    def _generate_with_gigachat(self, student_id, prediction, risk_factors):
        """Генерация через GigaChat"""

        factors_text = "\n".join(
            [f"• {f}" for f in risk_factors]) if risk_factors else "• Значимых факторов риска не выявлено"

        prob_0 = prediction['class_probabilities'].get(0, 0) * 100
        prob_1 = prediction['class_probabilities'].get(1, 0) * 100
        prob_2 = prediction['class_probabilities'].get(2, 0) * 100
        prob_3 = prediction['class_probabilities'].get(3, 0) * 100

        prompt = f"""Ты — академический консультант в университете. Напиши персонализированные рекомендации для студента.

    ДАННЫЕ СТУДЕНТА (ID: {student_id}):

    ПРОГНОЗ МОДЕЛИ:
    - Вероятность сдать с первого раза: {prob_0:.1f}%
    - Вероятность пересдачи: {prob_1:.1f}%
    - Вероятность комиссии: {prob_2:.1f}%
    - Вероятность отчисления: {prob_3:.1f}%
    - Прогнозируемый средний балл: {prediction['predicted_grade']:.2f}

    ВЫЯВЛЕННЫЕ ФАКТОРЫ РИСКА:
    {factors_text}

    Напиши доброжелательные, конкретные и практичные рекомендации для этого студента. 
    Используй обращение на "Вы". Раздели рекомендации на категории:
    1. Посещаемость
    2. Успеваемость
    3. Подготовка к сессии
    4. Доступные ресурсы помощи

    Заверши ободряющей фразой.
    """

        try:
            print("🔄 Отправка запроса к GigaChat...")

            response = self.client.chat(prompt)

            if hasattr(response, 'choices') and len(response.choices) > 0:
                recommendations = response.choices[0].message.content
            else:
                recommendations = str(response)

            print("✅ Ответ получен")

            result = f"""
    === РЕКОМЕНДАЦИИ ДЛЯ СТУДЕНТА {student_id} ===

    {recommendations}
    """
            return result

        except Exception as e:
            print(f"❌ Ошибка GigaChat: {e}")
            return self._generate_fallback(student_id, prediction, risk_factors)

    def _generate_fallback(self, student_id, prediction, risk_factors):
        """На случай отсутствия API"""

        class_desc = [
            "Вы успешно справляетесь с учебой. Рекомендуем поддерживать текущий темп.",
            "У вас есть риск пересдач. Рекомендуем уделить больше времени подготовке.",
            "Ситуация требует внимания. Рекомендуем срочно обратиться к преподавателям.",
            "Критическая ситуация. Необходима срочная консультация с деканатом."
        ]

        pred_class = prediction['predicted_class']

        factors_text = "\n".join(
            [f"• {f}" for f in risk_factors]) if risk_factors else "• Значимых факторов риска не выявлено"

        prob_0 = prediction['class_probabilities'].get(0, 0) * 100
        prob_1 = prediction['class_probabilities'].get(1, 0) * 100
        prob_2 = prediction['class_probabilities'].get(2, 0) * 100
        prob_3 = prediction['class_probabilities'].get(3, 0) * 100

        result = f"""
    Уважаемый студент!

    На основе анализа ваших данных мы подготовили следующие рекомендации.

    Ваш прогноз: {class_desc[pred_class]}
       • Вероятность сдать с первого раза: {prob_0:.1f}%
       • Вероятность пересдачи: {prob_1:.1f}%
       • Вероятность комиссии: {prob_2:.1f}%
       • Вероятность отчисления: {prob_3:.1f}%
       • Прогнозируемый средний балл: {prediction['predicted_grade']:.2f}

    Выявленные факторы риска:
    {factors_text}

    Рекомендации:

    По посещаемости:
       • Регулярно посещайте все лекции и практические занятия
       • При пропусках обязательно отрабатывайте материал
       • Записывайтесь на консультации к преподавателям

    По успеваемости:
       • Своевременно сдавайте лабораторные и практические работы
       • Участвуйте в дополнительных занятиях
       • Используйте материалы электронной библиотеки

    По подготовке к сессии:
       • Начните подготовку заранее
       • Посещайте предэкзаменационные консультации
       • Работайте в группах с одногруппниками

    Ресурсы помощи:
       • Учебный отдел: каб. 301
       • Психологическая поддержка: каб. 115
       • Электронная почта: dean@university.ru

    Желаем успехов в учебе!
    """
        return result

    def generate_dean_report(self, top_n=10):
        """Генерация отчета для деканата"""

        # Загружаем данные
        features_path = Path(__file__).parent.parent / 'data' / 'features.csv'
        df = pd.read_csv(features_path)

        # Получаем прогнозы для всех студентов
        predictions = []

        for student_id in df['student_id']:
            pred = self.predict_student(student_id)
            if pred:
                predictions.append(pred)

        predictions.sort(key=lambda x: (
            -x['predicted_class'],
            -x['class_probabilities'].get(x['predicted_class'], 0)))

        report = f"""
    ╔══════════════════════════════════════════════════════════════════╗
    ║              ОТЧЕТ ДЛЯ ДЕКАНАТА                                  ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║                      {pd.Timestamp.now().strftime('%d.%m.%Y %H:%M')}                      ║
    ╚══════════════════════════════════════════════════════════════════╝

    ОБЩАЯ СТАТИСТИКА:
       • Всего студентов: {len(predictions)}
       • Сдадут с первого раза: {sum(1 for p in predictions if p['predicted_class'] == 0)}
       • Пересдача: {sum(1 for p in predictions if p['predicted_class'] == 1)}
       • Комиссия: {sum(1 for p in predictions if p['predicted_class'] == 2)}
       • Отчисление: {sum(1 for p in predictions if p['predicted_class'] == 3)}

    СТУДЕНТЫ ГРУППЫ РИСКА (класс 2 и 3):
    """

        risk_students = [p for p in predictions if p['predicted_class'] >= 2]

        if risk_students:
            for i, pred in enumerate(risk_students[:top_n]):
                prob = pred['class_probabilities'].get(pred['predicted_class'], 0) * 100
                factors = self.get_risk_factors(pred['features'])
                factors_text = ', '.join(factors[:2]) if factors else "Нет"

                report += f"""
       {i + 1}. Студент ID: {pred['student_id']}
          Статус: {pred['predicted_class_name'].upper()}
          Вероятность: {prob:.1f}%
          Прогноз балла: {pred['predicted_grade']:.2f}
          Факторы риска: {factors_text}
    """
        else:
            report += "\n   ✅ Студентов группы риска нет\n"

        report += f"""
    СТУДЕНТЫ С ПЕРЕСДАЧАМИ (класс 1):
    """

        retake_students = [p for p in predictions if p['predicted_class'] == 1]

        if retake_students:
            for i, pred in enumerate(retake_students[:top_n]):
                prob = pred['class_probabilities'].get(1, 0) * 100

                report += f"""
       {i + 1}. Студент ID: {pred['student_id']}
          Вероятность пересдачи: {prob:.1f}%
          Прогноз балла: {pred['predicted_grade']:.2f}
    """
        else:
            report += "\n   Студентов с пересдачами нет\n"

        report += """

    РЕКОМЕНДАЦИИ ДЕКАНАТУ:
       1. Немедленно провести встречи со студентами группы риска (классы 2-3)
       2. Организовать дополнительные консультации по предметам с низкой успеваемостью
       3. Назначить кураторов для студентов с пересдачами (класс 1)
       4. Подготовить проекты приказов на отчисление для студентов класса 3
       5. Информировать родителей студентов группы риска

    ═══════════════════════════════════════════════════════════════════
    """

        return report


