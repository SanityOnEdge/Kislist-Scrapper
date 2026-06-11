# Prompt: porta.com.pl (PL)
Ta strona prezentuje drzwi (renderingi). Obrazy produktu zwykle znajdują się w ścieżkach typu `/phavi/do/...` i mogą być kilka wariantów rozdzielczości. Szukaj faktycznych renderów drzwi (front na białym/neutralnym tle). Odrzuć:
- bannery, social, logo (ścieżki `/img/social/*`, logo veneo itp.),
- grafiki informacyjne, menu, nagłówki.
Jeśli węzły sugerują klamki (nazwy serii: doro, simplo, euforia, fioro, segura, unico, eleganto, azura, lago, moderno, organic, lungo, fiumo), dodaj je do `handles`.
Zwróć JSON:
{
  "product_main": ["..."],
  "handles": ["..."],
  "ignore": ["..."],
  "ads": ["..."]
}
