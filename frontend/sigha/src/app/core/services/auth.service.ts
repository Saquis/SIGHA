// German Del Rio
// Desarrollador Version 1
// SIGHA - Sistema de Gestión de Horarios y Asignación

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class AuthService {

  constructor(private http: HttpClient, private router: Router) {}

  login(email: string, password: string) {
    return this.http.post<any>(`${environment.apiUrl}/auth/login`, { email, password });
  }

  guardarToken(token: string) {
    localStorage.setItem('token', token);
  }

  obtenerToken(): string | null {
    return localStorage.getItem('token');
  }

  obtenerRol(): string | null {
    const token = this.obtenerToken();
    if (!token) return null;
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.rol;
  }

  estaAutenticado(): boolean {
    return !!this.obtenerToken();
  }

  cerrarSesion() {
    localStorage.removeItem('token');
    this.router.navigate(['/login']);
  }
}