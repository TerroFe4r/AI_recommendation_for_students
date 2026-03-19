"""
ORM модели для SQLAlchemy (альтернативный подход)
"""
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, Float, Enum, ForeignKey, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from ..config import DATABASE_URL

Base = declarative_base()


class Student(Base):
    """Модель студента"""
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True, autoincrement=True)
    last_name = Column(String(50), nullable=False)
    first_name = Column(String(50), nullable=False)
    middle_name = Column(String(50))
    gender = Column(Enum('М', 'Ж'), nullable=False)
    course = Column(Integer, default=2)
    department = Column(String(100), default='Прикладная информатика')
    login = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    salt = Column(String(32), nullable=False)

    attendance_records = relationship("Attendance", back_populates="student")
    session_results = relationship("Session", back_populates="student")

    def __repr__(self):
        return f"<Student(id={self.id}, name='{self.last_name} {self.first_name}')>"


class Subject(Base):
    """Модель дисциплины"""
    __tablename__ = 'subjects'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)

    attendance_records = relationship("Attendance", back_populates="subject")
    session_results = relationship("Session", back_populates="subject")
    schedule_items = relationship("Schedule", back_populates="subject")

    def __repr__(self):
        return f"<Subject(id={self.id}, name='{self.name}')>"


class Schedule(Base):
    """Модель расписания"""
    __tablename__ = 'schedule'

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)
    lesson_type = Column(Enum('лекция', 'практическое', 'лабораторная'), nullable=False)
    lesson_order = Column(Integer, nullable=False)  # 1-5 пары
    day_of_week = Column(Integer, nullable=False)  # 1-6
    week_number = Column(Integer, nullable=False)  # 1-2

    subject = relationship("Subject", back_populates="schedule_items")

    __table_args__ = (
        CheckConstraint('day_of_week BETWEEN 1 AND 6', name='check_day_of_week'),
        CheckConstraint('week_number IN (1, 2)', name='check_week_number'),
    )

    def __repr__(self):
        return f"<Schedule(id={self.id}, subject='{self.subject.name}', type='{self.lesson_type}')>"


class Attendance(Base):
    """Модель посещаемости и оценок"""
    __tablename__ = 'attendance'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)
    lesson_type = Column(Enum('лекция', 'практическое', 'лабораторная'), nullable=False)
    lesson_order = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    is_present = Column(Boolean, default=False)
    grade = Column(Integer, nullable=True)  # NULL для лекций

    student = relationship("Student", back_populates="attendance_records")
    subject = relationship("Subject", back_populates="attendance_records")

    __table_args__ = (
        CheckConstraint('grade BETWEEN 2 AND 5 OR grade IS NULL', name='check_grade'),
        CheckConstraint('lesson_order BETWEEN 1 AND 5', name='check_lesson_order'),
    )

    def __repr__(self):
        status = "✅" if self.is_present else "❌"
        return f"<Attendance(student_id={self.student_id}, subject='{self.subject.name}', date='{self.date}') {status}>"


class Session(Base):
    """Модель сессии"""
    __tablename__ = 'session'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)
    exam_type = Column(Enum('зачет', 'диф.зачет', 'экзамен'), nullable=False)
    attempt = Column(Integer, default=1)
    result = Column(String(20), nullable=False)
    status = Column(Enum('сдал', 'пересдача', 'комиссия', 'отчислен'), default='сдал')

    # Связи
    student = relationship("Student", back_populates="session_results")
    subject = relationship("Subject", back_populates="session_results")

    __table_args__ = (
        CheckConstraint('attempt IN (1, 2, 3)', name='check_attempt'),
    )

    def __repr__(self):
        return f"<Session(student_id={self.student_id}, subject='{self.subject.name}', result='{self.result}')>"


def init_db():
    """Инициализация базы данных"""
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()