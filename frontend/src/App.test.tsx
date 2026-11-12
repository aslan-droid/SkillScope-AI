import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { MainLayout } from './layouts/MainLayout';
import { AboutPage } from './pages/AboutPage';
import { ErrorBanner, SyntheticDataBanner } from './components/StatusUI';

describe('SkillScope AI Frontend Bileşen ve Etkileşim Testleri', () => {
  it('Sidebar navigasyon menüsünü ve tüm ana modül bağlantılarını doğru şekilde render eder', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <MainLayout>
          <div>İçerik Alanı</div>
        </MainLayout>
      </MemoryRouter>
    );

    expect(screen.getByText('SkillScope')).toBeInTheDocument();
    expect(screen.getByText('İş Piyasası Analizi')).toBeInTheDocument();
    expect(screen.getByText('Beceri Keşfetme')).toBeInTheDocument();
    expect(screen.getByText('Kariyer Eşleştirme')).toBeInTheDocument();
    expect(screen.getByText('AI Kariyer Asistanı')).toBeInTheDocument();
    expect(screen.getByText('Veri Yönetimi')).toBeInTheDocument();
    expect(screen.getByText('Model Performansı')).toBeInTheDocument();
  });

  it('Karanlık ve Aydınlık tema geçiş butonunu çalıştırır', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <MainLayout>
          <div>Test</div>
        </MainLayout>
      </MemoryRouter>
    );

    const themeButton = screen.getByTitle('Temayı Değiştir');
    expect(themeButton).toBeInTheDocument();
    fireEvent.click(themeButton);
    expect(document.documentElement.classList.contains('dark')).toBe(false);
    fireEvent.click(themeButton);
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('Sentetik Demo Veri Etiketi bileşenini şeffaf biçimde gösterir', () => {
    render(<SyntheticDataBanner demoCount={72} realCount={5} />);
    expect(screen.getByText(/72 adet Sentetik Demo İlanı/i)).toBeInTheDocument();
  });

  it('Hata bildirimi ve Tekrar Dene etkileşimini çalıştırır', () => {
    const onRetryMock = vi.fn();
    render(<ErrorBanner message="Veritabanı bağlantısı zaman aşımına uğradı" onRetry={onRetryMock} />);
    expect(screen.getByText('Veritabanı bağlantısı zaman aşımına uğradı')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Tekrar Dene'));
    expect(onRetryMock).toHaveBeenCalledTimes(1);
  });

  it('Hakkında sayfasında sıfır bütçe mimarisini ve veri gizliliği ilkelerini gösterir', () => {
    render(<AboutPage />);
    expect(screen.getByText(/Teknoloji Yığını \(Sıfır Bütçe\)/i)).toBeInTheDocument();
    expect(screen.getByText(/CV Gizliliği:/i)).toBeInTheDocument();
  });
});
