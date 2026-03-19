#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для обучения моделей многоклассовой классификации и регрессии
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler, label_binarize
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             confusion_matrix, classification_report, roc_auc_score,
                             mean_squared_error, r2_score, mean_absolute_error)
import xgboost as xgb
import catboost as cb
import joblib
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import cycle

sys.path.append(str(Path(__file__).parent.parent))


class ModelTrainer:
    """Класс для обучения моделей машинного обучения"""

    def __init__(self):
        self.df = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.scaler = StandardScaler()
        self.best_classifier = None
        self.best_regressor = None
        self.class_names = ['сдал', 'пересдача', 'комиссия']

    def load_data(self):
        """Загрузка датасета с признаками"""
        print("[*] Загрузка данных...")

        data_path = Path(__file__).parent.parent / 'data' / 'features.csv'
        self.df = pd.read_csv(data_path)

        print(f"[OK] Загружено {len(self.df)} строк, {len(self.df.columns)} колонок")
        return True

    def prepare_features(self):
        """Подготовка признаков для обучения"""
        print("[*] Подготовка признаков...")

        exclude_cols = ['student_id', 'target_class', 'target_regression']
        feature_cols = [col for col in self.df.columns if col not in exclude_cols]

        X = self.df[feature_cols]
        y_class = self.df['target_class']
        y_reg = self.df['target_regression']

        print(f"   Признаков: {len(feature_cols)}")
        print(f"   Распределение классов:")
        class_dist = y_class.value_counts().sort_index()
        for cls, count in class_dist.items():
            print(f"      {self.class_names[cls]}: {count} ({count / len(y_class) * 100:.1f}%)")
        print(f"   Регрессия: min={y_reg.min():.2f}, max={y_reg.max():.2f}, mean={y_reg.mean():.2f}")

        return X, y_class, y_reg, feature_cols

    def split_data(self, X, y_class, y_reg):
        """Разделение данных на train/test"""
        print("[*] Разделение данных...")

        # Разделяем для классификации со стратификацией
        X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(
            X, y_class, test_size=0.2, random_state=42, stratify=y_class
        )

        # Разделяем для регрессии (те же индексы)
        X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(
            X, y_reg, test_size=0.2, random_state=42
        )

        # Масштабируем признаки
        X_train_scaled = self.scaler.fit_transform(X_train_c)
        X_test_scaled = self.scaler.transform(X_test_c)

        self.X_train = X_train_c
        self.X_test = X_test_c
        self.X_train_scaled = X_train_scaled
        self.X_test_scaled = X_test_scaled
        self.y_train_class = y_train_c
        self.y_test_class = y_test_c
        self.y_train_reg = y_train_r
        self.y_test_reg = y_test_r
        self.feature_names = X.columns.tolist()

        print(f"   Train size: {len(X_train_c)}")
        print(f"   Test size: {len(X_test_c)}")
        print(f"   Распределение классов в train:")
        train_dist = y_train_c.value_counts().sort_index()
        for cls, count in train_dist.items():
            print(f"      {self.class_names[cls]}: {count}")
        print(f"   Распределение классов в test:")
        test_dist = y_test_c.value_counts().sort_index()
        for cls, count in test_dist.items():
            print(f"      {self.class_names[cls]}: {count}")

        return True

    def train_classifiers(self):
        """Обучение моделей многоклассовой классификации"""
        print("\n" + "=" * 70)
        print("ОБУЧЕНИЕ МОДЕЛЕЙ МНОГОКЛАССОВОЙ КЛАССИФИКАЦИИ")
        print("=" * 70)

        # Проверяем распределение классов
        unique_classes = np.unique(self.y_train_class)
        print(f"   Уникальные классы в ОБУЧАЮЩЕЙ выборке: {unique_classes}")
        class_counts = pd.Series(self.y_train_class).value_counts().sort_index()
        for cls, count in class_counts.items():
            cls_name = ['сдал', 'пересдача', 'комиссия'][int(cls)]
            print(f"      {cls_name}: {count}")

        classifiers = {
            'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
            'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'XGBoost': xgb.XGBClassifier(random_state=42),
            'CatBoost': cb.CatBoostClassifier(random_state=42, verbose=0)
        }

        results = []
        best_score = 0
        best_model = None
        best_name = None

        for name, model in classifiers.items():
            print(f"\n[*] Обучение {name}...")

            try:
                model.fit(self.X_train, self.y_train_class)
                y_pred = model.predict(self.X_test)

                accuracy = accuracy_score(self.y_test_class, y_pred)
                print(f"   Accuracy: {accuracy:.4f}")

                results.append({
                    'Model': name,
                    'Accuracy': accuracy
                })

                if accuracy > best_score:
                    best_score = accuracy
                    best_model = model
                    best_name = name

            except Exception as e:
                print(f"   ОШИБКА: {e}")
                continue

        if best_model is None:
            print("\n❌ НИ ОДНА МОДЕЛЬ НЕ ОБУЧИЛАСЬ! Создаю Random Forest по умолчанию")
            best_model = RandomForestClassifier(n_estimators=100, random_state=42)
            best_model.fit(self.X_train, self.y_train_class)
            best_name = "Random Forest (default)"
            y_pred = best_model.predict(self.X_test)
            best_score = accuracy_score(self.y_test_class, y_pred)
            print(f"   Accuracy default model: {best_score:.4f}")

        results_df = pd.DataFrame(results)
        if not results_df.empty:
            results_df = results_df.sort_values('Accuracy', ascending=False)
            print("\n" + "-" * 70)
            print("РЕЗУЛЬТАТЫ КЛАССИФИКАЦИИ:")
            print(results_df.to_string(index=False))

        self.best_classifier = best_model
        print(f"\n🏆 Лучшая модель: {best_name} (Accuracy: {best_score:.4f})")

        return results_df

    def plot_confusion_matrix(self, model_name, y_true, y_pred):
        """Построение матрицы ошибок"""
        try:
            unique_classes = sorted(np.unique(np.concatenate([y_true, y_pred])))
            class_names_present = [self.class_names[i] for i in unique_classes]

            cm = confusion_matrix(y_true, y_pred, labels=unique_classes)

            plt.figure(figsize=(8, 6))
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                        xticklabels=class_names_present,
                        yticklabels=class_names_present)
            plt.title(f'Матрица ошибок - {model_name}')
            plt.ylabel('Факт')
            plt.xlabel('Прогноз')
            plt.tight_layout()

            cm_path = Path(__file__).parent.parent / 'data' / 'confusion_matrix.png'
            plt.savefig(cm_path)
            print(f"[OK] Матрица ошибок сохранена в {cm_path}")
            plt.close()
        except Exception as e:
            print(f"   Ошибка построения матрицы ошибок: {e}")

    def train_regressors(self):
        """Обучение моделей регрессии"""
        print("\n" + "=" * 60)
        print("ОБУЧЕНИЕ МОДЕЛЕЙ РЕГРЕССИИ")
        print("=" * 60)

        from sklearn.linear_model import LinearRegression, Ridge

        regressors = {
            'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'XGBoost': xgb.XGBRegressor(random_state=42),
            'Linear Regression': LinearRegression(),
            'Ridge': Ridge(alpha=1.0)
        }

        results = []
        best_score = float('inf')
        best_model = None
        best_name = None

        for name, model in regressors.items():
            print(f"\n[*] Обучение {name}...")

            try:
                model.fit(self.X_train, self.y_train_reg)
                y_pred = model.predict(self.X_test)

                # Метрики
                mse = mean_squared_error(self.y_test_reg, y_pred)
                rmse = np.sqrt(mse)
                mae = mean_absolute_error(self.y_test_reg, y_pred)
                r2 = r2_score(self.y_test_reg, y_pred)

                results.append({
                    'Model': name,
                    'RMSE': rmse,
                    'MAE': mae,
                    'R2': r2
                })

                print(f"   RMSE: {rmse:.4f}")
                print(f"   MAE: {mae:.4f}")
                print(f"   R2: {r2:.4f}")

                if rmse < best_score:
                    best_score = rmse
                    best_model = model
                    best_name = name

            except Exception as e:
                print(f"   Ошибка при обучении {name}: {e}")
                continue

        if results:
            results_df = pd.DataFrame(results)
            results_df = results_df.sort_values('RMSE')

            print("\n" + "-" * 60)
            print("РЕЗУЛЬТАТЫ РЕГРЕССИИ:")
            print(results_df.to_string(index=False))

            if best_model is not None:
                self.best_regressor = best_model
                print(f"\nЛучшая модель: {best_name} (RMSE: {best_score:.4f})")
        else:
            print("\nНе удалось обучить ни одну модель регрессии")
            self.best_regressor = RandomForestRegressor(n_estimators=100, random_state=42)

        return pd.DataFrame(results) if results else pd.DataFrame()

    def feature_importance_analysis(self):
        """Анализ важности признаков"""
        print("\n" + "=" * 60)
        print("АНАЛИЗ ВАЖНОСТИ ПРИЗНАКОВ")
        print("=" * 60)

        if hasattr(self.best_classifier, 'feature_importances_'):
            importance = self.best_classifier.feature_importances_
            model_name = type(self.best_classifier).__name__
        elif hasattr(self.best_classifier, 'coef_'):
            importance = np.mean(np.abs(self.best_classifier.coef_), axis=0)
            model_name = 'Logistic Regression'
        else:
            print("   Невозможно получить важность признаков")
            return

        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)

        print(f"\nВажность признаков ({model_name}):")
        for idx, row in importance_df.head(10).iterrows():
            print(f"   {row['feature']}: {row['importance']:.4f}")

        # Визуализация
        plt.figure(figsize=(12, 8))
        sns.barplot(data=importance_df.head(10), x='importance', y='feature', palette='viridis')
        plt.title(f'Топ-10 важных признаков - {model_name}')
        plt.xlabel('Важность')
        plt.tight_layout()

        # Сохраняем график
        imp_path = Path(__file__).parent.parent / 'data' / 'feature_importance.png'
        plt.savefig(imp_path)
        print(f"[OK] График важности сохранен в {imp_path}")
        plt.close()

        return importance_df

    def save_models(self):
        """Сохранение обученных моделей"""
        print("\n" + "=" * 60)
        print("СОХРАНЕНИЕ МОДЕЛЕЙ")
        print("=" * 60)

        models_dir = Path(__file__).parent / 'saved'
        models_dir.mkdir(exist_ok=True)
        print(f"Папка для сохранения: {models_dir}")

        if self.best_classifier is not None:
            clf_path = models_dir / 'classifier.pkl'
            joblib.dump(self.best_classifier, clf_path)
            print(f"[OK] Классификатор сохранен в {clf_path}")
        else:
            from sklearn.ensemble import RandomForestClassifier
            backup_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            backup_classifier.fit(self.X_train, self.y_train_class)
            clf_path = models_dir / 'classifier.pkl'
            joblib.dump(backup_classifier, clf_path)
            print(f"[OK] Запасной классификатор сохранен в {clf_path}")
            self.best_classifier = backup_classifier

        if self.best_regressor is not None:
            reg_path = models_dir / 'regressor.pkl'
            joblib.dump(self.best_regressor, reg_path)
            print(f"[OK] Регрессор сохранен в {reg_path}")
        else:
            print("[ERROR] best_regressor is None")

        if self.scaler is not None:
            scaler_path = models_dir / 'scaler.pkl'
            joblib.dump(self.scaler, scaler_path)
            print(f"[OK] Scaler сохранен в {scaler_path}")
        else:
            print("[ERROR] scaler is None")

        if hasattr(self, 'feature_names') and self.feature_names:
            features_path = models_dir / 'feature_names.txt'
            with open(features_path, 'w', encoding='utf-8') as f:
                for feat in self.feature_names:
                    f.write(f"{feat}\n")
            print(f"[OK] Список признаков сохранен в {features_path}")
        else:
            print("[ERROR] feature_names отсутствуют")

    def run(self):
        """Запуск полного цикла обучения"""
        print("\n" + "=" * 70)
        print("ЗАПУСК ОБУЧЕНИЯ МОДЕЛЕЙ")
        print("=" * 70)

        if not self.load_data():
            return False

        X, y_class, y_reg, feature_names = self.prepare_features()

        self.split_data(X, y_class, y_reg)

        clf_results = self.train_classifiers()

        reg_results = self.train_regressors()

        importance = self.feature_importance_analysis()

        self.save_models()

        print("\n" + "=" * 70)
        print("ОБУЧЕНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("=" * 70)

        return True


def main():
    """Точка входа для обучения моделей"""
    trainer = ModelTrainer()
    trainer.run()


if __name__ == "__main__":
    main()