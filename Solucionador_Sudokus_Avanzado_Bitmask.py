# ----------------------------------------------------------------------------------------
#
# VERSIÓN CON BITMASKS
# --------------------
# Los candidatos de cada celda se guardan en un entero de 9 bits en lugar de un set:
# el bit (d - 1) está activo si el dígito d es candidato. Por ejemplo, 0b000010101
# representa los candidatos {1, 3, 5}.
#
#   Añadir d:       mask |= BIT[d]
#   Quitar d:       mask &= ~BIT[d]
#   ¿Es candidato?: mask & BIT[d]
#   Nº candidatos:  mask.bit_count()        (Python 3.10+)
#   Único dígito:   mask.bit_length()       (si solo hay un bit activo)
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
# CONSTANTES DE BITS
# ----------------------------------------------------------------------------------------
TODOS = 0b111111111                          # Los 9 dígitos son candidatos
BIT = [0] + [1 << (d - 1) for d in range(1, 10)]  # BIT[d] = máscara del dígito d (BIT[0] = 0)


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
    (i, j): tuple({c for u in UNIDADES if (i, j) in u for c in u} - {(i, j)})
    for i in range(9) for j in range(9)
}


# ----------------------------------------------------------------------------------------
# FUNCIONES DE AYUDA
# ----------------------------------------------------------------------------------------
def digitos(mask):
    """Devuelve la lista de dígitos de la máscara, de menor a mayor"""
    resultado = []
    while mask:
        bajo = mask & -mask              # Bit activo más bajo
        resultado.append(bajo.bit_length())
        mask ^= bajo
    return resultado

def mascara_unidad(sudoku, celdas):
    """Devuelve la máscara de los valores ya colocados en una unidad"""
    mask = 0
    for i, j in celdas:
        mask |= BIT[sudoku[i][j]]
    return mask


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
    """Devuelve una matriz 9x9 de máscaras con los candidatos de cada celda (0 en las
       celdas ya colocadas), o None si alguna celda vacía se queda sin candidatos"""
    usados_fila    = [mascara_unidad(sudoku, u) for u in FILAS]
    usados_columna = [mascara_unidad(sudoku, u) for u in COLUMNAS]
    usados_bloque  = [mascara_unidad(sudoku, u) for u in BLOQUES]

    candidatos = [[0] * 9 for _ in range(9)]
    for i in range(9):
        for j in range(9):
            if sudoku[i][j] == 0:
                usados = usados_fila[i] | usados_columna[j] | usados_bloque[3 * (i // 3) + j // 3]
                candidatos[i][j] = TODOS & ~usados
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
    candidatos[i][j] = 0

    quitar = ~BIT[val]
    for x, y in VECINOS[celda]:
        if sudoku[x][y] == 0:
            candidatos[x][y] &= quitar
            if not candidatos[x][y]:
                return False  # Contradicción nº1

    return True


# ----------------------------------------------------------------------------------------
# LÓGICA (NAKED SINGLES Y HIDDEN SINGLES)
# ----------------------------------------------------------------------------------------
def colocar_hidden(sudoku, candidatos, celdas):
    """Busca hidden singles en una unidad (lista de celdas (i, j)) y los coloca.
       Devuelve (ok, progreso): ok=False si hay contradicción, progreso=True si se colocó algo"""
    # Con dos máscaras sabemos qué dígitos aparecen como candidato al menos una vez
    # y cuáles al menos dos veces en la unidad, sin contar celda a celda
    una_vez = dos_veces = 0
    for i, j in celdas:
        if sudoku[i][j] == 0:
            m = candidatos[i][j]
            dos_veces |= una_vez & m
            una_vez |= m

    faltan = TODOS & ~mascara_unidad(sudoku, celdas)
    if faltan & ~una_vez:
        return False, False  # Contradicción nº2

    progreso = False
    for d in digitos(una_vez & ~dos_veces):  # Dígitos que solo caben en una celda
        # Buscamos esa celda. Si ya no está libre es que otro hidden single de esta
        # misma unidad la ha ocupado antes
        for i, j in celdas:
            if sudoku[i][j] == 0 and candidatos[i][j] & BIT[d]:
                break
        else:
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

        # Naked singles: celdas con un único candidato (un solo bit activo)
        progreso_naked = True
        while progreso_naked:
            progreso_naked = False
            for i in range(9):
                for j in range(9):
                    m = candidatos[i][j]
                    if sudoku[i][j] == 0 and m & (m - 1) == 0:
                        sudoku[i][j] = m.bit_length()
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
            if sudoku[i][j] == 0:
                n = candidatos[i][j].bit_count()
                if n < min_candidatos:
                    min_candidatos = n
                    mejor_celda = (i, j)
                    if n == 2:
                        break
        if min_candidatos == 2:
            break

    if mejor_celda is None:
        return False

    # Probamos cada candidato de la celda elegida (de menor a mayor) sobre una copia y
    # seguimos recursivamente. Copiar los candidatos es copiar listas de enteros
    i, j = mejor_celda
    for val in digitos(candidatos[i][j]):
        copia_sudoku = [fila[:] for fila in sudoku]
        copia_candidatos = [fila[:] for fila in candidatos]
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

