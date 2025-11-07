import tkinter as tk
from tkinter import messagebox
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import io
from tkinter import filedialog
from PIL import Image
import win32clipboard
import sys
import os
import re
from tkinter import ttk


def fit_T1(x, SI, k, T1):
    return np.abs(SI * (1 - (1 - k) * np.exp(-x / T1)))

def fit_T2(x, SI0, SI, T2):
    return SI0 * np.exp(-x / T2) + SI

class FitApp:
    
    def __init__(self, root):
        self.root = root
        self.root.title("T1 und T2 Fit")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        canvas = tk.Canvas(root, borderwidth=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, borderwidth=0, highlightthickness=0, relief="flat")
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        self.scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="n")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Menubar
        menubar = tk.Menu(root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="New", command=self.refresh)
        filemenu.add_command(label="Save", command=self.save_plot)
        filemenu.add_command(label="Copy", command=self.copy_plot)
        menubar.add_cascade(label="Option", menu=filemenu)
        root.config(menu=menubar)

        # Input container for centering
        input_container = tk.Frame(self.scroll_frame)
        input_container.grid(row=0, column=0, pady=10, padx=(38, 38))

        tk.Label(input_container, text="Compound").grid(row=0, column=0, pady=5)
        self.name_entry = tk.Entry(input_container, width=35)
        self.name_entry.grid(row=0, column=1, pady=5)

        tk.Label(input_container, text="Concentration").grid(row=1, column=0, pady=5)
        self.conc_entry = tk.Entry(input_container, width=35)
        self.conc_entry.grid(row=1, column=1, pady=5)

        self.var_T1 = tk.BooleanVar()
        self.var_T2 = tk.BooleanVar()
        tk.Checkbutton(input_container, text="T1", variable=self.var_T1).grid(row=2, column=0, pady=5)
        tk.Checkbutton(input_container, text="T2", variable=self.var_T2).grid(row=2, column=1, pady=5)

        tk.Label(input_container, text="Add Data (First Column = Time in s, Second Column Magnitude)").grid(row=3, column=0, columnspan=2, pady=5)
        

        self.coord_label = tk.Label(self.scroll_frame, text="X: ---, Y: ---", font=("Arial", 10))
        self.coord_label.grid(row=7, column=0, pady=(0, 10))

        self.data_text = tk.Text(input_container, width=55, height=15)
        self.data_text.grid(row=4, column=0, columnspan=2, pady=5)
        self.data_text.tag_configure("bad", background="red")
        self.data_text.bind("<Enter>", lambda e: self.data_text.bind_all("<MouseWheel>", lambda event: self.data_text.yview_scroll(int(-1 * (event.delta / 120)), "units")))
        self.data_text.bind("<Leave>", lambda e: self.data_text.unbind_all("<MouseWheel>"))

        tk.Button(input_container, text="Solve", command=self.calculate_fit).grid(row= 5, column=0, columnspan=2, pady=5)

        self.result_entry = ttk.Entry(input_container, width=30)
        self.result_entry.insert(0, "...")
        self.result_entry.config(state="readonly")
        self.result_entry.grid(row=6, column=0, columnspan=2, pady=5)

        self.canvas_frame = tk.Frame(self.scroll_frame)
        self.canvas_frame.grid(row=1, column=0, sticky="nsew", padx=(38, 38), pady=10)
        

        self.scroll_frame.grid_rowconfigure(1, weight=1)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self.selected_index = None
        self.removed_indices = set()


    def on_close(self):
        plt.close('all') 
        self.root.quit()  
        self.root.destroy()  
        sys.exit()  

    
    def save_plot(self):
        try:
            filetypes = [("PNG-Bild", "*.png"), ("Alle Dateien", "*.*")]
            filename = filedialog.asksaveasfilename(defaultextension=".png", filetypes=filetypes, title="Image saved")
            if filename:
                self.canvas.figure.savefig(filename, bbox_inches='tight')
                messagebox.showinfo("Saved", f"Image saved in:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error during Saving", str(e))
            self.canvas.figure.savefig(filename, bbox_inches='tight')
            messagebox.showinfo("Saved", f"Image saved as {filename}")
        except Exception as e:
            messagebox.showerror("Error during Saving", str(e))
    
    def copy_plot(self):
        try:
            # Save image as png
            buf = io.BytesIO()
            self.canvas.figure.savefig(buf, format='png')
            buf.seek(0)
            image = Image.open(buf)

            # convert in DIB (Device Independent Bitmap) 
            output = io.BytesIO()
            image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]  # remove BMP header

            # copy
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()

            messagebox.showinfo("Copied", "Image copied.")
        except Exception as e:
            messagebox.showerror("Error during copy", str(e))




    def refresh(self):
        self.name_entry.delete(0, tk.END)
        self.conc_entry.delete(0, tk.END)
        self.data_text.delete("1.0", tk.END)
        self.var_T1.set(False)
        self.var_T2.set(False)
        self.selected_index = None
        self.result_entry.config(state="normal")
        self.result_entry.delete(0, tk.END)
        self.result_entry.config(state="readonly")
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

    def calculate_fit(self):
        try:
            self.selected_index = None
            self.data_text.tag_remove("bad", "1.0", tk.END)
            raw = self.data_text.get("1.0", tk.END).strip()
            comma_decimal = False
            lines = raw.splitlines()
            for line in lines:
                parts = line.split("\t")
                if len(parts) >= 2:
                    if "," in parts[0] or "," in parts[1]:
                        comma_decimal = True
                        break

            raw_converted = raw.replace(",", ".") if comma_decimal else raw
            raw_cleaned = re.sub(r"[^\d\.\-\t\n]", "", raw_converted)
            df = pd.read_csv(io.StringIO(raw_cleaned), sep="\t", header=None)

            original_lines = len(raw.splitlines())

            df = df.dropna(how="all")

            y_raw = df.iloc[:, 1:].replace(0, np.nan)
            y_mean = y_raw.mean(axis=1, skipna=True)
            self.original_indices = np.arange(len(df))
            valid_mask = ~np.isnan(y_mean)
            self.valid_indices = self.original_indices[valid_mask]

            valid_mask = ~np.isnan(y_mean)
            x = df.iloc[:, 0].values[valid_mask]
            y = y_mean.values[valid_mask]

            removed = sum(np.isnan(y))
            if removed > 0:
                messagebox.showinfo("Data Cleaning", f"{removed} rows with only 0 or NaN values were excluded from curve fitting.")

            valid_y = np.where(np.isnan(y), np.inf, y)
            T10 = - (1 / np.log(1 / 2)) * x[np.argmin(valid_y)]

            if self.var_T1.get():
                popt, pcov = curve_fit(fit_T1, x, y, p0=[y.max(), -1, T10])
                std_t = np.sqrt(np.diag(pcov)[2])/1000
                fitted = fit_T1(np.linspace(0, max(x),10000), *popt)
                self.result_entry.config(state="normal")
                self.result_entry.delete(0, tk.END)
                value = f"{popt[2]/1000:.2f}"
                if comma_decimal:
                    value = value.replace(".", ",")
                self.result_entry.insert(0, f"T1 = {value} \u00B1 {std_t: 0.3f} s") 
                self.result_entry.config(state="readonly")

                label = f"T1={popt[2]/1000:.2f} s"
            elif self.var_T2.get():
                popt, pcov = curve_fit(fit_T2, x, y, p0=[-1, y[0], y[-1]])
                std_t = np.sqrt(np.diag(pcov)[2])/1000
                fitted = fit_T2(np.linspace(0, max(x),10000), *popt)
                self.result_entry.config(state="normal")
                self.result_entry.delete(0, tk.END)
                value = f"{popt[2]/1000:.2f}"
                if comma_decimal:
                    value = value.replace(".", ",")
                self.result_entry.insert(0, f"T2 = {value} \u00B1 {std_t: 0.3f} s")  
                self.result_entry.config(state="readonly")

                label = f"T2={popt[2]/1000:.2f} s"
            else:
                messagebox.showwarning("No Selection", "Please select T1 or T2.")
                return
            
            std_mean = np.std(y_mean)

            self.plot_data(x, y, fitted, label, std_mean)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def plot_data(self, x, y, fitted, label, std_mean):
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(5, 4)) 
        
        self.canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Datapoint colour
        self.point_colors = ['blue'] * len(x)
        self.points = ax.scatter(x, y, c=self.point_colors, s =10, picker=True)

        # fit
        ax.plot(np.linspace(0, max(x),10000), fitted, 'r-', label=label)
        title = f"{self.name_entry.get()} \n [c] = {self.conc_entry.get()}"
        ax.set_title(title)
        ax.set_xlabel("τ in ms")
        ax.set_ylabel("Magnitude")
        ax.legend()
        fig.tight_layout()
        fig.canvas.mpl_connect("motion_notify_event", self.on_motion)
        fig.canvas.mpl_connect("button_press_event", lambda event: self.on_click(event, x, y, self.valid_indices))
        self.canvas.draw()

    def on_motion(self, event):
        if event.inaxes:
            x_coord = event.xdata
            y_coord = event.ydata
            self.coord_label.config(text=f"X: {x_coord:.2f}, Y: {y_coord:.2f}")
        else:
            self.coord_label.config(text="X: ---, Y: ---")
    
    def on_click(self, event, x, y, original_indices):
        if event.inaxes:
            distances = np.hypot(x - event.xdata, y - event.ydata)
            idx = np.argmin(distances)
            line_number = original_indices[idx]

            start = f"{line_number+1}.0"
            end = f"{line_number+1}.end"
            self.data_text.tag_remove("bad", "1.0", tk.END)
            self.data_text.tag_add("bad", start, end)


            if self.selected_index is not None:
                self.point_colors[self.selected_index] = 'blue'
            self.point_colors[idx] = 'red'
            self.selected_index = idx
            self.points.set_color(self.point_colors)
            self.canvas.draw()


if __name__ == "__main__":
    root = tk.Tk()

    style = ttk.Style()
    style.theme_use("default")  

    root.geometry("600x567")

    app = FitApp(root)
    root.mainloop()


