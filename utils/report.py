#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для генерации отчетов по шаблону для деканата
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
import os
import sys

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️ ReportLab не установлен. Экспорт в PDF будет недоступен.")
    print("   Установите: pip install reportlab")


class ReportGenerator:
    """Класс для генерации отчетов для деканата"""

    def __init__(self):
        self.report_dir = Path(__file__).parent.parent / 'reports'
        self.report_dir.mkdir(exist_ok=True)

        self.font_name = 'Arial'
        self.font_name_bold = 'Arial-Bold'
        self._register_fonts()

    def _register_fonts(self):
        """Регистрация шрифтов с поддержкой кириллицы"""
        if not REPORTLAB_AVAILABLE:
            return

        try:
            if sys.platform == 'win32':
                font_paths = [
                    "C:/Windows/Fonts/arial.ttf",
                    "C:/Windows/Fonts/Arial.ttf",
                    "C:/Windows/Fonts/times.ttf",
                    "C:/Windows/Fonts/Times.ttf"
                ]

                bold_font_paths = [
                    "C:/Windows/Fonts/arialbd.ttf",
                    "C:/Windows/Fonts/Arialbd.ttf",
                    "C:/Windows/Fonts/timesbd.ttf",
                    "C:/Windows/Fonts/Timesbd.ttf"
                ]

                font_registered = False
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        pdfmetrics.registerFont(TTFont('Arial', font_path))
                        self.font_name = 'Arial'
                        font_registered = True
                        print(f"✅ Зарегистрирован шрифт: {font_path}")
                        break

                for font_path in bold_font_paths:
                    if os.path.exists(font_path):
                        pdfmetrics.registerFont(TTFont('Arial-Bold', font_path))
                        self.font_name_bold = 'Arial-Bold'
                        print(f"✅ Зарегистрирован жирный шрифт: {font_path}")
                        break

                if not font_registered:
                    print("⚠️ Шрифты не найдены, используем стандартный")
                    self.font_name = 'Helvetica'
                    self.font_name_bold = 'Helvetica-Bold'

            elif sys.platform == 'linux':
                font_paths = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                    "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf"
                ]

                for font_path in font_paths:
                    if os.path.exists(font_path):
                        pdfmetrics.registerFont(TTFont('Arial', font_path))
                        self.font_name = 'Arial'
                        print(f"✅ Зарегистрирован шрифт: {font_path}")
                        break
                else:
                    self.font_name = 'Helvetica'
                    self.font_name_bold = 'Helvetica-Bold'

            elif sys.platform == 'darwin':
                font_paths = [
                    "/Library/Fonts/Arial.ttf",
                    "/System/Library/Fonts/Helvetica.ttc"
                ]

                for font_path in font_paths:
                    if os.path.exists(font_path):
                        pdfmetrics.registerFont(TTFont('Arial', font_path))
                        self.font_name = 'Arial'
                        print(f"✅ Зарегистрирован шрифт: {font_path}")
                        break
                else:
                    self.font_name = 'Helvetica'
                    self.font_name_bold = 'Helvetica-Bold'

        except Exception as e:
            print(f"⚠️ Ошибка регистрации шрифтов: {e}")
            self.font_name = 'Helvetica'
            self.font_name_bold = 'Helvetica-Bold'

    def generate_dean_report_pdf(self, students_data, predictions, filename=None):
        """
        Генерация PDF-отчета для деканата

        Параметры:
        students_data (list): список студентов
        predictions (list): список прогнозов для студентов
        filename (str): имя файла (если None, генерируется автоматически)

        Возвращает:
        str: путь к созданному файлу
        """
        if not REPORTLAB_AVAILABLE:
            return self.generate_dean_report_txt(students_data, predictions, filename)

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dean_report_{timestamp}.pdf"

        filepath = self.report_dir / filename

        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
            encoding='utf-8'
        )

        elements = []

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName=self.font_name_bold,
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#2196F3')
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontName=self.font_name_bold,
            fontSize=14,
            spaceAfter=10
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=self.font_name,
            fontSize=10,
            spaceAfter=6
        )

        # Заголовок
        title = Paragraph("Отчет деканата", title_style)
        elements.append(title)

        # Дата
        date_text = Paragraph(f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}", normal_style)
        elements.append(date_text)
        elements.append(Spacer(1, 0.5 * cm))

        # Статистика
        stats = self._calculate_statistics(students_data, predictions)

        # Статистика в виде таблицы
        stats_data = [
            ["Показатель", "Значение"],
            ["Всего студентов", str(stats['total'])],
            ["Сдадут", f"{stats['passed']} ({stats['passed_percent']:.1f}%)"],
            ["Пересдача", f"{stats['retake']} ({stats['retake_percent']:.1f}%)"],
            ["Комиссия", f"{stats['commission']} ({stats['commission_percent']:.1f}%)"],
            ["Отчисление", f"{stats['expelled']} ({stats['expelled_percent']:.1f}%)"]
        ]

        stats_table = Table(stats_data, colWidths=[8 * cm, 6 * cm])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.font_name_bold),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 1), (-1, -1), self.font_name),
        ]))

        elements.append(stats_table)
        elements.append(Spacer(1, 1 * cm))

        # Заголовок таблицы студентов
        elements.append(Paragraph("Список студентов группы риска", heading_style))
        elements.append(Spacer(1, 0.3 * cm))

        # Таблица студентов группы риска
        risk_students = [p for p in predictions if p['predicted_class'] >= 1]

        if risk_students:
            risk_students.sort(key=lambda x: (-x['predicted_class'], -max(x['class_probabilities'].values())))

            table_data = [["ID", "Фамилия", "Имя", "Прогноз", "Вероятность", "Ср. балл"]]

            class_names = ['Сдаст', 'Пересдача', 'Комиссия', 'Отчислен']

            for pred in risk_students[:10]:
                student = next((s for s in students_data if s['id'] == pred['student_id']), None)
                if not student:
                    continue

                class_name = pred['predicted_class_name']
                prob = pred['class_probabilities'].get(class_name, 0) * 100

                table_data.append([
                    str(pred['student_id']),
                    student['last_name'],
                    student['first_name'],
                    class_names[pred['predicted_class']],
                    f"{prob:.1f}%",
                    f"{pred['predicted_grade']:.2f}"
                ])

            student_table = Table(table_data, colWidths=[2 * cm, 3 * cm, 3 * cm, 3.5 * cm, 3 * cm, 2.5 * cm])

            table_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), self.font_name_bold),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 1), (-1, -1), self.font_name),
            ]

            for i, pred in enumerate(risk_students[:20]):
                row = i + 1
                if pred['predicted_class'] == 3:  # Отчислен
                    table_style.extend([
                        ('TEXTCOLOR', (0, row), (-1, row), colors.red),
                        ('FONTNAME', (0, row), (-1, row), self.font_name_bold),
                    ])
                elif pred['predicted_class'] == 2:  # Комиссия
                    table_style.extend([
                        ('TEXTCOLOR', (0, row), (-1, row), colors.black),
                    ])

            student_table.setStyle(TableStyle(table_style))
            elements.append(student_table)
        else:
            elements.append(Paragraph("Нет студентов в группе риска", normal_style))

        elements.append(Spacer(1, 1 * cm))

        elements.append(Paragraph("Рекомендации деканату", heading_style))
        elements.append(Spacer(1, 0.3 * cm))

        recommendations = [
            "1. Провести индивидуальные встречи со студентами группы риска (классы 2-3).",
            "2. Организовать дополнительные консультации по предметам с низкой успеваемостью.",
            "3. Назначить кураторов для студентов с пересдачами (класс 1).",
            "4. Информировать родителей студентов группы риска о текущей ситуации."
        ]

        for rec in recommendations:
            elements.append(Paragraph(rec, normal_style))
            elements.append(Spacer(1, 0.1 * cm))

        elements.append(Spacer(1, 1 * cm))
        elements.append(Paragraph("С уважением,", normal_style))
        elements.append(Paragraph("Интеллектуальный агент", normal_style))
        elements.append(Paragraph(datetime.now().strftime("%d.%m.%Y"), normal_style))

        try:
            doc.build(elements)
            print(f"PDF отчет сохранен: {filepath}")
            return str(filepath)
        except Exception as e:
            print(f"Ошибка при создании PDF: {e}")
            return self.generate_dean_report_txt(students_data, predictions, filename.replace('.pdf', '.txt'))
    def generate_dean_report_txt(self, students_data, predictions, filename=None):
        """
        Генерация текстового отчета для деканата (резервный вариант)
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dean_report_{timestamp}.txt"
        elif filename.endswith('.pdf'):
            filename = filename.replace('.pdf', '.txt')

        filepath = self.report_dir / filename

        stats = self._calculate_statistics(students_data, predictions)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("ОТЧЕТ ДЛЯ ДЕКАНАТА\n")
            f.write(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
            f.write("=" * 70 + "\n\n")

            f.write("ОБЩАЯ СТАТИСТИКА:\n")
            f.write(f"   Всего студентов: {stats['total']}\n")
            f.write(f"   Сдадут: {stats['passed']} ({stats['passed_percent']:.1f}%)\n")
            f.write(f"   Пересдача: {stats['retake']} ({stats['retake_percent']:.1f}%)\n")
            f.write(f"   Комиссия: {stats['commission']} ({stats['commission_percent']:.1f}%)\n")
            f.write(f"   Отчисление: {stats['expelled']} ({stats['expelled_percent']:.1f}%)\n\n")

            f.write("СТУДЕНТЫ ГРУППЫ РИСКА:\n")
            risk_students = [p for p in predictions if p['predicted_class'] >= 1]
            risk_students.sort(key=lambda x: (-x['predicted_class'], -max(x['class_probabilities'].values())))

            class_names = ['Сдаст', 'Пересдача', 'Комиссия', 'Отчислен']

            if risk_students:
                for i, pred in enumerate(risk_students[:20]):
                    student = next((s for s in students_data if s['id'] == pred['student_id']), None)
                    if not student:
                        continue

                    class_name = pred['predicted_class_name']
                    prob = pred['class_probabilities'].get(class_name, 0) * 100

                    f.write(
                        f"\n   {i + 1}. {student['last_name']} {student['first_name']} (ID: {pred['student_id']})\n")
                    f.write(f"      Прогноз: {class_names[pred['predicted_class']]}\n")
                    f.write(f"      Вероятность: {prob:.1f}%\n")
                    f.write(f"      Средний балл: {pred['predicted_grade']:.2f}\n")
            else:
                f.write("   Нет студентов в группе риска\n")

            f.write("\n" + "=" * 70 + "\n")

        return str(filepath)

    def _calculate_statistics(self, students_data, predictions):
        """Расчет статистики по прогнозам"""
        total = len(predictions)
        passed = sum(1 for p in predictions if p['predicted_class'] == 0)
        retake = sum(1 for p in predictions if p['predicted_class'] == 1)
        commission = sum(1 for p in predictions if p['predicted_class'] == 2)
        expelled = sum(1 for p in predictions if p['predicted_class'] == 3)

        return {
            'total': total,
            'passed': passed,
            'retake': retake,
            'commission': commission,
            'expelled': expelled,
            'passed_percent': (passed / total * 100) if total > 0 else 0,
            'retake_percent': (retake / total * 100) if total > 0 else 0,
            'commission_percent': (commission / total * 100) if total > 0 else 0,
            'expelled_percent': (expelled / total * 100) if total > 0 else 0
        }

