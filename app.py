import os
from pathlib import Path
from functools import wraps

from flask import (
    Flask,
    render_template,
    render_template_string,
    abort,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.security import check_password_hash

from database import (
    create_tables,
    get_all_products,
    get_products_by_category,
    get_product_by_id,
    get_admin_by_email
)


app = Flask(__name__)

# SECURITY CONFIGURATION
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

if not app.secret_key:
    raise RuntimeError(
        "FLASK_SECRET_KEY is missing. Configure it before starting Flask."
    )

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# ENSURE DATABASE TABLES EXIST
create_tables()


# ADMIN LOGIN PROTECTION
def admin_required(view_function):

    @wraps(view_function)
    def decorated_function(*args, **kwargs):

        if "admin_id" not in session:
            flash("Please log in as an administrator.", "error")
            return redirect(url_for("admin_login"))

        return view_function(*args, **kwargs)

    return decorated_function


# ALL PRODUCT CATEGORIES
CATEGORIES = {
    "clothing": {
        "title": "Our Clothing Collection",
        "description": (
            "Explore stylish clothing designed "
            "to bring out your elegance."
        ),
        "folder": "clothing",
        "keywords": [
            "clothing", "clothes", "fashion", "outfits",
            "tops", "shirts", "trousers", "skirts",
            "jeans", "blouses", "wear"
        ]
    },

    "gowns": {
        "title": "Beautiful Gowns",
        "description": (
            "Discover elegant gowns for every occasion. "
            "Find your perfect style at Grace Luxury."
        ),
        "folder": "gowns",
        "keywords": [
            "gown", "gowns", "dress", "dresses",
            "evening dress", "party dress", "maxi dress"
        ]
    },

    "handbags": {
        "title": "Beautiful Handbags",
        "description": (
            "Explore our collection of beautiful and "
            "elegant handbags."
        ),
        "folder": "handbags",
        "keywords": [
            "handbag", "handbags", "purse", "purses",
            "ladies bag", "fashion bag"
        ]
    },

    "crossbody_bags": {
        "title": "Beautiful Crossbody Bags",
        "description": (
            "Discover stylish crossbody bags designed "
            "for elegance, comfort and everyday fashion."
        ),
        "folder": "crossbody_bags",
        "keywords": [
            "crossbody", "crossbody bag", "crossbody bags",
            "shoulder bag", "sling bag", "small bag"
        ]
    },

    "necklaces": {
        "title": "Necklaces & Jewellery",
        "description": (
            "Discover beautiful necklaces and elegant "
            "jewellery that add luxury to every outfit."
        ),
        "folder": "necklaces",
        "keywords": [
            "necklace", "necklaces", "jewellery",
            "jewelry", "pendant", "chains", "earrings"
        ]
    },

    "shoes": {
        "title": "Beautiful Shoes",
        "description": (
            "Discover elegant heels, sneakers, canvas shoes "
            "and fashionable footwear for every occasion."
        ),
        "folder": "shoes",
        "keywords": [
            "shoe", "shoes", "sneakers", "sneaker",
            "canvas", "canvas shoes", "nike", "adidas",
            "boots", "footwear", "trainers"
        ]
    },

    "hair": {
        "title": "Wigs & Human Hair",
        "description": (
            "Discover beautiful bone straight, pixie curls, "
            "frontal wigs, closure wigs and luxurious "
            "human hair collections."
        ),
        "folder": "hair",
        "keywords": [
            "hair", "wig", "wigs", "human hair",
            "bone straight", "pixie curls", "frontal",
            "closure", "weavon", "weave"
        ]
    },

    "watches": {
        "title": "Elegant Wristwatches",
        "description": (
            "Explore our collection of elegant and stylish "
            "wristwatches for every occasion."
        ),
        "folder": "watches",
        "keywords": [
            "watch", "watches", "wristwatch",
            "wristwatches", "timepiece"
        ]
    },

    "heels": {
        "title": "Beautiful Heels",
        "description": (
            "Discover elegant heels for special occasions, "
            "parties, celebrations and everyday style."
        ),
        "folder": "heels",
        "keywords": [
            "heel", "heels", "high heels",
            "stilettos", "women heels"
        ]
    }
}


# ALLOWED IMAGE FORMATS
ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".avif"
}


# AUTOMATICALLY LOAD CATEGORY IMAGES
def get_category_images(folder):

    image_folder = Path(app.static_folder) / "images" / folder

    if not image_folder.exists():
        return []

    images = []

    for image in image_folder.iterdir():

        if (
            image.is_file()
            and image.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS
        ):
            images.append(image.name)

    return sorted(images, key=str.casefold)


# REUSABLE CATEGORY PAGE
def show_category(category_name):

    category = CATEGORIES.get(category_name)

    if category is None:
        abort(404)

    images = get_category_images(category["folder"])
    products = get_products_by_category(category_name)

    return render_template(
        "category.html",
        category=category,
        images=images,
        products=products
    )


# SEARCH ENGINE
def search_categories(search_query):

    query = search_query.casefold().strip()
    matching_categories = []

    if not query:
        return matching_categories

    for category_name, category in CATEGORIES.items():

        searchable_words = (
            category["title"].casefold().split()
            + category["description"].casefold().split()
            + category["keywords"]
        )

        for keyword in searchable_words:

            if keyword in query or query in keyword:

                images = get_category_images(category["folder"])

                matching_categories.append({
                    "name": category_name,
                    "title": category["title"],
                    "description": category["description"],
                    "folder": category["folder"],
                    "image": images[0] if images else None
                })

                break

    return matching_categories


# HOMEPAGE
@app.route("/")
def home():

    shoes_images = get_category_images("shoes")
    hair_images = get_category_images("hair")
    watches_images = get_category_images("watches")
    heels_images = get_category_images("heels")
    crossbody_images = get_category_images("crossbody_bags")

    return render_template(
        "home.html",
        shoes_images=shoes_images,
        hair_images=hair_images,
        watches_images=watches_images,
        heels_images=heels_images,
        crossbody_images=crossbody_images
    )


# SHOP PAGE
@app.route("/store")
def store():

    category_cards = []

    for category_name, category in CATEGORIES.items():

        images = get_category_images(category["folder"])

        category_cards.append({
            "name": category_name,
            "title": category["title"],
            "description": category["description"],
            "folder": category["folder"],
            "image": images[0] if images else None
        })

    products = get_all_products()

    return render_template(
        "store.html",
        categories=category_cards,
        products=products
    )


# CUSTOMER SEARCH
@app.route("/search")
def search():

    search_query = request.args.get("q", "").strip()
    results = search_categories(search_query)

    if not search_query:
        message = "Please enter a fashion product to search."

    elif results:
        message = ""

    else:
        message = (
            "We couldn't find a matching fashion category. "
            "Grace Luxury specialises in fashion, including "
            "clothing, gowns, shoes, bags, jewellery and hair. "
            "Please try another fashion search."
        )

    return render_template(
        "search_results.html",
        query=search_query,
        results=results,
        message=message
    )


# INDIVIDUAL PRODUCT DETAILS
@app.route("/product/<int:product_id>")
def product_detail(product_id):

    product = get_product_by_id(product_id)

    if product is None or not product["is_active"]:
        abort(404)

    return render_template(
        "product_detail.html",
        product=product
    )


# =====================================================
# ADMINISTRATOR LOGIN
# =====================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if "admin_id" in session:
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        admin = get_admin_by_email(email)

        if admin and check_password_hash(
            admin["password_hash"], password
        ):

            session.clear()
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["full_name"]

            flash("Welcome to your admin dashboard!", "success")

            return redirect(url_for("admin_dashboard"))

        flash("Incorrect email or password.", "error")

    return render_template("admin_login.html")


# ADMIN DASHBOARD
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():

    return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport"
                  content="width=device-width, initial-scale=1.0">
            <title>Admin Dashboard | Grace Luxury</title>
        </head>

        <body style="font-family: Arial; background: #fffaf5;
                     padding: 40px;">

            <h1 style="color: #3b1f2b;">
                GRACE LUXURY ADMIN DASHBOARD
            </h1>

            <h2>Welcome, {{ admin_name }}!</h2>

            <p>You are successfully logged in as an administrator.</p>

            <a href="{{ url_for('admin_logout') }}"
               style="background: #3b1f2b; color: white;
                      padding: 12px 20px; text-decoration: none;">
                Logout
            </a>

        </body>
        </html>
    """, admin_name=session.get("admin_name", "Administrator"))


# ADMIN LOGOUT
@app.route("/admin/logout")
@admin_required
def admin_logout():

    session.clear()

    flash("You have logged out successfully.", "success")

    return redirect(url_for("admin_login"))


# CLOTHING
@app.route("/clothing")
def clothing():
    return show_category("clothing")


# GOWNS
@app.route("/gowns")
def gowns():
    return show_category("gowns")


# HANDBAGS
@app.route("/handbags")
def handbags():
    return show_category("handbags")


# CROSSBODY BAGS
@app.route("/crossbody-bags")
def crossbody_bags():
    return show_category("crossbody_bags")


# NECKLACES AND JEWELLERY
@app.route("/necklaces")
def necklaces():
    return show_category("necklaces")


# SHOES
@app.route("/shoes")
def shoes():
    return show_category("shoes")


# WIGS AND HUMAN HAIR
@app.route("/hair")
def hair():
    return show_category("hair")


# WRISTWATCHES
@app.route("/watches")
def watches():
    return show_category("watches")


# HEELS
@app.route("/heels")
def heels():
    return show_category("heels")


# FUTURE CATEGORY PAGES
@app.route("/category/<category_name>")
def category_page(category_name):
    return show_category(category_name)


# CUSTOMER REGISTRATION
@app.route("/register")
def register():
    return render_template("register.html")


# CUSTOMER LOGIN
@app.route("/login")
def login():
    return render_template("login.html")


# FORGOTTEN PASSWORD
@app.route("/forgotten_password")
def forgotten_password():
    return render_template("forgotten.html")


if __name__ == "__main__":
    app.run(debug=True)