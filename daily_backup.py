import os
import time
import schedule
from datetime import datetime, timedelta

def backup_database():
    db_name = "ASFX"
    user = "root"
    password = ""  # add if your MySQL has a password
    backup_dir = "D:\\project_backup"  # change to your desired backup folder

    # Ensure the backup directory exists
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # Generate a unique backup filename based on the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}\\{db_name}_backup_{timestamp}.sql"

    # Run the mysqldump command
    command = f'mysqldump -u {user} -p{password} {db_name} > "{backup_file}"'
    os.system(command)
    print(f"Backup created: {backup_file}")

    # Remove backups older than 7 days
    delete_old_backups(backup_dir, days=7)


def delete_old_backups(backup_dir, days=7):
    now = datetime.now()
    cutoff = now - timedelta(days=days)
    deleted_files = 0

    for filename in os.listdir(backup_dir):
        if filename.endswith(".sql"):
            file_path = os.path.join(backup_dir, filename)
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))

            if file_time < cutoff:
                os.remove(file_path)
                deleted_files += 1

    if deleted_files > 0:
        print(f"{deleted_files} old backup files deleted (older than {days} days).")
    else:
        print("No old backups were deleted.")


# Schedule the backup to run daily at 01:00
schedule.every().day.at("01:00").do(backup_database)

# backup_database()  # Test Backup right now
print("Automatic database backup is running. Press Ctrl + C to stop.")

while True:
    schedule.run_pending()
    time.sleep(60)