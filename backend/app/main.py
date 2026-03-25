# German Del Rio

# Desarrollador Version 1

# SIGHA - Sistema de Gestión de Horarios y Asignación

# main.py: Configuración de FastAPI, middleware y routers



from dotenv import load_dotenv



# PRIMERO cargar variables ANTES de cualquier otro import

load_dotenv(encoding='latin-1')



from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware



# Importar motor de BD y Modelos

from app.database import engine, Base

import app.models



# Importar Routers

from app.routers import authr, docentes, asignaturas, horariosr, reportesr

# Importar router de periodos para crear automáticamente módulos al crear un periodo académico

from app.routers import periodosr



# Crear las tablas en la base de datos si no existen

Base.metadata.create_all(bind=engine)



app = FastAPI(title="SIGHA")



# Configuración CORS para Angular

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)



# Registrar los endpoints

app.include_router(authr.router)

app.include_router(docentes.router)

app.include_router(asignaturas.router)

app.include_router(horariosr.router)

app.include_router(reportesr.router)

app.include_router(periodosr.router)