import tkinter as tk
from tkinter import messagebox
from Solucionador_Sudokus_Avanzado import solucionar_sudoku_avanzado


class SudokuGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku Solver")

        self.entries = [[None for _ in range(9)] for _ in range(9)]
        self.create_grid()
        self.create_solve_button()

    def create_grid(self):
        for row in range(9):
            for col in range(9):
                entry = tk.Entry(self.root, width=2, font=('Arial', 18), justify='center')
                entry.grid(row=row, column=col, padx=1, pady=1)

                # Grosor de los bordes para distinguir regiones
                if row % 3 == 0 and row != 0:
                    entry.grid(row=row, column=col, pady=(5,1))
                if col % 3 == 0 and col != 0:
                    entry.grid(row=row, column=col, padx=(5,1))

                self.entries[row][col] = entry

    def create_solve_button(self):
        # Botón para resolver
        solve_button = tk.Button(self.root, text="Resolver Sudoku", command=self.solve_sudoku)
        solve_button.grid(row=9, column=0, columnspan=9, pady=10)
        
        # Botón para reiniciar
        reset_button = tk.Button(self.root, text="Reiniciar", command=self.reset_board)
        reset_button.grid(row=10, column=0, columnspan=9, pady=(0, 10))

    def get_board(self):
        board = []
        for row in range(9):
            current_row = []
            for col in range(9):
                val = self.entries[row][col].get()
                if val == "":
                    current_row.append(0)
                else:
                    try:
                        current_row.append(int(val))
                    except ValueError:
                        messagebox.showerror("Entrada inválida", f"Celda ({row+1},{col+1}) tiene un valor no numérico.")
                        return None
            board.append(current_row)
        return board

    def display_solution(self, board):
        for row in range(9):
            for col in range(9):
                self.entries[row][col].delete(0, tk.END)
                if board[row][col] != 0:
                    self.entries[row][col].insert(0, str(board[row][col]))

    def solve_sudoku(self):
        board = self.get_board()
        if board is None:
            return

        # Llama a tu función de resolución aquí
        if solucionar_sudoku_avanzado(board) == 3:
            self.display_solution(board)
        else:
            messagebox.showerror("Sin solución", "El Sudoku ingresado no tiene solución.")
            
    def reset_board(self):
        for row in range(9):
            for col in range(9):
                self.entries[row][col].delete(0, tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuGUI(root)
    root.mainloop()