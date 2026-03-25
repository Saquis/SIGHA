// German Del Rio
// Desarrollador Version 1
// SIGHA - Sistema de Gestión de Horarios y Asignación

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-docentes',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './docentes.component.html'
})
export class DocentesComponent implements OnInit {
  docentes: any[] = [];
  nuevo = { nombre: '', email: '', password: '', tipo: 'tiempo_completo' };
  error = '';

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.cargarDocentes();
  }

  cargarDocentes() {
    this.http.get<any[]>(`${environment.apiUrl}/docentes/`).subscribe({
      next: (data) => this.docentes = data,
      error: () => this.error = 'Error al cargar docentes'
    });
  }

  crearDocente() {
    this.http.post(`${environment.apiUrl}/docentes/`, this.nuevo).subscribe({
      next: () => {
        this.cargarDocentes();
        this.nuevo = { nombre: '', email: '', password: '', tipo: 'tiempo_completo' };
      },
      error: () => this.error = 'Error al crear docente'
    });
  }

  eliminarDocente(id: string) {
    this.http.delete(`${environment.apiUrl}/docentes/${id}`).subscribe({
      next: () => this.cargarDocentes(),
      error: () => this.error = 'Error al eliminar docente'
    });
  }
}