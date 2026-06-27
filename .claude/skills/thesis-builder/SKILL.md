---
name: thesis-builder
description: Guía el flujo de trabajo para convertir una hipótesis macro (tesis temática) en una lista de candidatas de acciones analizadas. Útil al trabajar con src/thesis_energy.py o al crear un nuevo script de tesis temática.
---

# thesis-builder

Esta skill estructura el flujo "de hipótesis macro a candidatas concretas" usado en `src/thesis_energy.py`.

## Flujo recomendado

1. **Formula la hipótesis explícitamente** en una frase, p. ej. "la demanda de energía sube por la IA y los datacenters". Si el usuario da algo vago, pide que lo concrete en una hipótesis comprobable.
2. **Define un universo de partida** — sectores o tickers plausiblemente afectados por la hipótesis. Que sea editable, no hardcodeado de forma rígida.
3. **Elige 2-4 filtros cuantitativos** relacionados con la tesis (crecimiento de ingresos, márgenes, valoración, etc.), no docenas — el objetivo es una lista corta, no una base de datos completa.
4. **Ejecuta el screening** y revisa los resultados.
5. **Señala explícitamente cuándo los datos contradicen la tesis** — por ejemplo, si una candidata "obvia" no cumple los filtros, dilo en vez de omitirla en silencio. Esto es la regla más importante de esta skill: no presentar solo confirmaciones de la hipótesis.
6. **Entrega una lista corta con next steps**, no una recomendación de inversión — el siguiente paso siempre es análisis manual adicional (noticias, comparables, riesgos).

## Notas

- Reutiliza el patrón `_try_endpoints` de `src/thesis_energy.py` si un endpoint de screener/fundamentales no responde como se espera.
- Nunca presentes la lista de candidatas como una recomendación de compra; es un punto de partida para investigación propia.
