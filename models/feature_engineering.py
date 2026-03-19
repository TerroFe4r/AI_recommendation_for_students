#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для создания признаков на основе данных из БД
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from database.db_connector import DatabaseConnector


class FeatureEngineer:
    """Класс для создания признаков для ML моделей"""

    def __init__(self):
        self.db = DatabaseConnector()
        self.features_df = None
        self.target_df = None

    def load_data(self):
        """Загрузка данных из БД"""
        print("[*] Загрузка данных из MySQL...")

        if not self.db.connect():
            return False

        # Загружаем студентов
        self.students = pd.DataFrame(self.db.get_students())
        print(f"   Загружено студентов: {len(self.students)}")

        # Загружаем посещаемость
        self.attendance = pd.DataFrame(self.db.get_attendance())
        print(f"   Загружено записей посещаемости: {len(self.attendance)}")

        # Загружаем сессию
        self.session = pd.DataFrame(self.db.get_session_results())
        print(f"   Загружено записей сессии: {len(self.session)}")

        # Загружаем дисциплины
        self.subjects = pd.DataFrame(self.db.get_subjects())
        print(f"   Загружено дисциплин: {len(self.subjects)}")

        self.db.disconnect()
        return True

    def create_attendance_features(self):
        """Создание признаков на основе посещаемости"""
        print("[*] Создание признаков посещаемости...")

        features = []

        for student_id in self.students['id']:
            student_attendance = self.attendance[self.attendance['student_id'] == student_id]

            if len(student_attendance) == 0:
                continue

            # Общая посещаемость
            total_lessons = len(student_attendance)
            attended = student_attendance['is_present'].sum()
            attendance_rate = attended / total_lessons if total_lessons > 0 else 0

            # Посещаемость по типам занятий
            attendance_by_type = {}
            for lesson_type in ['лекция', 'практическое', 'лабораторная']:
                type_lessons = student_attendance[student_attendance['lesson_type'] == lesson_type]
                if len(type_lessons) > 0:
                    type_attended = type_lessons['is_present'].sum()
                    type_rate = type_attended / len(type_lessons)
                else:
                    type_rate = 0
                if lesson_type == 'лекция':
                    attendance_by_type['lecture_attendance_rate'] = type_rate
                elif lesson_type == 'практическое':
                    attendance_by_type['practical_attendance_rate'] = type_rate
                elif lesson_type == 'лабораторная':
                    attendance_by_type['lab_attendance_rate'] = type_rate

            # Средний балл за практические и лабораторные
            graded = student_attendance[student_attendance['grade'].notna()]
            avg_grade = graded['grade'].mean() if len(graded) > 0 else 0

            # Количество пропусков подряд
            attendance_series = student_attendance.sort_values('date')['is_present'].tolist()
            max_absent_streak = 0
            current_streak = 0
            for present in attendance_series:
                if not present:
                    current_streak += 1
                    max_absent_streak = max(max_absent_streak, current_streak)
                else:
                    current_streak = 0

            feature_row = {
                'student_id': student_id,
                'total_attendance_rate': attendance_rate,
                'avg_grade': avg_grade,
                'max_absent_streak': max_absent_streak,
                'total_lessons': total_lessons,
                'attended_lessons': attended
            }
            feature_row.update(attendance_by_type)
            features.append(feature_row)

        result = pd.DataFrame(features)
        print(f"   Создано {len(result)} записей признаков посещаемости")
        print(f"   Колонки: {list(result.columns)}")
        return result

    def create_session_features(self):
        """Создание признаков на основе результатов сессии"""
        print("[*] Создание признаков сессии...")

        features = []

        for student_id in self.students['id']:
            student_session = self.session[self.session['student_id'] == student_id]

            if len(student_session) == 0:
                continue

            # Количество сданных предметов
            passed = len(student_session[student_session['status'] == 'сдал'])
            total = len(student_session)
            pass_rate = passed / total if total > 0 else 0

            # Количество пересдач
            retakes = len(student_session[student_session['attempt'] > 1])

            # Средний балл
            graded = student_session[student_session['exam_type'].isin(['диф.зачет', 'экзамен'])]
            grades = []
            for _, row in graded.iterrows():
                try:
                    if row['result'].isdigit():
                        grades.append(int(row['result']))
                except:
                    pass

            avg_grade_session = np.mean(grades) if grades else 0

            status_counts = student_session['status'].value_counts().to_dict()

            features.append({
                'student_id': student_id,
                'passed_subjects': passed,
                'total_subjects': total,
                'pass_rate': pass_rate,
                'retakes_count': retakes,
                'avg_grade_session': avg_grade_session,
                'failed_subjects': status_counts.get('отчислен', 0),
                'retake_status': status_counts.get('пересдача', 0),
                'commission_status': status_counts.get('комиссия', 0)
            })

        result = pd.DataFrame(features)
        print(f"   Создано {len(result)} записей признаков сессии")
        return result

    def create_demographic_features(self):
        """Создание демографических признаков"""
        print("[*] Создание демографических признаков...")

        features = []

        for _, student in self.students.iterrows():
            gender_encoded = 1 if student['gender'] == 'М' else 0

            features.append({
                'student_id': student['id'],
                'gender_encoded': gender_encoded,
                'course': student['course']
            })

        result = pd.DataFrame(features)
        print(f"   Создано {len(result)} записей демографических признаков")
        return result

    def create_target_variable(self):
        """Создание целевой переменной для многоклассовой классификации"""
        print("[*] Создание целевой переменной...")

        targets = []
        class_counts = {0: 0, 1: 0, 2: 0}

        for student_id in self.students['id']:
            student_session = self.session[self.session['student_id'] == student_id]

            if len(student_session) == 0:
                continue

            has_failed_commission = any(
                (row['status'] == 'комиссия' and row['result'] in ['2', 'незачет'])
                for _, row in student_session.iterrows()
            )

            if has_failed_commission:
                target_class = 2
                class_counts[2] += 1
            else:
                max_attempt = student_session['attempt'].max()
                if max_attempt >= 2:
                    target_class = 1
                    class_counts[1] += 1
                else:
                    target_class = 0
                    class_counts[0] += 1

            graded = student_session[student_session['exam_type'].isin(['диф.зачет', 'экзамен'])]
            grades = []
            for _, row in graded.iterrows():
                try:
                    if row['result'].isdigit():
                        grade = int(row['result'])
                        if 2 <= grade <= 5:
                            grades.append(grade)
                        else:
                            print(f"   Предупреждение: оценка {grade} вне диапазона 2-5")
                except:
                    pass

            if grades:
                avg_grade = sum(grades) / len(grades)
                if avg_grade > 5:
                    print(f"   ВНИМАНИЕ! Средний балл {avg_grade} > 5, устанавливаю 5.0")
                    avg_grade = 5.0
            else:
                avg_grade = 3.0
            targets.append({
                'student_id': student_id,
                'target_class': target_class,
                'target_regression': avg_grade
            })

        result = pd.DataFrame(targets)
        print(f"   Распределение классов:")
        print(f"      0 (сдал): {class_counts[0]}")
        print(f"      1 (пересдача): {class_counts[1]}")
        print(f"      2 (комиссия): {class_counts[2]}")
        print(
            f"   Диапазон среднего балла: {result['target_regression'].min():.2f} - {result['target_regression'].max():.2f}")

        return result

    def create_all_features(self):
        """Создание всех признаков и объединение в один датасет"""
        print("\n" + "=" * 60)
        print("СОЗДАНИЕ ПРИЗНАКОВ ДЛЯ МОДЕЛЕЙ")
        print("=" * 60)

        # Загружаем данные
        if not self.load_data():
            return None

        # Создаем признаки
        attendance_feat = self.create_attendance_features()
        session_feat = self.create_session_features()
        demographic_feat = self.create_demographic_features()
        target = self.create_target_variable()

        # Объединяем все признаки
        print("[*] Объединение признаков...")

        result = demographic_feat
        result = result.merge(attendance_feat, on='student_id', how='left')
        result = result.merge(session_feat, on='student_id', how='left')
        result = result.merge(target, on='student_id', how='left')

        # Заполняем пропуски
        result = result.fillna(0)

        print(f"\n[OK] Итоговый датасет:")
        print(f"   Студентов: {len(result)}")
        print(f"   Признаков: {len(result.columns) - 1}")
        print(f"   Колонки: {list(result.columns)}")

        output_path = Path(__file__).parent.parent / 'data' / 'features.csv'
        result.to_csv(output_path, index=False, encoding='utf-8')
        print(f"[OK] Датасет сохранен в {output_path}")

        self.features_df = result
        return result

    def get_feature_summary(self):
        """Получение сводки по признакам"""
        if self.features_df is None:
            return "Датасет не создан"

        summary = []
        summary.append("\n" + "=" * 60)
        summary.append("СВОДКА ПО ПРИЗНАКАМ")
        summary.append("=" * 60)

        for col in self.features_df.columns:
            if col == 'student_id':
                continue

            dtype = self.features_df[col].dtype
            missing = self.features_df[col].isna().sum()
            unique = self.features_df[col].nunique()

            if dtype in ['int64', 'float64']:
                stats = f"min={self.features_df[col].min():.2f}, max={self.features_df[col].max():.2f}, mean={self.features_df[col].mean():.2f}"
            else:
                stats = f"unique values: {unique}"

            summary.append(f"\n{col}:")
            summary.append(f"   Тип: {dtype}")
            summary.append(f"   Пропуски: {missing}")
            summary.append(f"   {stats}")

        return "\n".join(summary)


def main():
    """Точка входа для создания признаков"""
    engineer = FeatureEngineer()
    features = engineer.create_all_features()

    if features is not None:
        print(engineer.get_feature_summary())


if __name__ == "__main__":
    main()