import os
import uuid
from pathlib import Path
from functools import wraps

from flask import (
    Flask,
    render_template,
    abort,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

from database import (
    create_tables,
    add_product,
    get_all_products,
    get_products_by_category,
    get_product_by_id,
    get_admin_by_email,
    update_product,
    delete_product,
    get_connection
)


app = Flask(__name__)

# =====================================================
# SECURITY CONFIGURATION
# =====================================================

app.secret_key = os.environ.get("FLASK_SECRET_KEY")

if not app.secret_key:
    raise RuntimeError(
        "FLASK_SECRET_KEY is missing. Configure it before starting Flask."
    )

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

create_tables()


# =====================================================
# ADMIN LOGIN PROTECTION
# =====================================================

def admin_required(view_function):

    @wraps(view_function)
    def decorated_function(*args, **kwargs):

        if "admin_id" not in session:
            flash("Please log in as an administrator.", "error")
            return redirect(url_for("admin_login"))

        return view_function(*args, **kwargs)

    return decorated_function


# =====================================================
# PRODUCT CATEGORIES
# =====================================================

CATEGORIES = {
    "clothing": {
        "title": "Our Clothing Collection",
        "description": "Explore stylish clothing designed to bring out your elegance.",
        "folder": "clothing",
        "keywords": [
            "clothing", "clothes", "fashion", "outfits",
            "tops", "shirts", "trousers", "skirts",
            "jeans", "blouses", "wear"
        ]
    },
    "gowns": {
        "title": "Beautiful Gowns",
        "description": "Discover elegant gowns for every occasion. Find your perfect style at Grace Luxury.",
        "folder": "gowns",
        "keywords": [
            "gown", "gowns", "dress", "dresses",
            "evening dress", "party dress", "maxi dress"
        ]
    },
    "handbags": {
        "title": "Beautiful Handbags",
        "description": "Explore our collection of beautiful and elegant handbags.",
        "folder": "handbags",
        "keywords": [
            "handbag", "handbags", "purse", "purses",
            "ladies bag", "fashion bag"
        ]
    },
    "crossbody_bags": {
        "title": "Beautiful Crossbody Bags",
        "description": "Discover stylish crossbody bags designed for elegance, comfort and everyday fashion.",
        "folder": "crossbody_bags",
        "keywords": [
            "crossbody", "crossbody bag", "crossbody bags",
            "shoulder bag", "sling bag", "small bag"
        ]
    },
    "necklaces": {
        "title": "Necklaces & Jewellery",
        "description": "Discover beautiful necklaces and elegant jewellery that add luxury to every outfit.",
        "folder": "necklaces",
        "keywords": [
            "necklace", "necklaces", "jewellery",
            "jewelry", "pendant", "chains", "earrings"
        ]
    },
    "shoes": {
        "title": "Beautiful Shoes",
        "description": "Discover elegant heels, sneakers, canvas shoes and fashionable footwear for every occasion.",
        "folder": "shoes",
        "keywords": [
            "shoe", "shoes", "sneakers", "sneaker",
            "canvas", "canvas shoes", "nike", "adidas",
            "boots", "footwear", "trainers"
        ]
    },
    "hair": {
        "title": "Wigs & Human Hair",
        "description": "Discover beautiful bone straight, pixie curls, frontal wigs, closure wigs and luxurious human hair collections.",
        "folder": "hair",
        "keywords": [
            "hair", "wig", "wigs", "human hair",
            "bone straight", "pixie curls", "frontal",
            "closure", "weavon", "weave"
        ]
    },
    "watches": {
        "title": "Elegant Wristwatches",
        "description": "Explore our collection of elegant and stylish wristwatches for every occasion.",
        "folder": "watches",
        "keywords": [
            "watch", "watches", "wristwatch",
            "wristwatches", "timepiece"
        ]
    },
    "heels": {
        "title": "Beautiful Heels",
        "description": "Discover elegant heels for special occasions, parties, celebrations and everyday style.",
        "folder": "heels",
        "keywords": [
            "heel", "heels", "high heels",
            "stilettos", "women heels"
        ]
    }
}


# =====================================================
# IMAGE CONFIGURATION
# =====================================================

ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"
}


def allowed_image(filename):
    return Path(filename).suffix.lower() in ALLOWED_IMAGE_EXTENSIONS


def get_category_images(folder):

    image_folder = Path(app.static_folder) / "images" / folder

    if not image_folder.exists():
        return []

    images = []

    for image in image_folder.iterdir():
        if image.is_file() and image.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS:
            images.append(image.name)

    return sorted(images, key=str.casefold)


# =====================================================
# ADMIN PRODUCT LIST (ACTIVE AND HIDDEN)
# =====================================================

def get_admin_products():

    connection = get_connection()

    try:
        return connection.execute("""
            SELECT *
            FROM products
            ORDER BY created_at DESC, id DESC
        """).fetchall()

    finally:
        connection.close()


# =====================================================
# REUSABLE CATEGORY PAGE
# =====================================================

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


# =====================================================
# SEARCH ENGINE
# =====================================================

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


# =====================================================
# HOMEPAGE
# =====================================================

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


# =====================================================
# SHOP PAGE
# =====================================================

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


# =====================================================
# CUSTOMER SEARCH
# =====================================================

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


# =====================================================
# INDIVIDUAL PRODUCT DETAILS
# =====================================================

@app.route("/product/<int:product_id>")
def product_detail(product_id):

    product = get_product_by_id(product_id)

    if product is None or not product["is_active"]:
        abort(404)

    return render_template(
    "product_detail.html",
    product=product,
    categories=CATEGORIES
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

        if admin and check_password_hash(admin["password_hash"], password):

            session.clear()
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["full_name"]

            flash("Welcome to your admin dashboard!", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Incorrect email or password.", "error")

    return render_template("admin_login.html")


# =====================================================
# ADMIN DASHBOARD
# =====================================================

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():

    products = get_admin_products()

    return render_template(
        "admin_dashboard.html",
        products=products,
        categories=CATEGORIES,
        admin_name=session.get("admin_name", "Administrator")
    )


# =====================================================
# ADD NEW PRODUCT
# =====================================================

@app.route("/admin/products/add", methods=["POST"])
@admin_required
def admin_add_product():

    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    category_name = request.form.get("category", "").strip()
    price_input = request.form.get("price", "").strip()
    stock_input = request.form.get("stock_quantity", "").strip()
    image = request.files.get("image")

    if not all([name, description, category_name, price_input, stock_input]):
        flash("Please complete all product fields.", "error")
        return redirect(url_for("admin_dashboard"))

    if category_name not in CATEGORIES:
        flash("Please select a valid product category.", "error")
        return redirect(url_for("admin_dashboard"))

    try:
        price = int(price_input)
        stock_quantity = int(stock_input)

        if price < 0 or stock_quantity < 0:
            raise ValueError

    except ValueError:
        flash("Price and stock quantity must be valid non-negative numbers.", "error")
        return redirect(url_for("admin_dashboard"))

    if not image or not image.filename:
        flash("Please select a product image.", "error")
        return redirect(url_for("admin_dashboard"))

    if not allowed_image(image.filename):
        flash("Unsupported image format. Use JPG, JPEG, PNG, WEBP, GIF or AVIF.", "error")
        return redirect(url_for("admin_dashboard"))

    category_folder = CATEGORIES[category_name]["folder"]
    image_directory = Path(app.static_folder) / "images" / category_folder
    image_directory.mkdir(parents=True, exist_ok=True)

    original_filename = secure_filename(image.filename)
    extension = Path(original_filename).suffix.lower()
    image_filename = f"{uuid.uuid4().hex}{extension}"
    image_path = image_directory / image_filename

    try:
        image.save(image_path)

        product_id = add_product(
            name,
            description,
            price,
            category_name,
            image_filename,
            stock_quantity
        )

    except Exception:
        if image_path.exists():
            image_path.unlink()
        raise

    flash(f"Product added successfully! Product ID: {product_id}", "success")
    return redirect(url_for("admin_dashboard"))


# =====================================================
# EDIT PRODUCT
# =====================================================

@app.route("/admin/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_product(product_id):

    product = get_product_by_id(product_id)

    if product is None:
        abort(404)

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        category_name = request.form.get("category", "").strip()
        price_input = request.form.get("price", "").strip()
        stock_input = request.form.get("stock_quantity", "").strip()
        new_image = request.files.get("image")

        if not all([name, description, category_name, price_input, stock_input]):
            flash("Please complete all product fields.", "error")
            return redirect(url_for("admin_edit_product", product_id=product_id))

        if category_name not in CATEGORIES:
            flash("Please select a valid category.", "error")
            return redirect(url_for("admin_edit_product", product_id=product_id))

        try:
            price = int(price_input)
            stock_quantity = int(stock_input)

            if price < 0 or stock_quantity < 0:
                raise ValueError

        except ValueError:
            flash("Price and stock must be non-negative whole numbers.", "error")
            return redirect(url_for("admin_edit_product", product_id=product_id))

        updates = {
            "name": name,
            "description": description,
            "category": category_name,
            "price": price,
            "stock_quantity": stock_quantity
        }

        old_category_folder = CATEGORIES.get(product["category"], {}).get("folder")
        old_image_filename = product["image_filename"]
        replacement_image_path = None
        replacement_image_filename = None

        if new_image and new_image.filename:

            if not allowed_image(new_image.filename):
                flash("Unsupported image format.", "error")
                return redirect(url_for("admin_edit_product", product_id=product_id))

            new_image_directory = (
                Path(app.static_folder)
                / "images"
                / CATEGORIES[category_name]["folder"]
            )
            new_image_directory.mkdir(parents=True, exist_ok=True)

            extension = Path(secure_filename(new_image.filename)).suffix.lower()
            replacement_image_filename = f"{uuid.uuid4().hex}{extension}"
            replacement_image_path = new_image_directory / replacement_image_filename

            try:
                new_image.save(replacement_image_path)
            except Exception:
                flash("Could not save the replacement image.", "error")
                return redirect(url_for("admin_edit_product", product_id=product_id))

            updates["image_filename"] = replacement_image_filename

        try:
            updated = update_product(product_id, **updates)

            if not updated:
                if replacement_image_path and replacement_image_path.exists():
                    replacement_image_path.unlink()
                flash("Product could not be updated.", "error")
                return redirect(url_for("admin_dashboard"))

        except Exception:
            if replacement_image_path and replacement_image_path.exists():
                replacement_image_path.unlink()
            raise

        # Remove the previous product image after a successful replacement.
        if replacement_image_filename and old_category_folder:
            old_image_path = (
                Path(app.static_folder)
                / "images"
                / old_category_folder
                / old_image_filename
            )
            if old_image_path.exists():
                try:
                    old_image_path.unlink()
                except OSError:
                    pass

        flash("Product updated successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template(
        "admin_edit_product.html",
        product=product,
        categories=CATEGORIES
    )


# =====================================================
# HIDE / REACTIVATE PRODUCT
# =====================================================

@app.route("/admin/products/<int:product_id>/toggle", methods=["POST"])
@admin_required
def admin_toggle_product(product_id):

    product = get_product_by_id(product_id)

    if product is None:
        abort(404)

    new_status = 0 if product["is_active"] else 1

    update_product(product_id, is_active=new_status)

    if new_status:
        flash("Product is now visible in the shop.", "success")
    else:
        flash("Product has been hidden from the shop.", "success")

    return redirect(url_for("admin_dashboard"))


# =====================================================
# DELETE PRODUCT
# =====================================================

@app.route("/admin/products/<int:product_id>/delete", methods=["GET", "POST"])
@admin_required
def admin_delete_product(product_id):

    product = get_product_by_id(product_id)

    if product is None:
        abort(404)

    if request.method == "POST":

        category_folder = CATEGORIES.get(product["category"], {}).get("folder")
        image_filename = product["image_filename"]

        deleted = delete_product(product_id)

        if not deleted:
            flash("Product could not be deleted.", "error")
            return redirect(url_for("admin_dashboard"))

        if category_folder and image_filename:
            image_path = (
                Path(app.static_folder)
                / "images"
                / category_folder
                / image_filename
            )

            if image_path.exists():
                try:
                    image_path.unlink()
                except OSError:
                    pass

        flash("Product deleted successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template(
        "admin_delete_product.html",
        product=product
    )


# =====================================================
# ADMIN LOGOUT
# =====================================================

@app.route("/admin/logout")
@admin_required
def admin_logout():

    session.clear()
    flash("You have logged out successfully.", "success")
    return redirect(url_for("admin_login"))


# =====================================================
# CATEGORY ROUTES
# =====================================================

@app.route("/clothing")
def clothing():
    return show_category("clothing")


@app.route("/gowns")
def gowns():
    return show_category("gowns")


@app.route("/handbags")
def handbags():
    return show_category("handbags")


@app.route("/crossbody-bags")
def crossbody_bags():
    return show_category("crossbody_bags")


@app.route("/necklaces")
def necklaces():
    return show_category("necklaces")


@app.route("/shoes")
def shoes():
    return show_category("shoes")


@app.route("/hair")
def hair():
    return show_category("hair")


@app.route("/watches")
def watches():
    return show_category("watches")


@app.route("/heels")
def heels():
    return show_category("heels")


@app.route("/category/<category_name>")
def category_page(category_name):
    return show_category(category_name)


# =====================================================
# CUSTOMER REGISTRATION / LOGIN PLACEHOLDERS
# =====================================================

@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/forgotten_password")
def forgotten_password():
    return render_template("forgotten.html")


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":
    app.run(debug=True)