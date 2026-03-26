// German Del Rio
// Desarrollador Version 1.2
// SIGHA - Sistema de Gestión de Horarios y Asignación

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-horarios',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './horarios.component.html'
})
export class HorariosComponent implements OnInit {
  horarios: any[] = [];
  modulos: any[] = [];
  carreras: any[] = [];
  moduloSeleccionado = '';
  carreraSeleccionada = '';
  error = '';
  mensaje = '';

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.cargarModulos();
    this.cargarCarreras();
  }

  // Cargar lista de módulos desde el backend
  cargarModulos() {
    this.http.get<any[]>(`${environment.apiUrl}/horarios/modulos`).subscribe({
      next: (data) => this.modulos = data,
      error: () => this.error = 'Error al cargar módulos'
    });
  }

  // Cargar lista de carreras desde el backend
  cargarCarreras() {
    this.http.get<any[]>(`${environment.apiUrl}/academic/carreras`).subscribe({
      next: (data) => this.carreras = data,
      error: () => this.error = 'Error al cargar carreras'
    });
  }

  // Cargar horarios filtrados por módulo seleccionado
  cargarHorarios() {
    if (!this.moduloSeleccionado) return; // Validar que haya módulo seleccionado
    this.http.get<any[]>(`${environment.apiUrl}/horarios/?modulo_id=${this.moduloSeleccionado}`).subscribe({
      next: (data) => this.horarios = data,
      error: () => this.error = 'Error al cargar horarios'
    });
  }

  // Generar horarios con IA enviando módulo y carrera
  generarHorarios() {
    if (!this.moduloSeleccionado || !this.carreraSeleccionada) {
      this.error = 'Seleccione módulo y carrera';
      return; // Validar campos obligatorios antes de llamar al backend
    }
    this.http.post(
      `${environment.apiUrl}/horarios/generar?modulo_id=${this.moduloSeleccionado}&carrera_id=${this.carreraSeleccionada}`,
      {}
    ).subscribe({
      next: (res: any) => {
        // Manejar respuesta condicional: requiere_ajuste vs éxito
        if (res.status === 'requiere_ajuste') {
          // Si requiere ajuste, guardamos la propuesta en la variable para poder editarla
          this.horarios = res.propuesta_sugerida; 
          this.error = 'Conflictos: ' + res.errores.join(' | ');
          this.mensaje = 'Por favor, edite los horarios y guarde manualmente.';
        } else {
          this.mensaje = res.mensaje;
          this.error = '';
          this.cargarHorarios(); // Recargar lista solo si se guardó en BD
        }
      },
      error: () => this.error = 'Error al generar horarios'
    });
  }

  // NUEVA FUNCIÓN: Guardar la planificación después de la edición manual
  guardarPlanificacionFinal() {
    if (!this.horarios || this.horarios.length === 0) {
      this.error = 'No hay horarios para guardar';
      return;
    }

    this.http.post(`${environment.apiUrl}/horarios/guardar_manual`, this.horarios).subscribe({
      next: (res: any) => {
        this.mensaje = 'Planificación final guardada con éxito';
        this.error = '';
        this.cargarHorarios(); 
      },
      error: (err) => {
        if (err.status === 409) {
          this.error = 'Error de validación: ' + err.error.detail.mensaje;
        } else {
          this.error = 'Error en el servidor al guardar la planificación';
        }
        this.mensaje = '';
      }
    });
  }

  // Eliminar un horario por ID
  eliminarHorario(id: string) {
    this.http.delete(`${environment.apiUrl}/horarios/${id}`).subscribe({
      next: () => {
        this.mensaje = 'Horario eliminado correctamente';
        this.error = '';
        this.cargarHorarios(); // Actualizar lista después de eliminar
      },
      error: () => this.error = 'Error al eliminar horario'
    });
  }
}