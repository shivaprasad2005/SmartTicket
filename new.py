import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import DateEntry
from PIL import Image, ImageTk
import sqlite3
import matplotlib.pyplot as plt
from fpdf import FPDF
import csv
import qrcode
import os
from datetime import datetime, timedelta

# Initialize database
conn = sqlite3.connect('book_ticket.db')
cursor = conn.cursor()

# Create tables if not exists
cursor.execute('''CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    passenger_name TEXT,
    age INTEGER,
    gender TEXT,
    source TEXT,
    destination TEXT,
    journey_date TEXT,
    return_date TEXT,
    fare REAL
)''')
conn.commit()

# Function to generate PDF ticket with QR code
def generate_ticket_pdf(ticket_id):
    cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    ticket = cursor.fetchone()

    if ticket:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", style='B', size=16)
        pdf.cell(200, 10, txt="Smart Ticketing System", ln=True, align='C')
        pdf.ln(5)

        pdf.set_line_width(0.5)
        pdf.rect(10, 30, 190, 80)

        pdf.set_font("Arial", size=12)
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Ticket ID: {ticket[0]}", ln=True)
        pdf.cell(200, 10, txt=f"Passenger Name: {ticket[1]}", ln=True)
        pdf.cell(200, 10, txt=f"Age: {ticket[2]}", ln=True)
        pdf.cell(200, 10, txt=f"Gender: {ticket[3]}", ln=True)
        pdf.cell(200, 10, txt=f"Source: {ticket[4]}", ln=True)
        pdf.cell(200, 10, txt=f"Destination: {ticket[5]}", ln=True)
        pdf.cell(200, 10, txt=f"Journey Date: {ticket[6]}", ln=True)
        pdf.cell(200, 10, txt=f"Return Date: {ticket[7]}", ln=True)
        pdf.cell(200, 10, txt=f"Fare: {ticket[8]} INR", ln=True)

        qr_data = f"Ticket ID: {ticket[0]}\nName: {ticket[1]}\nFrom: {ticket[4]} To: {ticket[5]}\nJourney: {ticket[6]}\nReturn: {ticket[7]}\nFare: {ticket[8]} INR"
        qr = qrcode.make(qr_data)
        qr_file = f"ticket_{ticket_id}.png"
        qr.save(qr_file)

        pdf.image(qr_file, x=80, y=120, w=50, h=50)
        pdf_output = f"Ticket_{ticket_id}.pdf"
        pdf.output(pdf_output)
        messagebox.showinfo("Success", f"Ticket PDF generated: {pdf_output}")
        
        try: os.remove(qr_file)
        except: pass
    else:
        messagebox.showerror("Error", "Ticket not found!")

def print_ticket():
    ticket_id = simpledialog.askinteger("Ticket ID", "Enter Ticket ID to print:")
    if ticket_id: generate_ticket_pdf(ticket_id)

def update_return_date_min(*args):
    try:
        journey_date = datetime.strptime(journey_date_var.get(), "%Y-%m-%d")
        return_calendar.configure(mindate=journey_date + timedelta(days=1))
    except ValueError: pass

def add_ticket():
    name = name_entry.get()
    age = age_entry.get()
    gender = gender_combobox.get()
    source = source_combobox.get()
    destination = destination_combobox.get()
    journey_date = journey_date_var.get()
    return_date = return_date_var.get()
    fare = fare_entry.get()

    if not (name and age and gender and source and destination and journey_date and return_date and fare):
        messagebox.showerror("Input Error", "All fields are required!")
        return

    try:
        journey_date_obj = datetime.strptime(journey_date, "%Y-%m-%d")
        return_date_obj = datetime.strptime(return_date, "%Y-%m-%d")
        if return_date_obj <= journey_date_obj:
            raise ValueError("Return date must be after journey date")
    except ValueError as e:
        messagebox.showerror("Date Error", str(e))
        return

    try:
        age = int(age)
        fare = float(fare)
        if age < 0 or fare < 0:
            raise ValueError("Age and Fare must be non-negative.")
    except ValueError as e:
        messagebox.showerror("Input Error", str(e))
        return

    try:
        cursor.execute("INSERT INTO tickets (passenger_name, age, gender, source, destination, journey_date, return_date, fare) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (name, age, gender, source, destination, journey_date, return_date, fare))
        conn.commit()
        messagebox.showinfo("Success", "Ticket Booked successfully!")
        clear_fields()
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"An error occurred: {e}")

def clear_fields():
    name_entry.delete(0, tk.END)
    age_entry.delete(0, tk.END)
    gender_combobox.set('')
    source_combobox.set('')
    destination_combobox.set('')
    journey_date_var.set('')
    return_date_var.set('')
    fare_entry.delete(0, tk.END)
    return_calendar.configure(mindate=datetime.now() + timedelta(days=1))

def show_analytics():
    cursor.execute("SELECT source, destination, COUNT(*), SUM(fare) FROM tickets GROUP BY source, destination")
    data = cursor.fetchall()

    if not data:
        messagebox.showinfo("No Data", "No tickets sold yet.")
        return

    fig, ax = plt.subplots(2, 2, figsize=(14, 10))

    routes = [f"{row[0]} -> {row[1]}" for row in data]
    passenger_counts = [row[2] for row in data]
    earnings = [row[3] for row in data]

    ax1 = ax[0, 0]
    ax1.bar(routes, passenger_counts, color='skyblue', label='Passengers')
    ax1.set_xlabel("Routes")
    ax1.set_ylabel("Number of Passengers")
    ax1.set_title("Passengers per Route")
    ax1.tick_params(axis='x', rotation=45)

    ax2 = ax1.twinx()
    ax2.plot(routes, earnings, color='orange', marker='o', label='Earnings')
    ax2.set_ylabel("Earnings (INR)")

    cursor.execute("SELECT gender, COUNT(*) FROM tickets GROUP BY gender")
    gender_data = cursor.fetchall()

    if gender_data:
        genders = [row[0] for row in gender_data]
        gender_counts = [row[1] for row in gender_data]
        ax[0, 1].pie(gender_counts, labels=genders, autopct='%1.1f%%', startangle=90, 
                    colors=['lightcoral', 'lightskyblue', 'lightgreen'])
        ax[0, 1].set_title("Gender Distribution")

    cursor.execute("SELECT age FROM tickets")
    ages = [row[0] for row in cursor.fetchall()]
    
    if ages:
        ax[1, 0].hist(ages, bins=[0, 12, 18, 30, 50, 100], edgecolor="black", alpha=0.7, color='teal')
        ax[1, 0].set_xticks([6, 15, 24, 40, 75])
        ax[1, 0].set_xticklabels(["0-12", "13-18", "19-30", "31-50", "51+"])
        ax[1, 0].set_xlabel("Age Group")
        ax[1, 0].set_ylabel("Number of Passengers")
        ax[1, 0].set_title("Age Group Distribution")

    sorted_data = sorted(data, key=lambda x: x[2], reverse=True)[:3]
    if sorted_data:
        top_routes = [f"{row[0]} -> {row[1]}" for row in sorted_data]
        top_counts = [row[2] for row in sorted_data]
        ax[1, 1].barh(top_routes, top_counts, color="goldenrod")
        ax[1, 1].set_xlabel("Passenger Count")
        ax[1, 1].set_title("Top 3 Most Popular Routes")

    plt.tight_layout()
    plt.show()

def refresh_history(tree):
    for item in tree.get_children(): tree.delete(item)
    cursor.execute("SELECT * FROM tickets")
    for row in cursor.fetchall():
        tree.insert("", tk.END, values=row)

def show_travel_history():
    cursor.execute("SELECT * FROM tickets")
    data = cursor.fetchall()

    if not data:
        messagebox.showinfo("No Data", "No tickets sold yet.")
        return

    history_window = tk.Toplevel(window)
    history_window.title("Travel History")
    history_window.geometry("1000x500")

    frame = ttk.Frame(history_window)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    v_scrollbar = ttk.Scrollbar(frame, orient="vertical")
    h_scrollbar = ttk.Scrollbar(frame, orient="horizontal")
    
    columns = ("ID", "Name", "Age", "Gender", "Source", "Destination", "Journey Date", "Return Date", "Fare")
    tree = ttk.Treeview(frame, columns=columns, show="headings", 
                       yscrollcommand=v_scrollbar.set,
                       xscrollcommand=h_scrollbar.set)
    
    v_scrollbar.config(command=tree.yview)
    h_scrollbar.config(command=tree.xview)
    
    v_scrollbar.pack(side="right", fill="y")
    h_scrollbar.pack(side="bottom", fill="x")
    
    for col in columns:
        tree.heading(col, text=col)
        if col == "ID": tree.column(col, width=50, anchor="center")
        elif col == "Age": tree.column(col, width=50, anchor="center")
        elif col == "Gender": tree.column(col, width=80, anchor="center")
        elif col == "Fare": tree.column(col, width=80, anchor="center")
        else: tree.column(col, width=120)
    
    for row in data: tree.insert("", tk.END, values=row)
    tree.pack(fill=tk.BOTH, expand=True)
    
    btn_frame = ttk.Frame(history_window)
    btn_frame.pack(fill="x", padx=10, pady=10)
    
    ttk.Button(btn_frame, text="Refresh", command=lambda: refresh_history(tree)).pack(side="left", padx=5)
    
    def print_selected():
        if selected := tree.selection():
            generate_ticket_pdf(tree.item(selected[0])['values'][0])
        else: messagebox.showinfo("No Selection", "Please select a ticket to print.")
    
    ttk.Button(btn_frame, text="Print Selected Ticket", command=print_selected).pack(side="left", padx=5)
    
    def export_selected():
        if not (selected := tree.selection()):
            messagebox.showinfo("No Selection", "Please select tickets to export.")
            return
        
        selected_data = [tree.item(item)['values'] for item in selected]
        with open("Selected_Tickets.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Passenger Name", "Age", "Gender", "Source", "Destination", 
                            "Journey Date", "Return Date", "Fare"])
            writer.writerows(selected_data)
        messagebox.showinfo("Success", "Selected tickets exported to Selected_Tickets.csv")
    
    ttk.Button(btn_frame, text="Export Selected", command=export_selected).pack(side="left", padx=5)

def search_ticket():
    search_query = simpledialog.askstring("Search Ticket", "Enter Passenger Name or Ticket ID:")
    if not search_query: return

    try:
        cursor.execute("SELECT * FROM tickets WHERE id = ?", (int(search_query),))
    except ValueError:
        cursor.execute("SELECT * FROM tickets WHERE passenger_name LIKE ?", (f"%{search_query}%",))
        
    if results := cursor.fetchall():
        result_text = "\n".join([f"Ticket ID: {row[0]}\nName: {row[1]}\nSource: {row[4]}\nDestination: {row[5]}\nJourney: {row[6]}\nReturn: {row[7]}" for row in results])
        messagebox.showinfo("Search Results", result_text)
    else:
        messagebox.showerror("Not Found", "No matching tickets found.")

def cancel_ticket():
    if ticket_id := simpledialog.askinteger("Cancel Ticket", "Enter Ticket ID to cancel:"):
        cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        if cursor.fetchone():
            cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
            conn.commit()
            messagebox.showinfo("Success", f"Ticket ID {ticket_id} has been canceled.")
        else:
            messagebox.showerror("Error", "Ticket ID not found!")

def export_to_csv():
    cursor.execute("SELECT * FROM tickets")
    if data := cursor.fetchall():
        with open("Travel_History.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Passenger Name", "Age", "Gender", "Source", "Destination", 
                            "Journey Date", "Return Date", "Fare"])
            writer.writerows(data)
        messagebox.showinfo("Success", "Travel history exported to Travel_History.csv")
    else:
        messagebox.showinfo("No Data", "No tickets available to export.")

# Main application window
window = tk.Tk()
window.title("Smart Ticket Vending System with Data Analytics")
window.geometry("1300x700")

try:
    background_img = Image.open("C:\\Users\\kisho\\Desktop\\project\\WhatsApp Image 2025-05-09 at 00.44.49_55ae71ca.jpg")
    background_photo = ImageTk.PhotoImage(background_img.resize((1300, 700)))
    background_label = tk.Label(window, image=background_photo)
    background_label.place(x=0, y=0, relwidth=1, relheight=1)
except Exception as e:
    print(f"Background image error: {e}")
    background_label = tk.Label(window, bg="#f0f8ff")
    background_label.place(x=0, y=0, relwidth=1, relheight=1)

frame = ttk.Frame(window, padding="20")
frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

style = ttk.Style()
style.configure("TFrame", background="#f0f8ff")
style.configure("TLabel", background="#f0f8ff", font=("Arial", 12, "bold"), foreground="#333333")

# Form elements
labels = ["Passenger Name:", "Age:", "Gender:", "Source:", "Destination:", "Journey Date:", "Return Date:", "Fare:"]
for i, text in enumerate(labels):
    ttk.Label(frame, text=text).grid(row=i, column=0, sticky=tk.W, pady=5, padx=10)

name_entry = ttk.Entry(frame)
age_entry = ttk.Entry(frame)
gender_combobox = ttk.Combobox(frame, values=["Male", "Female", "Other"])
source_combobox = ttk.Combobox(frame, values=["Delhi", "Hyderabad", "Mysore", "Bagalkote", "Ballari", 
                                            "Belagavi", "Bengaluru", "Bidar", "Chamarajanagar", 
                                            "Chikkaballapur", "Chikkamagaluru", "Chitradurga", 
                                            "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", 
                                            "Hassan", "Haveri", "Kalaburagi", "Kodagu", "Kolar", 
                                            "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara", 
                                            "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada", 
                                            "Vijayanagara", "Vijayapura", "Yadgir"])
destination_combobox = ttk.Combobox(frame, values=["Delhi", "Hyderabad", "Mysore", "Bagalkote", "Ballari", 
                                                  "Belagavi", "Bengaluru", "Bidar", "Chamarajanagar", 
                                                  "Chikkaballapur", "Chikkamagaluru", "Chitradurga", 
                                                  "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", 
                                                  "Hassan", "Haveri", "Kalaburagi", "Kodagu", "Kolar", 
                                                  "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara", 
                                                  "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada", 
                                                  "Vijayanagara", "Vijayapura", "Yadgir"])

journey_date_var = tk.StringVar()
return_date_var = tk.StringVar()
journey_calendar = DateEntry(frame, textvariable=journey_date_var, date_pattern='yyyy-mm-dd',
                            mindate=datetime.now(), maxdate=datetime.now() + timedelta(days=365))
return_calendar = DateEntry(frame, textvariable=return_date_var, date_pattern='yyyy-mm-dd',
                           mindate=datetime.now() + timedelta(days=1), maxdate=datetime.now() + timedelta(days=365))
fare_entry = ttk.Entry(frame)

journey_date_var.trace_add('write', update_return_date_min)

entries = [name_entry, age_entry, gender_combobox, source_combobox, destination_combobox, 
          journey_calendar, return_calendar, fare_entry]
for i, widget in enumerate(entries):
    widget.grid(row=i, column=1, pady=5, padx=10, sticky=tk.EW)

# Buttons
ttk.Button(frame, text="Book Ticket", command=add_ticket).grid(row=8, column=0, pady=20, padx=10)
ttk.Button(frame, text="Clear", command=clear_fields).grid(row=8, column=1, pady=20, padx=10)

# Bottom buttons
buttons = [
    ("Search Ticket", 0.2, search_ticket),
    ("Cancel Ticket", 0.4, cancel_ticket),
    ("Export to CSV", 0.6, export_to_csv),
    ("Print Ticket", 0.8, print_ticket)
]
for text, relx, command in buttons:
    ttk.Button(window, text=text, command=command).place(relx=relx, rely=0.85, anchor=tk.CENTER)

# Analytics & History buttons
ttk.Button(window, text="Show Analytics", command=show_analytics).place(relx=0.3, rely=0.92, anchor=tk.CENTER)
ttk.Button(window, text="Travel History", command=show_travel_history).place(relx=0.7, rely=0.92, anchor=tk.CENTER)

window.mainloop()
conn.close()