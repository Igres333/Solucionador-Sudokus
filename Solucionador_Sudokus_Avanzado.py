import time

# %% --------------------------------------------------------------------------
#
# LISTADO DE CONTRADICCIONES
# --------------------------
# nº1: Celda vacía sin candidatos
# nº2: Valor faltante en fila/columna/bloque que no puede ir en ninguna de sus celdas
# nº3: Celda con un candidato que no puede ir en su fila/columna/bloque
#
#
# %% --------------------------------------------------------------------------
# FUNCIONES DE AYUDA
# -----------------------------------------------------------------------------
def valores_fila(sudoku, i):
    return set(sudoku[i]) - {0}

def valores_columna(sudoku, j):
    return set(sudoku[x][j] for x in range(9)) - {0}

def valores_bloque(sudoku, i, j):
    bi, bj = 3 * (i // 3), 3 * (j // 3)
    return set(sudoku[bi + x][bj + y] for x in range(3) for y in range(3)) - {0}


# %% --------------------------------------------------------------------------
# VALIDACIÓN DEL SUDOKU
# -----------------------------------------------------------------------------
def comprobar_sudoku(sudoku):
    # Comprobar dimensiones
    if len(sudoku) != 9 or any(len(fila) != 9 for fila in sudoku):
        return False
    
    # Comprobar tipo y rango valores
    for fila in sudoku:
        for val in fila:
            if isinstance(val, bool) or not isinstance(val, int) or val < 0 or val > 9:
                return False
    
    # Comprobar filas y columnas
    for i in range(9):
        # Filas
        fila = [x for x in sudoku[i] if x != 0]
        if len(fila) != len(set(fila)):
            return False
        # Columnas
        columna = [sudoku[x][i] for x in range(9) if sudoku[x][i] != 0]
        if len(columna) != len(set(columna)):
            return False
    
    # Comprobar bloques 3x3
    for bi in range(0, 9, 3):
        for bj in range(0, 9, 3):
            bloque = [sudoku[bi + x][bj + y] for x in range(3) for y in range(3)
                      if sudoku[bi + x][bj + y] != 0]
            if len(bloque) != len(set(bloque)):
                return False
    
    return True


# %% --------------------------------------------------------------------------
# CONTROL DE CANDIDATOS
# -----------------------------------------------------------------------------
def calcular_candidatos(sudoku):
    '''Devuelve matriz 9x9 de sets (candidatos por celda).'''
    candidatos = [[set() for _ in range(9)] for _ in range(9)]
    for i in range(9):
        for j in range(9):
            if sudoku[i][j] == 0:
                usados = valores_fila(sudoku, i) | valores_columna(sudoku, j) | \
                         valores_bloque(sudoku, i, j)
                candidatos[i][j] = set(range(1, 10)) - usados
                if not candidatos[i][j]:
                    return None  # Contradicción nº1
    return candidatos

def actualizar_candidatos(sudoku, celda, candidatos):
    '''Propaga la asignación recién hecha en (i, j), eliminando su valor de los
       candidatos vecinos.'''
    i, j = celda
    val = sudoku[i][j]
    if val == 0:
        return True
    
    # La celda asignada ya no tiene candidatos
    candidatos[i][j].clear()
    
    # Actualiza fila y columna
    for x in range(9):
        # Fila
        if sudoku[i][x] == 0:
            candidatos[i][x].discard(val)
            if not candidatos[i][x]:
                return False  # Contradicción nº1
        # Columna
        if sudoku[x][j] == 0:
            candidatos[x][j].discard(val)
            if not candidatos[x][j]:
                return False  # Contradicción nº1
    
    # Actualiza bloque
    bi, bj = 3 * (i // 3), 3 * (j // 3)
    for x in range(3):
        for y in range(3):
            if sudoku[bi + x][bj + y] == 0:
                candidatos[bi + x][bj + y].discard(val)
                if not candidatos[bi + x][bj + y]:
                    return False  # Contradicción nº1
    
    return True

# %% --------------------------------------------------------------------------
# LÓGICA (NAKED SINGLES Y HIDDEN SINGLES)
# -----------------------------------------------------------------------------
def aplicar_logica(sudoku, candidatos):
    '''Naked singles + Hidden singles con sets. Devuelve False si hay contradicción.'''
    progreso = True
    while progreso:
        progreso = False
        
        # Naked singles
        hubo = True
        while hubo:
            hubo = False
            for i in range(9):
                for j in range(9):
                    if sudoku[i][j] == 0 and len(candidatos[i][j]) == 1:
                        val = next(iter(candidatos[i][j]))
                        sudoku[i][j] = val
                        if not actualizar_candidatos(sudoku, (i, j), candidatos):
                            return False  # Contradicción nº1
                        progreso = hubo = True
        
        # Hidden singles (en filas, columnas y bloques)
        def colocar_hidden(celdas):
            # celdas: lista de (i, j) donde aplicaremos la lógica
            nonlocal progreso
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
                    if not actualizar_candidatos(sudoku, (i, j), candidatos):
                        return False  # Contradicción nº1
                    progreso = True
            return True
        
        # Filas y columnas
        for i in range(9):
            if not colocar_hidden([(i, j) for j in range(9)]):
                return False
            if not colocar_hidden([(j, i) for j in range(9)]):
                return False
        
        # Bloques
        for bi in range(0, 9, 3):
            for bj in range(0, 9, 3):
                celdas = [(bi + x, bj + y) for x in range(3) for y in range(3)]
                if not colocar_hidden(celdas):
                    return False
        
    return True


# %% --------------------------------------------------------------------------
# BÚSQUEDA DE LA MEJOR CELDA (MRV)
# -----------------------------------------------------------------------------
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
        if not actualizar_candidatos(copia_sudoku, (i, j), copia_candidatos):
            continue  # Rama muerta, probamos el siguiente val
        if realizar_cambios(copia_sudoku, copia_candidatos):
            for x in range(9):
                sudoku[x][:] = copia_sudoku[x][:]
                for y in range(9):
                    candidatos[x][y] = copia_candidatos[x][y]
            return True
    
    return False
        

# %% --------------------------------------------------------------------------
# API PRINCIPAL
# -----------------------------------------------------------------------------
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


# %% --------------------------------------------------------------------------
# EJEMPLO DE USO
# -----------------------------------------------------------------------------
if __name__ == '__main__':
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
        t_inicial = time.perf_counter()
        idx = solucionar_sudoku_avanzado(sudoku)
        t_final = time.perf_counter()
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
            print(f"Tiempo = {(t_final - t_inicial):.6}s")
        print("\n")


