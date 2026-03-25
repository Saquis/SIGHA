# German Del Rio
# Desarrollador Version 1
# SIGHA - Sistema de Gestión de Horarios y Asignación
# services/horario_service.py: Lógica de IA con Groq y validaciones

import os
import json
from groq import Groq
from sqlalchemy.orm import Session
from app.models import Docente, Asignatura, Modulo

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generar_propuesta_ia(db: Session, modulo_id: str, carrera_id: str):
    # 1. Obtener datos necesarios de la BD
    docentes = db.query(Docente).all()
    asignaturas = db.query(Asignatura).filter(Asignatura.carrera_id == carrera_id).all()
    modulo = db.query(Modulo).filter(Modulo.id == modulo_id).first()

    # 2. Construir el contexto para la IA
    # Simplificamos los datos para que el prompt no sea gigante
    lista_docentes = [{"id": str(d.id), "nombre": d.usuario.nombre, "tipo": d.tipo} for d in docentes]
    lista_materias = [{"id": str(a.id), "nombre": a.nombre, "horas": a.horas_semanales} for a in asignaturas]

    prompt = f"""
    Eres un experto en gestión académica para el ITQ. 
    Genera un horario para el Módulo {modulo.numero} cumpliendo estas reglas:
    - Jornada Matutina: 08:00 a 12:00.
    - Jornada Nocturna: 18:30 a 21:30.
    - No puede haber choques de docente a la misma hora.
    - Máximo 3 materias por módulo por docente.
    
    DATOS:
    Docentes disponibles: {lista_docentes}
    Materias a asignar: {lista_materias}
    
    Responde ÚNICAMENTE en formato JSON con esta estructura:
    [
      {{"docente_id": "uuid", "asignatura_id": "uuid", "dia": "Lunes", "hora_inicio": "08:00", "hora_fin": "12:00", "jornada": "matutina", "paralelo": 1}}
    ]
    """

    # 3. Llamada a Groq
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"}
    )

    respuesta = json.loads(chat_completion.choices[0].message.content)
    # La IA a veces devuelve {"horarios": [...]} en lugar de [...]
    if isinstance(respuesta, dict):
        # Buscar la primera lista dentro del dict
        for key in respuesta:
            if isinstance(respuesta[key], list):
                return respuesta[key]

    return respuesta


def validar_propuesta(propuesta_json, db: Session):
    """
    Aquí irá la lógica de 'El Juez':
    - Validar que no sumen más de 380 horas.
    - Validar que no haya choques de horas.
    """
    errores = []
    # Lógica de validación programática (Python puro)
    # Si todo está bien, retorna True, sino la lista de errores
    return errores if errores else True


# Validación específica para reglas del ITQ (choques y jornadas) 

def validar_horario_itq(propuesta, db: Session):
    errores = []
    horarios_ocupados = {}  # Para detectar choques: {docente_id: [(dia, inicio, fin)]}

    for item in propuesta:
        docente_id = item['docente_id']
        dia = item['dia']
        inicio = item['hora_inicio']
        fin = item['hora_fin']
        
        # 1. Validación de Choque de Horario (Mismo docente, mismo tiempo)
        if docente_id not in horarios_ocupados:
            horarios_ocupados[docente_id] = []
        
        for h in horarios_ocupados[docente_id]:
            if h['dia'] == dia:
                # Lógica simple de traslape de horas
                if not (fin <= h['inicio'] or inicio >= h['fin']):
                    errores.append(f"Choque: El docente {docente_id} ya tiene clase el {dia} de {h['inicio']} a {h['fin']}")
        
        horarios_ocupados[docente_id].append({'dia': dia, 'inicio': inicio, 'fin': fin})

        # 2. Validación de Jornadas (Regla ITQ)
        if item['jornada'] == "matutina" and (inicio < "08:00" or fin > "12:00"):
            errores.append(f"Error: Horario fuera de rango matutino (08:00-12:00) en {item['asignatura_id']}")
            
        if item['jornada'] == "nocturna" and (inicio < "18:30" or fin > "21:30"):
            errores.append(f"Error: Horario fuera de rango nocturno (18:30-21:30) en {item['asignatura_id']}")

    return errores