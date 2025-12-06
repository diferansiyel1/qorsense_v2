# QorSense Tasarım ve Stil Rehberi

Bu belge, QorSense projesinin yeni marka kimliğini ve tasarım kurallarını tanımlar. Logo üzerinden türetilen renk paleti, uygulamanın hem frontend hem de backend (raporlama) bileşenlerinde tutarlı bir şekilde uygulanmıştır.

## 1. Renk Paleti

Marka kimliğimiz, teknolojik ve güvenilir bir imaj çizen Mor ve Mavi tonlarına dayanmaktadır.

### Birincil Renkler (Brand Core)
| Renk Adı | Hex Kodu | Kullanım Alanı | CSS Değişkeni |
|---|---|---|---|
| **Primary (Mor)** | `#af5ce0` | Ana aksiyon butonları, aktif navigasyon linkleri, ikon vurguları, önemli grafik çizgileri. | `--primary` |
| **Secondary (Mavi)** | `#2a44c7` | İkincil aksiyonlar, destekleyici grafik öğeleri, gradyan bitişleri. | `--secondary` |

### Nötr Renkler (Background & Surface)
| Renk Adı | Hex Kodu | Kullanım Alanı | CSS Değişkeni |
|---|---|---|---|
| **Background (Dark)** | `#0b0a14` | (Dark Mode) Ana sayfa arka planı. | `--background` |
| **Card (Surface)** | `#15141f` | (Dark Mode) Kartlar, paneller, modallar, sidebar arka planı. | `--card` |
| **Foreground (Text)** | `#ededf2` | (Dark Mode) Ana metin rengi. Okunabilirliği artırmak için hafif kırık beyaz. | `--foreground` |

### Durum Renkleri (Status)
| Renk Adı | Hex Kodu | Kullanım Alanı |
|---|---|---|
| **Success (Yeşil)** | `#10b981` | İşlem başarılı, sistem normal, yüksek sağlık skoru. |
| **Warning (Sarı)** | `#f59e0b` | Uyarılar, orta seviye risk, dikkat gerektiren durumlar. |
| **Destructive (Kırmızı)**| `#ef4444` | Hata, kritik risk, silme işlemleri. |

---

## 2. Kullanım Kuralları

### Butonlar
*   **Primary Button:** Arka plan `#af5ce0`, yazı rengi `white`. Hover durumunda parlaklık %10 artar.
*   **Secondary Button:** Arka plan `#2a44c7` veya şeffaf border'lı outline.
*   **Destructive Button:** Arka plan `#ef4444`.

### Grafikler (Charts)
Veri görselleştirmelerinde aşağıdaki renk sırası izlenmelidir:
1.  **Ana Veri Serisi:** `#af5ce0` (Primary)
2.  **Referans/Kıyaslama:** `#2a44c7` (Secondary)
3.  **Vurgu/Highlight:** `#d49bf5` (Primary Accent)
4.  **Hata/Limit:** `#ef4444` (Red)

### Tipografi
*   **Font Ailesi:** `Inter` veya `Roboto` (Modern sans-serif).
*   **Başlıklar:** Kalın (Bold), `#ededf2` (Dark Mode).
*   **Gövde Metni:** Normal (Regular), `#ededf2` (Dark Mode).
*   **Pasif Metin:** `#94a3b8` (Slate-400 equivalent).

---

## 3. Backend Raporlama (PDF)
PDF raporlarında da aynı marka renkleri kullanılmalıdır:
*   **Rapor Başlığı:** Siyah (`#000000`) veya Koyu Gri (`#1f2937`).
*   **Bölüm Başlıkları (H2):** Primary Color (`#af5ce0`).
*   **Ayırıcı Çizgiler:** Primary Color (`#af5ce0`).
*   **Tablo Başlıkları:** Primary Color (`#af5ce0`) arka plan kullanmaktan kaçınılmalı, bunun yerine metin rengi veya ince çizgilerle vurgulanmalıdır.

## 4. CSS Değişkenleri Entegrasyonu
Proje `shadcn/ui` ve `tailwindcss` altyapısını kullanmaktadır. Renkler `globals.css` içinde `HSL` formatında tanımlanmıştır.

Örnek Kullanım:
```tsx
// Tailwind Class
<div className="bg-primary text-primary-foreground">
  Buton
</div>

// Inline Style (Gerekirse)
style={{ color: 'hsl(var(--primary))' }}
```
