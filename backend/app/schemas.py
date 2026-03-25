# German Del Rio
# Desarrollador Version 1
# SIGHA - Sistema de Gestión de Horarios y Asignación
# schemas.py: Definición de esquemas Pydantic para validación y serialización

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, time
from uuid import UUID

# --- Usuario ---
class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol: str

class UsuarioOut(BaseModel):
    id: UUID
    nombre: str
    email: str
    rol: str
    class Config:
        from_attributes = True

# --- Auth ---
class Login(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Docente ---
class DocenteCreate(BaseModel):
    usuario_id: UUID
    tipo: str

class DocenteOut(BaseModel):
    id: UUID
    tipo: str
    horas_acumuladas: int
    usuario: UsuarioOut
    class Config:
        from_attributes = True

# --- Carrera ---
class CarreraCreate(BaseModel):
    nombre: str
    codigo: str

class CarreraOut(BaseModel):
    id: UUID
    nombre: str
    codigo: str
    class Config:
        from_attributes = True

# --- Asignatura ---
class AsignaturaCreate(BaseModel):
    carrera_id: UUID
    nombre: str
    nivel: int
    horas_semanales: int

class AsignaturaOut(BaseModel):
    id: UUID
    nombre: str
    nivel: int
    horas_semanales: int
    carrera: CarreraOut
    class Config:
        from_attributes = True

# --- Periodo Academico ---
class PeriodoCreate(BaseModel):
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    numero_paralelos: int

class PeriodoOut(BaseModel):
    id: UUID
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    numero_paralelos: int
    class Config:
        from_attributes = True

# --- Modulo ---
class ModuloCreate(BaseModel):
    periodo_id: UUID
    numero: int
    fecha_inicio: date
    fecha_fin: date

class ModuloOut(BaseModel):
    id: UUID
    numero: int
    fecha_inicio: date
    fecha_fin: date
    class Config:
        from_attributes = True

# --- Horario ---
class HorarioCreate(BaseModel):
    modulo_id: UUID
    docente_id: UUID
    asignatura_id: UUID
    carrera_id: UUID
    paralelo: int
    jornada: str
    dia: str
    hora_inicio: time
    hora_fin: time

class HorarioOut(BaseModel):
    id: UUID
    paralelo: int
    jornada: str
    dia: str
    hora_inicio: time
    hora_fin: time
    docente: DocenteOut
    asignatura: AsignaturaOut
    class Config:
        from_attributes = True      