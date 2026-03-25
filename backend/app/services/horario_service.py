# German Del Rio
# Desarrollador Version 1
# SIGHA - Sistema de Gestión de Horarios y Asignación
# services/horario_service.py: Lógica de IA con Groq y validaciones

import os
import json
from groq import Groq
from sqlalchemy.orm import Session
from app.models import Docente, Asignatura, Modulo, Horario

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generar_propuesta_ia(db: Session, modulo_id: str, carrera_id: str):
    docentes = db.query(Docente).all()
    asignaturas = db.query(Asignatura).filter(
        Asignatura.carrera_id == carrera_id).all()
    modulo = db.query(Modulo).filter(Modulo.id == modulo_id).first()

    lista_docentes = [
        {"id": str(d.id), "nombre": d.usuario.nombre, "tipo": d.tipo} for d in docentes]
    lista_materias = [{"id": str(
        a.id), "nombre": a.nombre, "horas": a.horas_semanales} for a in asignaturas]

    prompt = f"""
    Eres un experto en gestión académica para el ITQ.
    Genera un horario para el Módulo {modulo.numero} cumpliendo ESTRICTAMENTE estas reglas:

    REGLAS DE JORNADA:
    - Jornada Matutina: 08:00 a 12:00. Cada asignatura dura exactamente 2 horas.
      Bloques válidos: 08:00-10:00 o 10:00-12:00. Máximo 2 asignaturas matutinas por día.
    - Jornada Nocturna: 18:30 a 21:30. Cada asignatura dura exactamente 1:30 horas.
      Bloques válidos: 18:30-20:00 o 20:00-21:30. Máximo 2 asignaturas nocturnas por día.

    REGLAS DE DOCENTE:
    - Máximo 3 asignaturas por módulo por docente en total (matutina + nocturna).
    - No puede haber choques: mismo docente, mismo día, misma hora.
    - Docentes tiempo_completo deben tener entre 272 y 380 horas por periodo.

    DATOS:
    Docentes disponibles: {lista_docentes}
    Materias a asignar: {lista_materias}

    Responde ÚNICAMENTE en formato JSON con esta estructura:
    {{
      "horarios": [
        {{"docente_id": "uuid", "asignatura_id": "uuid", "dia": "Lunes", "hora_inicio": "08:00", "hora_fin": "10:00", "jornada": "matutina", "paralelo": 1}}
      ]
    }}
    """

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"}
    )

    respuesta = json.loads(chat_completion.choices[0].message.content)
    if isinstance(respuesta, dict):
        for key in respuesta:
            if isinstance(respuesta[key], list):
                return respuesta[key]
    return respuesta


def validar_horario_itq(propuesta, db: Session):
    errores = []
    horarios_ocupados = {}
    asignaturas_por_docente = {}
    horas_por_docente = {}

    for item in propuesta:
        docente_id = item['docente_id']
        dia = item['dia']
        inicio = item['hora_inicio']
        fin = item['hora_fin']
        jornada = item['jornada']

        # 1. Choque de horario
        if docente_id not in horarios_ocupados:
            horarios_ocupados[docente_id] = []

        for h in horarios_ocupados[docente_id]:
            if h['dia'] == dia:
                if not (fin <= h['inicio'] or inicio >= h['fin']):
                    errores.append(
                        f"Choque: Docente {docente_id} tiene conflicto el {dia} de {h['inicio']} a {h['fin']}")

        horarios_ocupados[docente_id].append(
            {'dia': dia, 'inicio': inicio, 'fin': fin})

        # 2. Máximo 3 asignaturas por módulo por docente
        if docente_id not in asignaturas_por_docente:
            asignaturas_por_docente[docente_id] = 0
        asignaturas_por_docente[docente_id] += 1
        if asignaturas_por_docente[docente_id] > 3:
            errores.append(
                f"Error: Docente {docente_id} supera el límite de 3 asignaturas por módulo")

        # 3. Validar duración exacta por jornada
        if jornada == "matutina":
            if inicio < "08:00" or fin > "12:00":
                errores.append(
                    f"Error: Horario matutino fuera de rango (08:00-12:00)")
            if not ((inicio == "08:00" and fin == "10:00") or (inicio == "10:00" and fin == "12:00")):
                errores.append(
                    f"Error: Bloque matutino inválido. Debe ser 08:00-10:00 o 10:00-12:00")

        if jornada == "nocturna":
            if inicio < "18:30" or fin > "21:30":
                errores.append(
                    f"Error: Horario nocturno fuera de rango (18:30-21:30)")
            if not ((inicio == "18:30" and fin == "20:00") or (inicio == "20:00" and fin == "21:30")):
                errores.append(
                    f"Error: Bloque nocturno inválido. Debe ser 18:30-20:00 o 20:00-21:30")

        # 4. Calcular horas por docente (matutina=2h, nocturna=1.5h)
        if docente_id not in horas_por_docente:
            horas_por_docente[docente_id] = 0
        if jornada == 'matutina':
            horas_por_docente[docente_id] += 2
        elif jornada == 'nocturna':
            horas_por_docente[docente_id] += 1.5

    # 5. Validar horas docente tiempo completo (272-380 horas por periodo)
    for docente_id, horas_propuesta in horas_por_docente.items():
        docente = db.query(Docente).filter(Docente.id == docente_id).first()
        if docente and docente.tipo == "tiempo_completo":
            total = docente.horas_acumuladas + horas_propuesta
            if total > 380:
                errores.append(
                    f"Error: Docente {docente_id} superaría las 380h permitidas (actual: {docente.horas_acumuladas}h + {horas_propuesta}h)")
    return errores