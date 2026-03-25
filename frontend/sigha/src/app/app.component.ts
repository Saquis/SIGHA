// German Del Rio
// Desarrollador Version 1
// SIGHA - Sistema de Gestión de Horarios y Asignación

import { Component } from '@angular/core';
import { RouterOutlet, RouterLink } from '@angular/router';
import { AuthService } from './core/services/auth.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, CommonModule],
  templateUrl: './app.component.html'
})
export class AppComponent {
  constructor(public authService: AuthService) {}
}