# 🧪 T1T2Calculator

A Python-based tool for calculating and visualizing **T₁** and **T₂ relaxation times** from NMR data.  
It uses curve fitting according to the **Rohrer equation** (ISSN: 0020-9996/05/4011-0715) and provides a graphical user interface built with **Tkinter**.

---

## ⚙️ Features

- Calculate **T₁** or **T₂** from experimental measurements  
- Curve fitting based on:
  - **T₁:**  
    $SI(TI) = |SI_{\inf} [1 - (1 - k) \cdot e^{-TI/T_1}]|$
  - **T₂:**  
    $SI(TE) = SI_0 \cdot e^{-TE/T_2} + SI_{noise}$
- Input data directly via text box (first column = time in s, second = magnitude)
- Automatic cleaning of invalid or zero data
- Interactive plot:
  - Click on a data point → highlights the corresponding line in the data table  
  - Mouse coordinates displayed in real time
- Output includes fitted T₁/T₂ values with standard deviation
- Save or copy plots directly from the interface



This application was developed **for Windows**.


