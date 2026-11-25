# Solucionador de Sudokus

Resuelve sudokus 9×9 de cualquier dificultad, incluidos los considerados más difíciles
(*AI Escargot*, *Everest* o sudokus de 17 pistas), normalmente en milisegundos.
Incluye una interfaz gráfica sencilla con Tkinter.

Python 3 puro, sin dependencias externas.

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
| 2  | Valor que falta en una fila/columna/bloque y no puede ir en ninguna de sus celdas |
| 3  | Celda con un candidato que no puede ir en su fila/columna/bloque |

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
python3 Solucionador_Sudokus_Avanzado.py
```

Resuelve cinco sudokus de ejemplo (AI Escargot, Everest, uno de 17 pistas, uno de dificultad
media y uno sin solución) y muestra la solución y el tiempo empleado.

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

Valores de retorno:

| Código | Significado |
|--------|-------------|
| 0 | Sudoku inválido |
| 1 | Sudoku sin solución |
| 2 | Error: algo no fue bien |
| 3 | Solución válida encontrada (el tablero queda resuelto) |

## Archivos

- `Solucionador_Sudokus_Avanzado.py`: el algoritmo y los ejemplos.
- `Interfaz_Usuario.py`: la interfaz gráfica con Tkinter.
