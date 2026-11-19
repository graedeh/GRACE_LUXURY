from pathlib import Path

from flask import Flask, render_template, abort


app = Flask(__name__)


# ALL PRODUCT CATEGORIES
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
    },

    "shoes": {
        "title": "Beautiful Shoes",
        "description": (
            "Discover elegant heels, sneakers, canvas shoes "
            "and fashionable footwear for every occasion."
        ),
        "folder": "shoes"
    },

    "hair": {
        "title": "Wigs & Human Hair",
        "description": (
            "Discover beautiful bone straight, pixie curls, "
            "frontal wigs, closure wigs and luxurious "
            "human hair collections."
        ),
        "folder": "hair"
    },

    "watches": {
        "title": "Elegant Wristwatches",
        "description": (
            "Explore our collection of elegant and stylish "
            "wristwatches for every occasion."
        ),
        "folder": "watches"
    },

    "heels": {
        "title": "Beautiful Heels",
        "description": (
            "Discover elegant heels for special occasions, "
            "parties, celebrations and everyday style."
        ),
        "folder": "heels"
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

    return render_template(
        "category.html",
        category=category,
        images=images
    )


# HOMEPAGE
@app.route("/")
def home():

    shoes_images = get_category_images("shoes")
    hair_images = get_category_images("hair")
    watches_images = get_category_images("watches")
    heels_images = get_category_images("heels")

    return render_template(
        "home.html",
        shoes_images=shoes_images,
        hair_images=hair_images,
        watches_images=watches_images,
        heels_images=heels_images
    )


# ALL PRODUCTS / SHOP PAGE
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

    return render_template(
        "store.html",
        categories=category_cards
    )


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