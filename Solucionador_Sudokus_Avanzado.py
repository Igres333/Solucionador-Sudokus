# ----------------------------------------------------------------------------------------
#
# LISTADO DE CONTRADICCIONES
# --------------------------
# nº1: Celda vacía sin candidatos posibles
# nº2: Valor que falta en una fila/columna/bloque y no puede ir en ninguna de sus celdas
# nº3: Celda con un candidato que no puede ir en su fila/columna/bloque
#
# ----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
# FUNCIONES DE AYUDA
# ----------------------------------------------------------------------------------------
def valores_fila(sudoku, i):
    return set(sudoku[i]) - {0}

def valores_columna(sudoku, j):
    return set(sudoku[x][j] for x in range(9)) - {0}

def valores_bloque(sudoku, i, j):
    bi, bj = 3 * (i // 3), 3 * (j // 3)
    return set(sudoku[bi + x][bj + y] for x in range(3) for y in range(3)) - {0}


# ----------------------------------------------------------------------------------------
# VALIDACIÓN DEL SUDOKU
# ----------------------------------------------------------------------------------------
def comprobar_sudoku(sudoku):
    # Comprobamos dimensiones
    if len(sudoku) != 9 or any(len(fila) != 9 for fila in sudoku):
        return False

    # Comprobamos tipo y rango de valores
    for fila in sudoku:
        for val in fila:
            if not isinstance(val, int) or isinstance(val, bool) or val < 0 or val > 9:
                return False

    # Comprobamos filas y columnas
    for i in range(9):
        fila = [x for x in sudoku[i] if x != 0]
        columna = [sudoku[x][i] for x in range(9) if sudoku[x][i] != 0]
        if len(set(fila)) != len(fila) or len(set(columna)) != len(columna):
            return False

    # Comprobamos bloques 3x3
    for bi in range(0, 9, 3):
        for bj in range(0, 9, 3):
            bloque = [sudoku[bi + x][bj + y] for x in range(3) for y in range(3) if sudoku[bi + x][bj + y] != 0]
            if len(set(bloque)) != len(bloque):
                return False

    return True


# ----------------------------------------------------------------------------------------
# CONTROL DE CANDIDATOS
# ----------------------------------------------------------------------------------------
def calcular_candidatos(sudoku):
    '''Devuelve una matriz 9x9 de sets (candidatos por celda)'''
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
    '''Propaga la asignación recién hecha en celda = (i, j), eliminando su valor de los
       candidatos vecinos'''
    i, j = celda
    val = sudoku[i][j]
    if val == 0:
        return True

    # La celda asignada ya no tiene candidatos
    candidatos[i][j].clear()

    # Actualizamos fila y columna
    for x in range(9):
        if sudoku[i][x] == 0:
            candidatos[i][x].discard(val)
            if not candidatos[i][x]:
                return False  # Contradicción nº1
        if sudoku[x][j] == 0:
            candidatos[x][j].discard(val)
            if not candidatos[x][j]:
                return False  # Contradicción nº1

    # Actualizamos bloque
    bi, bj = 3 * (i // 3), 3 * (j // 3)
    for x in range(3):
        for y in range(3):
            if sudoku[bi + x][bj + y] == 0:
                candidatos[bi + x][bj + y].discard(val)
                if not candidatos[bi + x][bj + y]:
                    return False  # Contradicción nº1

    return True


# ----------------------------------------------------------------------------------------
# LÓGICA (NAKED SINGLES Y HIDDEN SINGLES)
# ----------------------------------------------------------------------------------------
def aplicar_logica(sudoku, candidatos):
    '''Naked singles + Hidden singles con sets. Devuelve False si hay contradicción'''
    progreso_total = True
    while progreso_total:
        progreso_total = False

        # Naked singles
        progreso_naked = True
        while progreso_naked:
            progreso_naked = False
            for i in range(9):
                for j in range(9):
                    if sudoku[i][j] == 0 and len(candidatos[i][j]) == 1:
                        val = next(iter(candidatos[i][j]))
                        sudoku[i][j] = val
                        if not actualizar_candidatos(sudoku, candidatos, (i, j)):
                            return False  # Contradicción nº1
                        progreso_naked = True

        # Hidden singles
        def colocar_hidden(celdas):
            # celdas: lista de (i, j) donde aplicar la lógica
            nonlocal progreso_total
            presentes = set(sudoku[i][j] for i, j in celdas) - {0}
            faltan = set(range(1, 10)) - presentes
            contador = {d: [] for d in faltan}

            for i, j in celdas:
                if sudoku[i][j] == 0:
                    if not candidatos[i][j].issubset(faltan):
                        return False  # Contradicción nº3
                    for d in candidatos[i][j]:
                        contador[d].append((i, j))

            for d, sitios in contador.items():
                if not sitios:
                    return False  # Contradicción nº2
                if len(sitios) == 1:
                    i, j = sitios[0]
                    sudoku[i][j] = d
                    if not actualizar_candidatos(sudoku, candidatos, (i, j)):
                        return False  # Contradicción nº1
                    progreso_total = True

            return True

        # Buscarmoshidden singles en filas y columnas
        for i in range(9):
            if not colocar_hidden([(i, j) for j in range(9)]) or not colocar_hidden([(j, i) for j in range(9)]):
                return False

        # Buscamos hidden singles en bloques
        for bi in range(0, 9, 3):
            for bj in range(0, 9, 3):
                celdas = [(bi + x, bj + y) for x in range(3) for y in range(3)]
                if not colocar_hidden(celdas):
                    return False

    return True


# ----------------------------------------------------------------------------------------
# BÚSQUEDA DE LA MEJOR CELDA (MRV)
# ----------------------------------------------------------------------------------------
def realizar_cambios(sudoku, candidatos):
    # Aplicamos lógica
    if not aplicar_logica(sudoku, candidatos):
        return False

    # Si ya está resuelto
    if all(not 0 in fila for fila in sudoku):
        return True

    # MRV: celda con menos candidatos
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

    # Proponemos un cambio y volvemos a llamar a la función recursiva
    i, j = mejor_celda
    for val in sorted(candidatos[i][j]):
        copia_sudoku = [fila[:] for fila in sudoku]
        copia_candidatos = [[s.copy() for s in fila] for fila in candidatos]
        copia_sudoku[i][j] = val

        if not actualizar_candidatos(copia_sudoku, copia_candidatos, (i, j)):
            continue  # Rama muerta, probamos el siguiente val

        if realizar_cambios(copia_sudoku, copia_candidatos):
            for x in range(9):
                sudoku[x][:] = copia_sudoku[x][:]
                for y in range(9):
                    candidatos[x][y] = copia_candidatos[x][y]
            return True

    return False


# ----------------------------------------------------------------------------------------
# API PRINCIPAL
# ----------------------------------------------------------------------------------------
def imprimir_sudoku_como_lista(sudoku):
    print("Sudoku = [")
    for fila in sudoku:
        print(str(fila) + ",")
    print("]")

def solucionar_sudoku_avanzado(sudoku):
    '''
    Returns
    -------
        0: Sudoku inválido
        1: Sudoku sin solución
        2: Error. Algo no fue bien
        3: Solución válida encontrada
    '''
    # Comprobamos validez del sudoku propuesto
    if not comprobar_sudoku(sudoku):
        return 0

    # Calculamos los candidatos de todas las celdas
    candidatos = calcular_candidatos(sudoku)
    if candidatos is None:
        return 1

    if not realizar_cambios(sudoku, candidatos):
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

