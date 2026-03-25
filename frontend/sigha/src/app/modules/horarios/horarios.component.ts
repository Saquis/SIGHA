// German Del Rio
// Desarrollador Version 1
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

  cargarModulos() {
    this.http.get<any[]>(`${environment.apiUrl}/horarios/modulos`).subscribe({
      next: (data) => this.modulos = data,
      error: () => this.error = 'Error al cargar módulos'
    });
  }

  cargarCarreras() {
    this.http.get<any[]>(`${environment.apiUrl}/academic/carreras`).subscribe({
      next: (data) => this.carreras = data,
      error: () => this.error = 'Error al cargar carreras'
    });
  }

  cargarHorarios() {
    if (!this.moduloSeleccionado) return;
    this.http.get<any[]>(`${environment.apiUrl}/horarios/?modulo_id=${this.moduloSeleccionado}`).subscribe({
      next: (data) => this.horarios = data,
      error: () => this.error = 'Error al cargar horarios'
    });
  }

  generarHorarios() {
    if (!this.moduloSeleccionado || !this.carreraSeleccionada) {
      this.error = 'Seleccione módulo y carrera';
      return;
    }
    this.http.post(
      `${environment.apiUrl}/horarios/generar?modulo_id=${this.moduloSeleccionado}&carrera_id=${this.carreraSeleccionada}`,
      {}
    ).subscribe({
      next: (res: any) => {
        this.mensaje = res.mensaje;
        this.error = '';
        this.cargarHorarios();
      },
      error: () => this.error = 'Error al generar horarios'
    });
  }

  eliminarHorario(id: string) {
    this.http.delete(`${environment.apiUrl}/horarios/${id}`).subscribe({
      next: () => this.cargarHorarios(),
      error: () => this.error = 'Error al eliminar horario'
    });
  }
}