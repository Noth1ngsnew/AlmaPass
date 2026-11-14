import { Component, ElementRef, OnDestroy, inject, signal, viewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { extractCheckinToken } from '../core/config';
import { TPipe } from '../core/i18n';

/** Встроенный в браузер распознаватель QR (есть в Chrome и Edge). */
interface QrDetector {
  detect(source: HTMLVideoElement): Promise<{ rawValue: string }[]>;
}

@Component({
  selector: 'app-scan',
  imports: [FormsModule, TPipe],
  template: `
    <div class="container page page--narrow">
      <h1 class="page__title">{{ 'scan.title' | t }}</h1>

      <div class="panel">
        <p class="muted">{{ 'scan.text' | t }}</p>

        <div class="scanner" [class.is-on]="active()">
          <video #video playsinline muted></video>
          <div class="scanner__frame" aria-hidden="true"></div>
        </div>

        @if (cameraError(); as key) {
          <p class="form-error" role="alert">{{ key | t }}</p>
        }

        @if (active()) {
          <button type="button" class="btn btn--ghost" (click)="stop()">{{ 'scan.stop' | t }}</button>
        } @else {
          <button type="button" class="btn" (click)="start()">{{ 'scan.start' | t }}</button>
        }

        <form class="manual" (ngSubmit)="submit()">
          <label class="field">
            <span>{{ 'scan.manual' | t }}</span>
            <input name="code" [(ngModel)]="code" [placeholder]="'scan.manualPlaceholder' | t" spellcheck="false" />
          </label>
          @if (badCode()) {
            <p class="form-error" role="alert">{{ 'scan.badCode' | t }}</p>
          }
          <button class="btn btn--ghost" type="submit" [disabled]="!code.trim()">{{ 'scan.submit' | t }}</button>
        </form>
      </div>
    </div>
  `,
})
export class Scan implements OnDestroy {
  private router = inject(Router);
  private video = viewChild.required<ElementRef<HTMLVideoElement>>('video');

  protected code = '';
  protected readonly active = signal(false);
  protected readonly cameraError = signal('');
  protected readonly badCode = signal(false);

  private stream: MediaStream | null = null;
  private timer: ReturnType<typeof setInterval> | null = null;

  protected async start(): Promise<void> {
    this.cameraError.set('');
    const Detector = (window as unknown as { BarcodeDetector?: new (o: { formats: string[] }) => QrDetector })
      .BarcodeDetector;
    if (!Detector || !navigator.mediaDevices?.getUserMedia) {
      this.cameraError.set('scan.noCamera');
      return;
    }
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
    } catch {
      this.cameraError.set('scan.denied');
      return;
    }
    const video = this.video().nativeElement;
    video.srcObject = this.stream;
    await video.play();
    this.active.set(true);

    const detector = new Detector({ formats: ['qr_code'] });
    this.timer = setInterval(async () => {
      try {
        const codes = await detector.detect(video);
        const token = codes.map((item) => extractCheckinToken(item.rawValue)).find(Boolean);
        if (token) this.go(token);
      } catch {
        /* кадр ещё не готов */
      }
    }, 300);
  }

  protected stop(): void {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = null;
    this.active.set(false);
  }

  protected submit(): void {
    const token = extractCheckinToken(this.code);
    this.badCode.set(!token);
    if (token) this.go(token);
  }

  private go(token: string): void {
    this.stop();
    this.router.navigate(['/checkin', token]);
  }

  ngOnDestroy(): void {
    this.stop();
  }
}
