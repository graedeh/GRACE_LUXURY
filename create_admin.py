from getpass import getpass

from werkzeug.security import generate_password_hash

from database import add_admin, get_admin_by_email


def create_first_admin():

    print("\n===== GRACE LUXURY ADMIN SETUP =====\n")

    full_name = input("Enter your full name: ").strip()
    email = input("Enter your admin email: ").strip().lower()

    if not full_name or not email:
        print("Name and email are required.")
        return

    if get_admin_by_email(email):
        print("An administrator with this email already exists.")
        return

    password = getpass("Create your admin password: ")
    confirm_password = getpass("Confirm your password: ")

    if len(password) < 8:
        print("Password must contain at least 8 characters.")
        return

    if password != confirm_password:
        print("The passwords do not match.")
        return

    password_hash = generate_password_hash(password)

    admin_id = add_admin(
        full_name,
        email,
        password_hash
    )

    print("\nAdministrator account created successfully!")
    print(f"Admin ID: {admin_id}")
    print("You can now use your admin login page.")


if __name__ == "__main__":
    create_first_admin()