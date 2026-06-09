import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from database.db import init_db
from database.db_queries import add_admin

def main():
    init_db()
    username = input("Admin username: ").strip()
    fullname = input("Full name: ").strip()
    password = input("Password: ").strip()
    if add_admin(username, password, fullname):
        print(f"Admin '{username}' created. Run: streamlit run src/app.py")
    else:
        print("Username taken.")

if __name__ == "__main__":
    main()
