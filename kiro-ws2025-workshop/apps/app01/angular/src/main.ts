import 'zone.js';
import { Component } from '@angular/core';
import { bootstrapApplication } from '@angular/platform-browser';

@Component({
  selector: 'app-root',
  standalone: true,
  template: `
    <main data-testid="angular-workshop">
      <h1>Kiro Windows Upgrade Workshop</h1>
      <p>Angular application hosted by IIS on APP01.</p>
      <dl>
        <dt>Application</dt><dd>kiro-workshop-angular</dd>
        <dt>Compatibility marker</dt><dd id="compatibility-marker">ANGULAR_OK_V1</dd>
      </dl>
      <nav>
        <a href="/spring/api/info">Spring Boot API</a>
        <a href="/next/">Next.js application</a>
        <a href="/data/api/status.php">PHP status</a>
      </nav>
    </main>
  `
})
class AppComponent {}

bootstrapApplication(AppComponent).catch((error: unknown) => console.error(error));
