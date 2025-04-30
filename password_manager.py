import sqlite3
from cryptography.fernet import Fernet
import tkinter as tk
from tkinter import messagebox
import os
import secrets
import string
import hashlib

#Master Password File for the passwords database
MASTER_PASSWORD_FILE = "master.key"

def generate_key():
    #Genereate a new encryption key
    key = Fernet.generate_key()
    with open("key.key", "wb") as key_file:
        key_file.write(key)
    print("Key generated and saved!")

def load_key():
    #Load the previously generated encryption key
    return open("key.key", "rb").read()

#Generates a key and loads it to encrypt passwords
if os.path.exists("key.key"):
    key = load_key()
else:
    generate_key()
    key = load_key()
cipher = Fernet(key)

def create_database():
    #Creates a database to store passwords.
    con = sqlite3.connect("passwords.db")
    cursor = con.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS passwords(website, username, password)""")
    con.commit()
    con.close()

def set_master_password():
    def save_password():
        password = entry1.get()
        confirm = entry2.get()
        if password != confirm:
            messagebox.showerror("Error", "Passwords don't match.")
            return
        hashed = hashlib.sha256(password.encode()).hexdigest()
        with open(MASTER_PASSWORD_FILE, "w") as f:
            f.write(hashed)
        messagebox.showinfo("Success", "Master password set. Please restart the application.")
        setup_window.destroy()
    
    setup_window = tk.Tk()
    setup_window.title("Set Master Password")
    setup_window.geometry("400x200")

    tk.Label(setup_window, text="Enter New Master Pasword").pack(pady=5)
    entry1 = tk.Entry(setup_window, show="*", width=30)
    entry1.pack(pady=5)

    tk.Label(setup_window, text="Confirm Master Pasword").pack(pady=5)
    entry2 = tk.Entry(setup_window, show="*", width=30)
    entry2.pack(pady=5)

    tk.Button(setup_window, text="Set Password", command=save_password).pack(pady=10)
    setup_window.mainloop()

def verify_master_password():
    if not os.path.exists(MASTER_PASSWORD_FILE):
        set_master_password()
        return
    
    def check_password():
        entered = master_entry.get()
        entered_hash = hashlib.sha256(entered.encode()).hexdigest()
        with open(MASTER_PASSWORD_FILE, "r") as f:
            stored_hash = f.read()
        if entered_hash == stored_hash:
            master_window.destroy()
            create_gui()
        else:
            messagebox.showerror("Access Denied", "Incorrect Master Password")

    master_window = tk.Tk()
    master_window.title("Enter Master Password")
    master_window.geometry("400x150")

    tk.Label(master_window, text="Master Password:")
    master_entry = tk.Entry(master_window, show="*", width=30)
    master_entry.pack(pady=5)

    tk.Button(master_window, text="Submit", command=check_password).pack(pady=10)
    master_window.mainloop()

def store_password(website, username, password):
    #Encrypt and store password in the database.
    encrypted_password = cipher.encrypt(password.encode())
    con = sqlite3.connect("passwords.db")
    cursor = con.cursor()
    cursor.execute("""INSERT INTO passwords (website, username, password) VALUES (?, ?, ?)""",
                   (website, username, encrypted_password))
    con.commit()
    con.close()

def retrieve_password(website, username):
    #Retrieve and decrypt a stored password.
    con = sqlite3.connect("passwords.db")
    cursor = con.cursor()
    cursor.execute("SELECT password FROM passwords WHERE website=? AND username=?", (website, username))
    result = cursor.fetchone()
    con.close()

    if result:
        encrypted_password = result[0]
        decrypted_password = cipher.decrypt(encrypted_password)
        return decrypted_password
    else:
        print("No password found for this website/username.")
        return None
    
def generate_password():
    #Generate a random strong password. (Could add length param)
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for _ in range(16))
    return password

def update_password(website, username, new_password):
    #Update an existing password in the database
    encrypted_password = cipher.encrypt(new_password.encode())
    con = sqlite3.connect("password.db")
    cursor = con.cursor()
    cursor.execute("""UPDATE passwords SET password = ? WHERE website = ? AND username = ?""",
                   (encrypted_password, website, username))
    con.commit()
    con.close()
    print(f"Password for {website} has been updated.")

def search_passwords(term):
    #Search for entries by website or username.
    con = sqlite3.connect("passwords.db")
    cursor = con.cursor()
    cursor.execute("""SELECT website, username, password FROM passwords
                   WHERE website LIKE ? OR username LIKE ?""",
                   (f'%{term}%', f'%{term}%'))
    results = cursor.fetchall()
    con.close()
    decrypted_results = []
    for website, username, encrypted_password in results:
        try:
            decrypted_password = cipher.decrypt(encrypted_password).decode()
        except Exception:
            decrypted_password = "[Decryption Failed]"
        decrypted_results.append((website, username, decrypted_password))
    return decrypted_results

def delete_password(website, username):
    #Deletes a password
    con = sqlite3.connect("passwords.db")
    cursor = con.cursor()
    cursor.execute("""DELETE from passwords WHERE website=? AND username=?""",
                   (website, username))
    
    con.commit()
    con.close()

# -- GUI Functions --

def on_store():
    website = website_entry.get()
    username = username_entry.get()
    password = password_entry.get()

    if website and username and password:
        store_password(website, username, password)
        messagebox.showinfo("Success", "Password stored.")
    else:
        messagebox.showerror("Error", "Please fill out all fields")
    clear_fields()

def on_retrieve():
    website = website_entry.get()
    username = username_entry.get()

    if website and username:
        password = retrieve_password(website, username)
        if password:
            messagebox.showinfo("Password", f"Password for {website} ({username}): {password}")
        else:
            messagebox.showerror("Error", "No password for this website/username.")
    else:
        messagebox.showerror("Error", "Please fill out website and username")

def on_update():
    website = website_entry.get()
    username = username_entry.get()
    password = password_entry.get()

    if website and username and password:
        update_password(website, username, password)
        messagebox.showinfo("Success", "Password updated.")
    else:
        messagebox.showerror("Error", "Please fill out all fields.")
    clear_fields()

def on_delete():
    website = website_entry.get()
    username = username_entry.get()
    if website and username:
        delete_password(website, username)
        messagebox.showinfo("Success", "Password deleted.")
    else:
        messagebox.showerror("Error", "Please fill out all fields")
    clear_fields()

def on_search():
    term = search_entry.get()
    results = search_passwords(term)
    results_list.delete(0, tk.END) # Clear previous results

    if results:
        for result in results:
            results_list.insert(tk.END, f"Website: {result[0]} | Username: {result[1]} | Password: {result[2]}")
    else:
        messagebox.showinfo("No Results", "No matching entries found.")

def on_generate():
    generated = generate_password()
    password_entry.delete(0, tk.END)
    password_entry.insert(0, generated)

    #Add copy to clipboard functionality

    tk.messagebox.showinfo("Password Generated", "Password generated.")

def clear_fields():
    website_entry.delete(0, tk.END)
    username_entry.delete(0, tk.END)
    password_entry.delete(0, tk.END)
    search_entry.delete(0, tk.END)
    results_list.delete(0, tk.END)

def create_gui():
    global website_entry, username_entry, password_entry, search_entry, results_list

    root = tk.Tk()
    root.title("Password Manager")
    root.geometry("700x500")
    root.resizable(True, True)

    root.columnconfigure(0, weight=1)
    root.columnconfigure(1, weight=3)
    root.rowconfigure(8, weight=1)

    tk.Label(root, text="Website:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
    website_entry = tk.Entry(root, width=40)
    website_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

    tk.Label(root, text="Username:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
    username_entry = tk.Entry(root, width=40)
    username_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew')

    tk.Label(root, text="Password:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
    password_entry = tk.Entry(root, width=40)
    password_entry.grid(row=2, column=1, padx=5, pady=5, sticky='ew')

    tk.Button(root, text= "Store Password", command=on_store).grid(row=3, column=0, pady=10)
    tk.Button(root, text= "Retrieve Password", command=on_retrieve).grid(row=3, column=1, pady=10)
    tk.Button(root, text= "Update Password", command=on_update).grid(row=4, column=0, pady=10)
    tk.Button(root, text= "Delete Password", command=on_delete).grid(row=4, column=1, pady=10)
    tk.Button(root, text= "Generate Password", command=on_generate).grid(row=5, pady=10)
    tk.Button(root, text="Clear", command=clear_fields).grid(row=7, column=1, pady=10)

    tk.Label(root, text="Search (website or username):").grid(row=6, column=0, padx=5, pady=5, sticky='e')
    search_entry = tk.Entry(root, width=40)
    search_entry.grid(row=6, column=1, padx=5, pady=5)

    tk.Button(root, text="Search", command=on_search).grid(row=7, column=0, pady=10)

    results_frame = tk.Frame(root)
    results_frame.grid(row=8, column=0, columnspan=2, sticky='nsew')
    results_frame.rowconfigure(0, weight=1)
    results_frame.columnconfigure(0, weight=1)

    results_list = tk.Listbox(results_frame)
    results_list.grid(row=0, column=0, sticky='nsew')

    scrollbar = tk.Scrollbar(results_frame, orient="vertical", command=results_list.yview)
    scrollbar.grid(row=0, column=1, sticky='ns')
    results_list.config(yscrollcommand=scrollbar.set)
    
    root.mainloop()


def main():
    create_database()
    verify_master_password()

if __name__ == "__main__":
    main()