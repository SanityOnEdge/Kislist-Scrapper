# Prompt: lazienkarium.pl (PL)
Sklep e‑commerce z produktami łazienkowymi. Odszukaj zdjęcia produktowe w galeriach (główne renderingi/zdjęcia produktu). Odrzuć:
- bannery, social, logo, pop‑upy i overlaye,
- obrazy ikon, miniatur panelu, menu, breadcrumbs.
Preferuj największe obrazy (IMG/picture/srcset), jeśli dostępny jest og:image – przyjmij jako fallback.
Zwróć JSON:
{
  "product_main": ["..."],
  "handles": [],
  "ignore": ["..."],
  "ads": ["..."]
}