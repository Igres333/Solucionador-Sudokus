# Solucionador de Sudokus

Resuelve sudokus 9×9 de cualquier dificultad, incluidos los considerados más difíciles
(*AI Escargot*, *Everest* o sudokus de 17 pistas), normalmente en milisegundos.
Incluye una interfaz gráfica sencilla con Tkinter.

Incluye dos implementaciones del mismo algoritmo:

- **`Solucionador_Sudokus_Avanzado.py`**: candidatos como `set` de Python. Más fácil de leer.
- **`Solucionador_Sudokus_Avanzado_Bitmask.py`**: candidatos como enteros de 9 bits.
  Misma API y mismo algoritmo, unas 3-4 veces más rápida.

Python 3 puro, sin dependencias externas (la versión con bitmasks requiere Python 3.10+
por `int.bit_count()`).

## Cómo funciona

1. **Validación**: comprueba que el tablero sea 9×9, que los valores sean enteros entre 0 y 9
   (0 = celda vacía) y que no haya repetidos en filas, columnas ni bloques.
2. **Candidatos**: calcula para cada celda vacía el conjunto de valores posibles.
3. **Lógica**: aplica en bucle *naked singles* (celdas con un único candidato) y
   *hidden singles* (valores que solo caben en una celda de su fila, columna o bloque).
4. **Búsqueda con backtracking**: si la lógica se atasca, elige la celda con menos candidatos
   (heurística MRV), prueba cada valor sobre una copia y vuelve al paso 3.

En cada paso se detectan contradicciones para podar ramas muertas cuanto antes:

| nº | Contradicción |
|----|---------------|
| 1  | Celda vacía sin candidatos |
| 2  | Dígito que falta en una unidad y no cabe en ninguna de sus celdas vacías |
| 3  | Dos dígitos que solo caben en la misma celda de una unidad |

*Unidad* = fila, columna o bloque 3×3. Las unidades y los 20 vecinos de cada celda se
precalculan una sola vez al cargar el módulo.

### Versión con bitmasks

En `Solucionador_Sudokus_Avanzado_Bitmask.py` los candidatos de cada celda se guardan en un
entero donde el bit `d - 1` está activo si el dígito `d` es candidato (p. ej. `0b000010101`
= {1, 3, 5}). Así las operaciones sobre candidatos son operaciones de bits:

| Operación | Código |
|-----------|--------|
| Añadir `d` | `mask \|= BIT[d]` |
| Quitar `d` | `mask &= ~BIT[d]` |
| ¿Es candidato? | `mask & BIT[d]` |
| Nº de candidatos | `mask.bit_count()` |
| ¿Un solo candidato? | `mask & (mask - 1) == 0` |

Los *hidden singles* se detectan con dos máscaras por unidad (dígitos que aparecen al menos
una vez y al menos dos veces), y copiar el estado en el backtracking es copiar listas de enteros.

## Uso

### Interfaz gráfica

```bash
python3 Interfaz_Usuario.py
```

Escribe los números conocidos, deja vacías las demás celdas y pulsa **Resolver Sudoku**.
**Reiniciar** limpia el tablero.

> En Linux puede hacer falta instalar Tkinter: `sudo apt install python3-tk`.

### Ejemplos por consola

```bash
python3 Solucionador_Sudokus_Avanzado.py          # versión con sets
python3 Solucionador_Sudokus_Avanzado_Bitmask.py  # versión con bitmasks
```

Resuelven cinco sudokus de ejemplo (AI Escargot, Everest, uno de 17 pistas, uno de dificultad
media y uno sin solución) y muestran la solución y el tiempo empleado.

Tiempos orientativos (Python 3.12):

| Sudoku | Sets | Bitmasks |
|--------|------|----------|
| AI Escargot | ~4,4 ms | ~1,2 ms |
| Everest | ~33 ms | ~9 ms |
| 17 pistas | ~3,5 ms | ~1,1 ms |
| Dificultad media | ~0,24 ms | ~0,10 ms |

### Desde código

```python
from Solucionador_Sudokus_Avanzado import solucionar_sudoku_avanzado

sudoku = [
    [1, 0, 0, 0, 0, 7, 0, 9, 0],
    [0, 3, 0, 0, 2, 0, 0, 0, 8],
    [0, 0, 9, 6, 0, 0, 5, 0, 0],
    [0, 0, 5, 3, 0, 0, 9, 0, 0],
    [0, 1, 0, 0, 8, 0, 0, 0, 2],
    [6, 0, 0, 0, 0, 4, 0, 0, 0],
    [3, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 4, 1, 0, 0, 0, 0, 0, 7],
    [0, 0, 7, 0, 0, 0, 3, 0, 0],
]

resultado = solucionar_sudoku_avanzado(sudoku)  # modifica `sudoku` en el sitio
```

Para usar la versión con bitmasks basta con cambiar el import:

```python
from Solucionador_Sudokus_Avanzado_Bitmask import solucionar_sudoku_avanzado
```

Valores de retorno:

| Código | Significado |
|--------|-------------|
| 0 | Sudoku inválido |
| 1 | Sudoku sin solución |
| 2 | Error: algo no fue bien |
| 3 | Solución válida encontrada (el tablero queda resuelto) |

## Archivos

- `Solucionador_Sudokus_Avanzado.py`: el algoritmo (candidatos con `set`) y los ejemplos.
- `Solucionador_Sudokus_Avanzado_Bitmask.py`: el mismo algoritmo con candidatos en bitmasks.
- `Interfaz_Usuario.py`: la interfaz gráfica con Tkinter (usa la versión con sets).
