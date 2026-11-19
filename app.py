from pathlib import Path

from flask import Flask, render_template, abort


app = Flask(__name__)


# All product categories and their image folders
CATEGORIES = {
    "clothing": {
        "title": "Our Clothing Collection",
        "description": (
            "Explore stylish clothing designed "
            "to bring out your elegance."
        ),
        "folder": "clothing"
    },

    "gowns": {
        "title": "Beautiful Gowns",
        "description": (
            "Discover elegant gowns for every occasion. "
            "Find your perfect style at Grace Luxury."
        ),
        "folder": "gowns"
    },

    "handbags": {
        "title": "Beautiful Handbags",
        "description": (
            "Explore our collection of beautiful and "
            "elegant handbags."
        ),
        "folder": "handbags"
    },

    "necklaces": {
        "title": "Necklaces & Jewellery",
        "description": (
            "Discover beautiful necklaces and elegant "
            "jewellery that add luxury to every outfit."
        ),
        "folder": "necklaces"
    }
}


# Image formats the website can display
ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".avif"
}


# Read all images inside a category folder
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


# Reusable function for displaying category pages
def show_category(category_name):

    category = CATEGORIES.get(category_name)

    if category is None:
        abort(404)

    images = get_category_images(category["folder"])

    return render_template(
        "category.html",
        category=category,
        images=images
    )


# HOMEPAGE
@app.route("/")
def home():
    return render_template("home.html")


# CLOTHING COLLECTION
@app.route("/store")
def store():
    return show_category("clothing")


# GOWNS COLLECTION
@app.route("/gowns")
def gowns():
    return show_category("gowns")


# HANDBAGS COLLECTION
@app.route("/handbags")
def handbags():
    return show_category("handbags")


# NECKLACES AND JEWELLERY COLLECTION
@app.route("/necklaces")
def necklaces():
    return show_category("necklaces")


# FUTURE CATEGORY PAGES
@app.route("/category/<category_name>")
def category_page(category_name):
    return show_category(category_name)


# REGISTRATION
@app.route("/register")
def register():
    return render_template("register.html")


# LOGIN
@app.route("/login")
def login():
    return render_template("login.html")


# FORGOTTEN PASSWORD
@app.route("/forgotten_password")
def forgotten_password():
    return render_template("forgotten.html")


if __name__ == "__main__":
    app.run(debug=True)