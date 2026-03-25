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
  loading = false;

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.cargarDocentes();
  }

  cargarDocentes() {
    this.loading = true;
    this.http.get<any[]>(`${environment.apiUrl}/docentes/`).subscribe({
      next: (data) => {
        this.docentes = data;
        this.error = '';
        this.loading = false;
      },
      error: () => {
        this.error = 'Error al cargar docentes';
        this.loading = false;
      }
    });
  }

  crearDocente() {
    if (!this.nuevo.nombre || !this.nuevo.email || !this.nuevo.password) {
      this.error = 'Complete todos los campos';
      return;
    }

    this.loading = true;
    this.error = '';

    const usuarioData = {
      nombre: this.nuevo.nombre,
      email: this.nuevo.email,
      password: this.nuevo.password,
      rol: 'docente'
    };

    this.http.post<any>(`${environment.apiUrl}/auth/register`, usuarioData).subscribe({
      next: (usuario) => {
        const docenteData = {
          usuario_id: usuario.id,
          tipo: this.nuevo.tipo
        };
        this.http.post(`${environment.apiUrl}/docentes/`, docenteData).subscribe({
          next: () => {
            this.cargarDocentes();
            this.nuevo = { nombre: '', email: '', password: '', tipo: 'tiempo_completo' };
          },
          error: () => {
            this.error = 'Error al crear docente';
            this.loading = false;
          }
        });
      },
      error: () => {
        this.error = 'Error al registrar usuario';
        this.loading = false;
      }
    });
  }
}