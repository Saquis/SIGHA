# German Del Rio
# Desarrollador Version 1.1 (Corregido)
# SIGHA - Sistema de Gestión de Horarios y Asignación
# services/horario_service.py: Lógica de IA con Groq y validaciones

import os
import json
import logging
from typing import List, Dict, Any
from groq import Groq
from sqlalchemy.orm import Session, joinedload
from app.models import Docente, Asignatura, Modulo, Horario

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generar_propuesta_ia(db: Session, modulo_id: str, carrera_id: str) -> List[Dict[str, Any]]:
    """
    Genera una propuesta de horario utilizando la IA de Groq.
    """
    try:
        # Cargar relaciones para evitar N+1 queries
        docentes = db.query(Docente).options(joinedload(Docente.usuario)).all()
        asignaturas = db.query(Asignatura).filter(
            Asignatura.carrera_id == carrera_id).all()
        modulo = db.query(Modulo).filter(Modulo.id == modulo_id).first()

        if not modulo:
            logger.error(f"Módulo {modulo_id} no encontrado")
            return []

        lista_docentes = [
            {"id": str(d.id), "nombre": d.usuario.nombre if d.usuario else "Sin nombre", "tipo": d.tipo} 
            for d in docentes
        ]
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
        - Un docente no puede estar en dos carreras distintas el mismo día a la misma hora.
        - Docentes tiempo_completo deben tener entre 272 y 380 horas por periodo (validar acumulado).
        - Distribuir las asignaturas entre todos los docentes disponibles de forma equitativa.
        - No asignar más de una vez la misma asignatura al mismo docente.

        DATOS:
        Docentes disponibles: {lista_docentes}
        Materias a asignar: {lista_materias}
        Módulo actual: {modulo.numero}
        Fecha inicio módulo: {modulo.fecha_inicio}
        Fecha fin módulo: {modulo.fecha_fin}

        Responde ÚNICAMENTE en formato JSON con esta estructura (sin markdown, solo JSON):
        {{
          "horarios": [
            {{"docente_id": "uuid-string", "asignatura_id": "uuid-string", "dia": "Lunes", "hora_inicio": "08:00", "hora_fin": "10:00", "jornada": "matutina", "paralelo": 1}}
          ]
        }}
        """

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            temperature=0.7
        )

        contenido = chat_completion.choices[0].message.content
        respuesta = json.loads(contenido)
        
        # Extracción segura de la lista de horarios
        if isinstance(respuesta, dict) and "horarios" in respuesta:
            return respuesta["horarios"]
        elif isinstance(respuesta, list):
            return respuesta
        else:
            logger.warning("Formato de respuesta IA inesperado")
            return []

    except Exception as e:
        logger.error(f"Error al generar propuesta con IA: {str(e)}")
        return []


def validar_horario_itq(propuesta: List[Dict[str, Any]], db: Session) -> List[str]:
    """
    Valida la propuesta de horario contra las reglas de negocio y la BD.
    """
    errores = []
    horarios_ocupados = {}  # {docente_id: [{'dia':..., 'inicio':..., 'fin':...}]}
    asignaturas_por_docente = {} # {docente_id: count}
    materias_por_docente = {} # {docente_id: set(asignatura_id)} para evitar duplicados
    horas_propuestas_por_docente = {} # {docente_id: horas_float}

    # 1. Pre-cargar horarios existentes para los docentes involucrados (Optimización)
    docentes_ids_propuesta = set(item['docente_id'] for item in propuesta)
    horarios_existentes_db = db.query(Horario).filter(
        Horario.docente_id.in_(docentes_ids_propuesta)
    ).all()

    # Estructurar horarios existentes para acceso rápido
    # {docente_id: [{'dia':..., 'inicio':..., 'fin':...}]}
    existentes_por_docente = {}
    for he in horarios_existentes_db:
        d_id = str(he.docente_id)
        if d_id not in existentes_por_docente:
            existentes_por_docente[d_id] = []
        existentes_por_docente[d_id].append({
            'dia': he.dia,
            'inicio': str(he.hora_inicio)[:5],
            'fin': str(he.hora_fin)[:5]
        })

    for item in propuesta:
        docente_id = str(item['docente_id'])
        asignatura_id = str(item['asignatura_id'])
        dia = item['dia']
        inicio = item['hora_inicio']
        fin = item['hora_fin']
        jornada = item['jornada']

        # --- Validaciones Internas (dentro de la propuesta) ---

        # 1. Choque de horario interno (dentro de la nueva propuesta)
        if docente_id not in horarios_ocupados:
            horarios_ocupados[docente_id] = []

        for h in horarios_ocupados[docente_id]:
            if h['dia'] == dia:
                # Verificar solapamiento de tiempos
                if not (fin <= h['inicio'] or inicio >= h['fin']):
                    errores.append(
                        f"Choque Interno: Docente {docente_id} tiene conflicto el {dia} de {h['inicio']} a {h['fin']} vs {inicio}-{fin}")

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
                errores.append(f"Error: Horario matutino fuera de rango (08:00-12:00)")
            if not ((inicio == "08:00" and fin == "10:00") or (inicio == "10:00" and fin == "12:00")):
                errores.append(f"Error: Bloque matutino inválido. Debe ser 08:00-10:00 o 10:00-12:00")

        if jornada == "nocturna":
            if inicio < "18:30" or fin > "21:30":
                errores.append(f"Error: Horario nocturno fuera de rango (18:30-21:30)")
            if not ((inicio == "18:30" and fin == "20:00") or (inicio == "20:00" and fin == "21:30")):
                errores.append(f"Error: Bloque nocturno inválido. Debe ser 18:30-20:00 o 20:00-21:30")

        # 4. Calcular horas por docente
        if docente_id not in horas_propuestas_por_docente:
            horas_propuestas_por_docente[docente_id] = 0
        
        if jornada == 'matutina':
            horas_propuestas_por_docente[docente_id] += 2
        elif jornada == 'nocturna':
            horas_propuestas_por_docente[docente_id] += 1.5

        # 5. Validar duplicidad de asignatura por docente
        if docente_id not in materias_por_docente:
            materias_por_docente[docente_id] = set()
        
        if asignatura_id in materias_por_docente[docente_id]:
            errores.append(f"Error: Docente {docente_id} tiene asignada la materia {asignatura_id} más de una vez")
        else:
            materias_por_docente[docente_id].add(asignatura_id)

        # --- Validaciones Externas (contra BD) ---

        # 6. Validar choques con horarios ya existentes en BD
        if docente_id in existentes_por_docente:
            for he in existentes_por_docente[docente_id]:
                if he['dia'] == dia:
                    # Verificar solapamiento con horario existente
                    if not (fin <= he['inicio'] or inicio >= he['fin']):
                        errores.append(
                            f"Choque con BD: Docente {docente_id} ya tiene clase el {dia} de {he['inicio']} a {he['fin']}")

    # 7. Validar horas docente tiempo completo (272-380 horas por periodo)
    # Se hace fuera del loop principal para consultar la BD una vez por docente único
    for docente_id, horas_nuevas in horas_propuestas_por_docente.items():
        docente = db.query(Docente).filter(Docente.id == docente_id).first()
        if docente and docente.tipo == "tiempo_completo":
            # Asumiendo que el modelo tiene el campo horas_acumuladas
            horas_actuales = getattr(docente, 'horas_acumuladas', 0) 
            total = horas_actuales + horas_nuevas
            
            if total > 380:
                errores.append(
                    f"Error Carga: Docente {docente_id} superaría las 380h permitidas (Actual: {horas_actuales}h + Nueva: {horas_nuevas}h)")

    return errores