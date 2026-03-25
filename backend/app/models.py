# German Del Rio
# Desarrollador Version 1
# SIGHA - Sistema de Gestión de Horarios y Asignación
# models.py: Definición de modelos SQLAlchemy para la base de datos

from sqlalchemy import Column, String, Integer, Date, Time, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    rol = Column(Enum("coordinador", "docente", "administrativo", name="rol_enum"), nullable=False)
    docente = relationship("Docente", back_populates="usuario", uselist=False)

class Docente(Base):
    __tablename__ = "docentes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    tipo = Column(Enum("tiempo_completo", "tiempo_parcial", name="tipo_enum"), nullable=False)
    horas_acumuladas = Column(Integer, default=0)
    usuario = relationship("Usuario", back_populates="docente")
    horarios = relationship("Horario", back_populates="docente")

class Carrera(Base):
    __tablename__ = "carreras"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String, nullable=False)
    codigo = Column(String, unique=True, nullable=False)
    asignaturas = relationship("Asignatura", back_populates="carrera")

class Asignatura(Base):
    __tablename__ = "asignaturas"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    carrera_id = Column(UUID(as_uuid=True), ForeignKey("carreras.id"), nullable=False)
    nombre = Column(String, nullable=False)
    nivel = Column(Integer, nullable=False)
    horas_semanales = Column(Integer, nullable=False)
    carrera = relationship("Carrera", back_populates="asignaturas")

class PeriodoAcademico(Base):
    __tablename__ = "periodos_academicos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String, nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    numero_paralelos = Column(Integer, nullable=False)
    modulos = relationship("Modulo", back_populates="periodo")

class Modulo(Base):
    __tablename__ = "modulos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    periodo_id = Column(UUID(as_uuid=True), ForeignKey("periodos_academicos.id"), nullable=False)
    numero = Column(Integer, nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    periodo = relationship("PeriodoAcademico", back_populates="modulos")
    horarios = relationship("Horario", back_populates="modulo")

class Horario(Base):
    __tablename__ = "horarios"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    modulo_id = Column(UUID(as_uuid=True), ForeignKey("modulos.id"), nullable=False)
    docente_id = Column(UUID(as_uuid=True), ForeignKey("docentes.id"), nullable=False)
    asignatura_id = Column(UUID(as_uuid=True), ForeignKey("asignaturas.id"), nullable=False)
    carrera_id = Column(UUID(as_uuid=True), ForeignKey("carreras.id"), nullable=False)
    paralelo = Column(Integer, nullable=False)
    jornada = Column(Enum("matutina", "nocturna", name="jornada_enum"), nullable=False)
    dia = Column(String, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    modulo = relationship("Modulo", back_populates="horarios")
    docente = relationship("Docente", back_populates="horarios")
    asignatura = relationship("Asignatura")