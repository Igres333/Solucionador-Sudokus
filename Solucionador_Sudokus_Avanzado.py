# ----------------------------------------------------------------------------------------
#
# LISTADO DE CONTRADICCIONES
# --------------------------
# nº1: Celda vacía sin candidatos
# nº2: Dígito que falta en una unidad y no cabe en ninguna de sus celdas vacías
# nº3: Dos dígitos que solo caben en la misma celda de una unidad
#
# Unidad = fila, columna o bloque 3x3
#
# ----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
# UNIDADES Y VECINOS (precalculados una sola vez)
# ----------------------------------------------------------------------------------------
FILAS    = [[(i, j) for j in range(9)] for i in range(9)]
COLUMNAS = [[(i, j) for i in range(9)] for j in range(9)]
BLOQUES  = [[(bi + x, bj + y) for x in range(3) for y in range(3)]
            for bi in range(0, 9, 3) for bj in range(0, 9, 3)]
UNIDADES = FILAS + COLUMNAS + BLOQUES

# Para cada celda, las 20 celdas que comparten fila, columna o bloque con ella
VECINOS = {
    (i, j): {c for u in UNIDADES if (i, j) in u for c in u} - {(i, j)}
    for i in range(9) for j in range(9)
}


# ----------------------------------------------------------------------------------------
# FUNCIONES DE AYUDA
# ----------------------------------------------------------------------------------------
def valores_fila(sudoku, i):
    """Devuelve el set de valores colocados en la fila i"""
    return set(sudoku[i]) - {0}

def valores_columna(sudoku, j):
    """Devuelve el set de valores colocados en la columna j"""
    return set(sudoku[x][j] for x in range(9)) - {0}

def valores_bloque(sudoku, i, j):
    """Devuelve el set de valores colocados en el bloque 3x3 que contiene la celda (i, j)"""
    bi, bj = 3 * (i // 3), 3 * (j // 3)
    return set(sudoku[bi + x][bj + y] for x in range(3) for y in range(3)) - {0}


# ----------------------------------------------------------------------------------------
# VALIDACIÓN DEL SUDOKU
# ----------------------------------------------------------------------------------------
def comprobar_sudoku(sudoku):
    """Comprueba que el sudoku sea una matriz 9x9 de enteros entre 0 y 9 sin valores
       repetidos en ninguna unidad. Los 0 representan celdas vacías"""
    # Comprobamos dimensiones
    if len(sudoku) != 9 or any(len(fila) != 9 for fila in sudoku):
        return False

    # Comprobamos tipo y rango de valores
    for fila in sudoku:
        for val in fila:
            # bool es subclase de int: True/False no son valores válidos
            if not isinstance(val, int) or isinstance(val, bool) or val < 0 or val > 9:
                return False

    # Comprobamos que no haya repetidos en filas, columnas ni bloques
    for celdas in UNIDADES:
        valores = [sudoku[i][j] for i, j in celdas if sudoku[i][j] != 0]
        if len(set(valores)) != len(valores):
            return False

    return True


# ----------------------------------------------------------------------------------------
# CONTROL DE CANDIDATOS
# ----------------------------------------------------------------------------------------
def calcular_candidatos(sudoku):
    """Devuelve una matriz 9x9 de sets con los candidatos de cada celda (vacío en las
       celdas ya colocadas), o None si alguna celda vacía se queda sin candidatos"""
    candidatos = [[set() for _ in range(9)] for _ in range(9)]

    for i in range(9):
        for j in range(9):
            if sudoku[i][j] == 0:
                usados = valores_fila(sudoku, i) | valores_columna(sudoku, j) | valores_bloque(sudoku, i, j)
                candidatos[i][j] = set(range(1, 10)) - usados
                if not candidatos[i][j]:
                    return None  # Contradicción nº1

    return candidatos


def actualizar_candidatos(sudoku, candidatos, celda):
    """Propaga la asignación recién hecha en celda = (i, j), eliminando su valor de los
       candidatos de sus vecinos. Devuelve False si algún vecino se queda sin candidatos"""
    i, j = celda
    val = sudoku[i][j]
    if val == 0:
        return True

    # La celda asignada ya no tiene candidatos
    candidatos[i][j].clear()

    for x, y in VECINOS[celda]:
        if sudoku[x][y] == 0:
            candidatos[x][y].discard(val)
            if not candidatos[x][y]:
                return False  # Contradicción nº1

    return True


# ----------------------------------------------------------------------------------------
# LÓGICA (NAKED SINGLES Y HIDDEN SINGLES)
# ----------------------------------------------------------------------------------------
def colocar_hidden(sudoku, candidatos, celdas):
    """Busca hidden singles en una unidad (lista de celdas (i, j)) y los coloca.
       Devuelve (ok, progreso): ok=False si hay contradicción, progreso=True si se colocó algo"""
    presentes = set(sudoku[i][j] for i, j in celdas) - {0}
    faltan = set(range(1, 10)) - presentes
    contador = {d: [] for d in faltan}  # dígito -> celdas donde puede ir

    for i, j in celdas:
        if sudoku[i][j] == 0:
            for d in candidatos[i][j]:
                contador[d].append((i, j))

    progreso = False
    for d, sitios in contador.items():
        if not sitios:
            return False, False  # Contradicción nº2
        if len(sitios) == 1:
            i, j = sitios[0]
            if sudoku[i][j] != 0:
                return False, False  # Contradicción nº3
            sudoku[i][j] = d
            if not actualizar_candidatos(sudoku, candidatos, (i, j)):
                return False, False  # Contradicción nº1
            progreso = True

    return True, progreso


def aplicar_logica(sudoku, candidatos):
    """Aplica naked singles y hidden singles hasta que no haya más progreso.
       Devuelve False si se encuentra una contradicción"""
    progreso_total = True
    while progreso_total:
        progreso_total = False

        # Naked singles: celdas con un único candidato
        progreso_naked = True
        while progreso_naked:
            progreso_naked = False
            for i in range(9):
                for j in range(9):
                    if sudoku[i][j] == 0 and len(candidatos[i][j]) == 1:
                        sudoku[i][j] = next(iter(candidatos[i][j]))
                        if not actualizar_candidatos(sudoku, candidatos, (i, j)):
                            return False  # Contradicción nº1
                        progreso_naked = True

        # Hidden singles: dígitos que solo caben en una celda de su unidad
        for celdas in UNIDADES:
            ok, progreso = colocar_hidden(sudoku, candidatos, celdas)
            if not ok:
                return False
            if progreso:
                progreso_total = True

    return True


# ----------------------------------------------------------------------------------------
# BACKTRACKING CON MRV
# ----------------------------------------------------------------------------------------
def resolver_recursivo(sudoku, candidatos):
    """Resuelve el sudoku in situ combinando lógica y backtracking. En cada nivel se
       ramifica sobre la celda con menos candidatos (MRV). Devuelve True si lo resuelve"""
    if not aplicar_logica(sudoku, candidatos):
        return False

    # Si ya está resuelto
    if all(0 not in fila for fila in sudoku):
        return True

    # MRV: celda con menos candidatos. Tras aplicar_logica no quedan celdas con uno
    # solo, así que si encontramos una con dos no hace falta seguir buscando
    min_candidatos = 10
    mejor_celda = None
    for i in range(9):
        for j in range(9):
            if sudoku[i][j] == 0 and len(candidatos[i][j]) < min_candidatos:
                min_candidatos = len(candidatos[i][j])
                mejor_celda = (i, j)
                if min_candidatos == 2:
                    break
        if min_candidatos == 2:
            break

    if mejor_celda is None:
        return False

    # Probamos cada candidato de la celda elegida sobre una copia y seguimos recursivamente
    i, j = mejor_celda
    for val in sorted(candidatos[i][j]):
        copia_sudoku = [fila[:] for fila in sudoku]
        copia_candidatos = [[s.copy() for s in fila] for fila in candidatos]
        copia_sudoku[i][j] = val

        if not actualizar_candidatos(copia_sudoku, copia_candidatos, (i, j)):
            continue  # Rama muerta, probamos el siguiente valor

        if resolver_recursivo(copia_sudoku, copia_candidatos):
            # Volcamos la solución; los candidatos ya no se van a usar
            for x in range(9):
                sudoku[x][:] = copia_sudoku[x]
            return True

    return False


# ----------------------------------------------------------------------------------------
# API PRINCIPAL
# ----------------------------------------------------------------------------------------
def imprimir_sudoku_como_lista(sudoku):
    """Imprime el sudoku con formato de lista de Python"""
    print("Sudoku = [")
    for fila in sudoku:
        print(str(fila) + ",")
    print("]")

def solucionar_sudoku_avanzado(sudoku):
    """Resuelve el sudoku in situ (los 0 representan celdas vacías).

    Devuelve
    --------
        0: Sudoku inválido
        1: Sudoku sin solución
        2: Error. Algo no fue bien
        3: Solución válida encontrada
    """
    # Comprobamos validez del sudoku propuesto
    if not comprobar_sudoku(sudoku):
        return 0

    # Calculamos los candidatos de todas las celdas
    candidatos = calcular_candidatos(sudoku)
    if candidatos is None:
        return 1

    if not resolver_recursivo(sudoku, candidatos):
        return 1

    # Comprobamos que el sudoku esté bien resuelto
    if not comprobar_sudoku(sudoku) or any(0 in fila for fila in sudoku):
        return 2

    return 3


# -----------------------------------------------------------------------------
# EJEMPLO DE USO
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import time
    sudokus = [None for _ in range(5)]

    sudokus[0] = [                   # AI Escargot
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
        
    sudokus[1] = [                   # Everest
            [8, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 3, 6, 0, 0, 0, 0, 0],
            [0, 7, 0, 0, 9, 0, 2, 0, 0],
            [0, 5, 0, 0, 0, 7, 0, 0, 0],
            [0, 0, 0, 0, 4, 5, 7, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 3, 0],
            [0, 0, 1, 0, 0, 0, 0, 6, 8],
            [0, 0, 8, 5, 0, 0, 0, 1, 0],
            [0, 9, 0, 0, 0, 0, 4, 0, 0],
    ]
        
    sudokus[2] = [                   # Sudoku de 17 pistas 
            [0, 0, 0, 0, 0, 0, 0, 1, 2],
            [0, 0, 0, 0, 3, 5, 0, 0, 0],
            [0, 0, 0, 7, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 3, 0, 0],
            [0, 0, 1, 0, 8, 0, 5, 0, 0],
            [0, 0, 9, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 2, 0, 0, 0],
            [0, 0, 0, 8, 4, 0, 0, 0, 0],
            [7, 2, 0, 0, 0, 0, 0, 0, 0],
    ]
        
    sudokus[3] = [                   # Sudoku dificultad media
            [0, 0, 0, 2, 6, 0, 7, 0, 1],
            [6, 8, 0, 0, 7, 0, 0, 9, 0],
            [1, 9, 0, 0, 0, 4, 5, 0, 0],
            [8, 2, 0, 1, 0, 0, 0, 4, 0],
            [0, 0, 4, 6, 0, 2, 9, 0, 0],
            [0, 5, 0, 0, 0, 3, 0, 2, 8],
            [0, 0, 9, 3, 0, 0, 0, 7, 4],
            [0, 4, 0, 0, 5, 0, 0, 3, 6],
            [7, 0, 3, 0, 1, 8, 0, 0, 0],
    ]
        
    sudokus[4] = [                   # Sudoku sin solución
            [5, 1, 6, 8, 4, 9, 7, 3, 2],
            [3, 0, 7, 6, 0, 5, 0, 0, 0],
            [8, 0, 9, 7, 0, 0, 0, 6, 5],
            [1, 3, 5, 0, 6, 0, 9, 0, 0],
            [4, 7, 2, 5, 9, 1, 0, 0, 6],
            [9, 6, 8, 3, 7, 0, 5, 0, 0],
            [2, 5, 3, 1, 8, 6, 0, 0, 7],
            [6, 8, 4, 2, 0, 7, 0, 5, 0],
            [7, 9, 1, 0, 5, 0, 6, 0, 0],
    ]

    for i, sudoku in enumerate(sudokus):
        print(str(i + 1) + ")")
        t_ini = time.perf_counter()
        idx = solucionar_sudoku_avanzado(sudoku)
        t_fin = time.perf_counter()

        if idx == 0:
            print("Sudoku inválido")
        elif idx == 1:
            print("Sudoku sin solución")
        elif idx == 2:
            print("Error. Algo no fue bien")
            imprimir_sudoku_como_lista(sudoku)
        elif idx == 3:
            print("Solución válida encontrada")
            imprimir_sudoku_como_lista(sudoku)
            print(f"Tiempo = {(t_fin - t_ini):.6}s")
        print("\n")

