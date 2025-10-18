import mysql.connector
import bcrypt
import datetime

def connect_db():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="ASFX"
        )
        print("Connection successful.")
        return conn
    except mysql.connector.Error:
        print("Connection cannot be found.")
        return None

# Bikin jadi siapa pun yang regis disini bakal jadi player dan masuk menu player.
def register_user(conn):
    cursor = conn.cursor()
    print("\n=== Registration ===")
    full_name = input("Enter Full Name: ")
    username = input("Enter Username: ")
    email = input("Enter Email: ")
    password = input("Enter Password: ")
    dob = input("Enter Date of Birth (YYYY-MM-DD): ")

    # Hash the password with bcrypt
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())  # bytes
    hashed_str = hashed.decode('utf-8')  # store as text in VARCHAR

    try:
        cursor.execute("""
            INSERT INTO Register (Full_Name, Username, Email, Password, Date_Of_Birth, Role)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (full_name, username, email, hashed_str, dob, "player"))
        conn.commit()
        reg_id = cursor.lastrowid
        log_action(conn, reg_id, "User registered an account.")
        print("Registration successful!")
    except mysql.connector.Error:
        # Batalkan semua register input jika ada error (Rollback)
        conn.rollback()
        print(f"Registration cannot be finished, Rollback due to error. Please try again later.")

def login_user(conn):
    cursor = conn.cursor()
    print("\n=== Login ===")
    username = input("Enter Username: ")

    # Easter Egg
    if username.lower() in ["admin", "administrator"]:
        print("What do you think you're doing :3")
        return

    password = input("Enter Password: ")

    cursor.execute("""
        SELECT Reg_id, Full_Name, Password, Role
        FROM Register
        WHERE Username = %s
    """, (username,))
    user = cursor.fetchone()
    if user:
        reg_id, full_name, stored_hash, role = user

        try:
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                print(f"Login successful! Welcome, {full_name}")

                # Masuk Menu masing-masing berdasarkan Role nya
                if role.lower() == "player":
                    log_action(conn, reg_id, "User login as player.")
                    after_login_menu(conn, reg_id)
                elif role.lower() == "admin":
                    log_action(conn, reg_id, "User login as admin.")
                    developer_menu(conn, reg_id, username)
                else:
                    print(f"Unknown role: {role}. Contact support.")
            else:
                print("Incorrect username or password.")
        except ValueError:
            print("Login failed due to invalid stored password format. Please contact tech support.")
    else:
        print("Incorrect username or password.")

def create_server(conn, reg_id):
    cursor = conn.cursor()
    print("\n=== Create New Server ===")
    svr_name = input("Server Name: ")
    svr_code = input("Server Code: ")

    # mode options
    modes = ["1v1", "2v2", "FFA", "Deathmatch"]
    print("\nChoose Server Mode:")
    for i, mode in enumerate(modes, 1):
        print(f"{i}. {mode}")

    while True:
        try:
            choice = int(input("Choose option (1-4): "))
            if 1 <= choice <= len(modes):
                svr_mode = modes[choice - 1]
                break
            else:
                print("Please choose a number between 1-4.")
        except ValueError:
            print("Input must be a number.")

    print("\nDescription is optional.")
    svr_desc = input("Server Description (press Enter to skip): ")
    if svr_desc.strip() == "":
        svr_desc = None

    try:
        cursor.execute("""
            INSERT INTO Server (Reg_id, SVR_Name, SVR_Code, SVR_Mode, SVR_Description)
            VALUES (%s, %s, %s, %s, %s)
        """, (reg_id, svr_name, svr_code, svr_mode, svr_desc))
        conn.commit()
        log_action(conn, reg_id, "User Created a new server.")
        print("Server created successfully.\n")
        play = input("Do you want to start the game? (y/n): ")
        if play == "y":
            print("The game starting, and you won the game because you are the server owner :D")
        else:
            return
    except mysql.connector.Error:
        # Batalkan semua create server input jika ada error (Rollback)
        conn.rollback()
        print(f"Creating Server cannot be finished, Rollback due to error. Please try again later.")

def join_server(conn, reg_id):
    cursor = conn.cursor()
    svr_name = input("Enter Server Name: ").strip()
    svr_code = input("Enter Server Code: ").strip()

    cursor.execute("""
        SELECT 1 FROM Server 
        WHERE SVR_Name = %s AND SVR_Code = %s
    """, (svr_name, svr_code))
    server = cursor.fetchone()

    if server:
        print(f"Successfully joined server '{svr_name}'.")
        log_action(conn, reg_id, "User Join a server.")
        play = input("Do you want to start the game? (y/n): ")
        if play == "y":
            print("The game starting, and you lost the game because you are not the server owner ;-;")
        else:
            return
    else:
        print("Server not found or code is incorrect.")

def inventory_menu(conn, reg_id):
    cursor = conn.cursor()
    cursor.execute("SELECT Inv_id, Inv_Name FROM Inventory")
    items = cursor.fetchall()

    print("\n=== Inventory ===")
    for idx, (inv_id, inv_name) in enumerate(items, start=1):
        print(f"{idx}. {inv_name}")

    choice = input("\nDo you want to change weapon? Choose 1-3, or 0 to cancel: ").strip()

    if not choice.isdigit():
        print("Invalid input, only numbers are allowed.")
        return

    choice = int(choice)

    if choice == 0:
        print("Cancelled weapon change.")
        return

    if 1 <= choice <= len(items):
        selected_item = items[choice - 1]
        inv_id = selected_item[0]
        inv_name = selected_item[1]

        cursor.execute("SELECT * FROM Equipment WHERE Reg_id = %s", (reg_id,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("UPDATE Equipment SET Inv_id = %s WHERE Reg_id = %s", (inv_id, reg_id))
            log_action(conn, reg_id, "User Update a weapon.")
            print(f"Weapon changed to {inv_name}")
        else:
            cursor.execute("INSERT INTO Equipment (Reg_id, Inv_id) VALUES (%s, %s)", (reg_id, inv_id))
            log_action(conn, reg_id, "User Insert a weapon.")
            print(f"Weapon selected: {inv_name}")

        conn.commit()
    else:
        print("Invalid option.")

def account_menu(conn, reg_id):
    cursor = conn.cursor()
    cursor.execute("SELECT Username, Email FROM Register WHERE Reg_id = %s", (reg_id,))
    account = cursor.fetchone()

    if not account:
        print("Account not found.")
        return

    username, email = account
    print("\n=== Account Menu ===")
    print(f"Username : {username}")
    print(f"Email    : {email}")

    print("\nOptions:")
    print("1. Update Username")
    print("2. Delete Account")
    print("3. Advanced Settings")
    print("0. Back")

    choice = input("Choose option: ").strip()

    if choice == "1":
        new_username = input("Enter new username: ").strip()
        try:
            cursor.execute("UPDATE Register SET Username = %s WHERE Reg_id = %s", (new_username, reg_id))
            conn.commit()
            log_action(conn, reg_id, "User Update their Username.")
            print(f"Username updated to {new_username}")
        except Exception:
            print(f"Failed to update username, please try again later.")

    elif choice == "2":
        confirm = input("Are you sure you want to delete this account? (y/n): ").lower()
        if confirm == "y":
            try:
                cursor.execute("DELETE FROM Register WHERE Reg_id = %s", (reg_id,))
                log_action(conn, reg_id, "User Delete their Account.")
                conn.commit()
                print("Account deleted successfully.")
                return "deleted"
            except Exception:
                print(f"Failed to delete account, please try again later.")
        else:
            print("Account deletion cancelled.")
    elif choice == "3":
        advanced_settings(conn, reg_id)
    elif choice == "0":
        print("Back to previous menu.")
    else:
        print("Invalid choice.")

def advanced_settings(conn, reg_id):
    cursor = conn.cursor()

    while True:
        print("\n=== Advanced Settings ===")
        print("1. Change Password")
        print("2. Change Email")
        print("0. Back")

        choice = input("Choose option: ").strip()

        if choice == "1":
            new_password = input("Enter new password: ").strip()
            hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            try:
                cursor.execute("UPDATE Register SET Password = %s WHERE Reg_id = %s", (hashed, reg_id))
                conn.commit()
                log_action(conn, reg_id, "User Update their Password.")
                print("Password successfully updated.")
            except Exception:
                print(f"Failed to update password, please try again later.")

        elif choice == "2":
            new_email = input("Enter new email: ").strip()
            try:
                cursor.execute("UPDATE Register SET Email = %s WHERE Reg_id = %s", (new_email, reg_id))
                conn.commit()
                log_action(conn, reg_id, "User Update their Email.")
                print("Email successfully updated.")
            except Exception:
                print(f"Failed to update email, please try again later.")

        elif choice == "0":
            print("Back to Menu.")
            break
        else:
            print("Invalid choice.")

# Register admin baru
def register_admin(conn, reg_id, username):
    cursor = conn.cursor()
    print("\n=== Register New Admin ===")
    
    full_name = input("Enter Full Name: ")
    username = input("Enter Username: ")
    email = input("Enter Email: ")
    password = input("Enter Password: ")
    dob = input("Enter Date of Birth (YYYY-MM-DD): ")

    # Hash password dengan bcrypt
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    hashed_str = hashed.decode('utf-8')

    try:
        cursor.execute("""
            INSERT INTO Register (Full_Name, Username, Email, Password, Date_Of_Birth, Role)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (full_name, username, email, hashed_str, dob, "admin"))
        conn.commit()
        log_action(conn, reg_id, "Admin Account have been created", username)
        print("Admin account registered successfully!")
    except mysql.connector.Error as err:
        conn.rollback()
        print("Failed to register an admin.")
        print(f"Error detail: {err}")

# Bikin Server Spesial
def create_special_server(conn, reg_id, username):
    cursor = conn.cursor()
    print("\n=== Create New Server ===")
    svr_name = input("Server Name: ")
    svr_code = input("Server Code: ")

    # mode options
    modes = ["1v1", "2v2", "FFA", "Deathmatch", "Anniversary", "New Year"]
    print("\nChoose Server Mode:")
    for i, mode in enumerate(modes, 1):
        print(f"{i}. {mode}")

    while True:
        try:
            choice = int(input("Choose option (1-6): "))
            if 1 <= choice <= len(modes):
                svr_mode = modes[choice - 1]
                break
            else:
                print("Please choose a number between 1-6.")
        except ValueError:
            print("Input must be a number.")

    print("\nDescription is optional.")
    svr_desc = input("Server Description (press Enter to skip): ")
    if svr_desc.strip() == "":
        svr_desc = None

    try:
        cursor.execute("""
            INSERT INTO Server (Reg_id, SVR_Name, SVR_Code, SVR_Mode, SVR_Description)
            VALUES (%s, %s, %s, %s, %s)
        """, (reg_id, svr_name, svr_code, svr_mode, svr_desc))
        conn.commit()
        log_action(conn, reg_id, "Special Server have been created", username)
        print("Server created successfully.\n")
        play = input("Do you want to start the game? (y/n): ")
        if play == "y":
            print("The game starting, and you won the game because you are the server owner :D")
        else:
            return
    except mysql.connector.Error as err:
        conn.rollback()
        print("Failed to created a server.")
        print(f"Error detail: {err}")

# Lihat server, dan join
def join_server_mediator(conn, reg_id, username):
    cursor = conn.cursor()
    print("\n=== Join Server as Mediator ===")

    try:
        cursor.execute("SELECT SVR_id, SVR_Name, SVR_Mode FROM Server")
        servers = cursor.fetchall()

        if not servers:
            print("No servers available to join.")
            return

        print("\nAvailable Servers:")
        for svr in servers:
            print(f"[{svr[0]}] {svr[1]} - Mode: {svr[2]}")

        svr_choice = input("\nEnter Server ID to join as mediator: ")

        cursor.execute("SELECT SVR_Name FROM Server WHERE SVR_id = %s", (svr_choice,))
        result = cursor.fetchone()

        if not result:
            print(" Server not found.")
            return

        svr_name = result[0]
        print(f"\n Joined '{svr_name}' as Mediator (Justice Enforcer).")
        print("You are now monitoring this server. Cheaters beware!")

        log_action(conn, reg_id, f"Joined server '{svr_name}' as mediator", username)

    except mysql.connector.Error as err:
        conn.rollback()
        print("Failed to join server as mediator.")
        print(f"Error detail: {err}")

# Lihat inventory, dan buat baru
def manage_inventory(conn, reg_id, username):
    cursor = conn.cursor()
    print("\n=== Inventory Management ===")

    try:
        while True:
            print("\n1. View Inventory")
            print("2. Add New Weapon")
            print("3. Back to Developer Menu")
            choice = input("Choose option (1-3): ")

            if choice == "1":
                cursor.execute("SELECT Inv_id, Inv_Name FROM Inventory ORDER BY Inv_id ASC")
                inventory = cursor.fetchall()

                if not inventory:
                    print("No weapons in inventory.")
                else:
                    print("\n--- Current Inventory ---")
                    for inv in inventory:
                        print(f"[{inv[0]}] {inv[1]}")
            elif choice == "2":
                new_weapon = input("Enter new weapon name: ").strip()
                if new_weapon == "":
                    print("Weapon name cannot be empty.")
                    continue

                try:
                    cursor.execute("INSERT INTO Inventory (Inv_Name) VALUES (%s)", (new_weapon,))
                    conn.commit()
                    log_action(conn, reg_id, f"Added new weapon named '{new_weapon}' to inventory", username)
                    print(f"Weapon '{new_weapon}' added successfully.")
                except mysql.connector.Error as err:
                    conn.rollback()
                    print("Failed to add new weapon.")
                    print(f"Error detail: {err}")
            elif choice == "3":
                break
            else:
                print("Invalid option. Please choose between 1-3.")
    except mysql.connector.Error as err:
        print("Unexpected database error.")
        print(f"Error detail: {err}")

# lihat audit log
def view_audit_log(conn):
    cursor = conn.cursor()
    print("\n=== Audit Log Viewer ===")

    page = 0
    limit = 10
    search_term = input("Search Log ID or Username (press Enter to show all): ").strip()

    while True:
        offset = page * limit

        if search_term:
            # Filter log berdasarkan Log_id (angka) atau Username (teks)
            if search_term.isdigit():
                cursor.execute("""
                    SELECT a.Log_id, r.Username, a.Action, a.Timestamp
                    FROM Audit_Log a
                    JOIN Register r ON a.Reg_id = r.Reg_id
                    WHERE a.Log_id = %s
                    ORDER BY a.Log_id DESC
                    LIMIT %s OFFSET %s
                """, (search_term, limit, offset))
            else:
                cursor.execute("""
                    SELECT a.Log_id, r.Username, a.Action, a.Timestamp
                    FROM Audit_Log a
                    JOIN Register r ON a.Reg_id = r.Reg_id
                    WHERE r.Username LIKE %s
                    ORDER BY a.Log_id DESC
                    LIMIT %s OFFSET %s
                """, (f"%{search_term}%", limit, offset))
        else:
            cursor.execute("""
                SELECT a.Log_id, r.Username, a.Action, a.Timestamp
                FROM Audit_Log a
                JOIN Register r ON a.Reg_id = r.Reg_id
                ORDER BY a.Log_id DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))

        logs = cursor.fetchall()

        if not logs:
            if page == 0:
                print("No audit logs found.")
            else:
                print("No more logs available.")
            break

        print(f"\n--- Page {page + 1} ---")
        for log in logs:
            print(f"[{log[0]}] User: {log[1]} | Action: {log[2]} | Time: {log[3]}")

        print("\nOptions:")
        print("N - Next page")
        print("B - Back to Developer Menu")
        print("C - Change search")

        choice = input("Choose option: ").strip().lower()

        if choice == "n":
            page += 1
        elif choice == "c":
            search_term = input("Enter new Log ID or Username: ").strip()
            page = 0
        elif choice == "b":
            break
        else:
            print("Invalid input. Returning to Developer Menu.")
            break

# log setiap aksi yang dilakukan player dan admin
def log_action(conn, reg_id, action_desc, username=None):
    cursor = conn.cursor()
    timestamp = datetime.datetime.now()

    # Jika username ada, maka gunakan ini
    if username:
        action_desc = f"{action_desc} by Admin '{username}'"

    cursor.execute(
        "INSERT INTO Audit_Log (Reg_id, Action, Timestamp) VALUES (%s, %s, %s)",
        (reg_id, action_desc, timestamp)
    )
    conn.commit()

# Menu untuk Admin
def developer_menu(conn, reg_id, username):
    while True:
        print("\n=== Developer Menu ===")
        print("1. Register Admin Account")
        print("2. Create Special Server")
        print("3. Join Server as Mediator")
        print("4. Manage Inventory")
        print("5. View Audit Log")
        print("6. Logout")

        choice = input("Select option: ")

        if choice == "1":
            register_admin(conn, reg_id, username)
        elif choice == "2":
            create_special_server(conn, reg_id, username)
        elif choice == "3":
            join_server_mediator(conn, reg_id, username)
        elif choice == "4":
            manage_inventory(conn, reg_id, username)
        elif choice == "5":
            view_audit_log(conn)
        elif choice == "6":
            print("Logging out, good work today Admin ", username)
            break
        else:
            print("Invalid choice, please try again.")

def after_login_menu(conn, reg_id):
    while True:
        print("\n=== After Login Menu ===")
        print("1. Create Server")
        print("2. Join Server")
        print("3. Inventory")
        print("4. Account")
        print("5. Logout")
        choice = input("Choose menu: ")

        if choice == "1":
            create_server(conn, reg_id)
        elif choice == "2":
            join_server(conn, reg_id)
        elif choice == "3":
            inventory_menu(conn, reg_id)
        elif choice == "4":
            result = account_menu(conn, reg_id)
            if result == "deleted":
                print("You have been logged out automatically.")
                break
        elif choice == "5":
            print("Logged out successfully.")
            break
        else:
            print("Invalid option. Try again.")

def main():
    conn = connect_db()
    while True:
        print("\n=== Main Menu ===")
        print("1. Login")
        print("2. Registration")
        print("3. Exit")
        choice = input("Choose menu: ")

        if choice == "1":
            login_user(conn)
        elif choice == "2":
            register_user(conn)
        elif choice == "3":
            print("Exiting program.")
            break
        else:
            print("Invalid option. Try again.")

    conn.close()

if __name__ == "__main__":
    main()
