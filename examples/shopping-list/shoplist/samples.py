"""Example dishes for a fresh install, so the app is not empty on first start."""

SAMPLE_DISHES = [
    {
        "name": "Spaghetti Bolognese",
        "servings": 4,
        "ingredients": [
            {"name": "Spaghetti", "amount": 500, "unit": "g", "category": "Vorrat"},
            {"name": "Hackfleisch", "amount": 400, "unit": "g", "category": "Fleisch & Fisch"},
            {"name": "Zwiebel", "amount": 1, "unit": "Stk", "category": "Obst & Gemüse"},
            {"name": "Knoblauchzehe", "amount": 2, "unit": "Stk", "category": "Obst & Gemüse"},
            {"name": "Passierte Tomaten", "amount": 500, "unit": "g", "category": "Vorrat"},
            {"name": "Parmesan", "amount": 50, "unit": "g", "category": "Kühlregal"},
            {"name": "Olivenöl", "amount": 2, "unit": "EL", "category": "Vorrat"},
        ],
    },
    {
        "name": "Gemüsecurry",
        "servings": 4,
        "ingredients": [
            {"name": "Süßkartoffel", "amount": 2, "unit": "Stk", "category": "Obst & Gemüse"},
            {"name": "Paprika", "amount": 1, "unit": "Stk", "category": "Obst & Gemüse"},
            {"name": "Zwiebel", "amount": 1, "unit": "Stk", "category": "Obst & Gemüse"},
            {"name": "Koriander", "amount": 1, "unit": "Bund", "category": "Obst & Gemüse"},
            {"name": "Kokosmilch", "amount": 400, "unit": "ml", "category": "Vorrat"},
            {"name": "Rote Currypaste", "amount": 2, "unit": "EL", "category": "Vorrat"},
            {"name": "Basmatireis", "amount": 300, "unit": "g", "category": "Vorrat"},
        ],
    },
    {
        "name": "Pfannkuchen",
        "servings": 2,
        "ingredients": [
            {"name": "Mehl", "amount": 250, "unit": "g", "category": "Vorrat"},
            {"name": "Milch", "amount": 500, "unit": "ml", "category": "Kühlregal"},
            {"name": "Eier", "amount": 3, "unit": "Stk", "category": "Kühlregal"},
            {"name": "Butter", "amount": 20, "unit": "g", "category": "Kühlregal"},
            {"name": "Salz", "amount": None, "unit": "", "category": "Vorrat"},
        ],
    },
]


def add_samples(dish_book):
    for dish in SAMPLE_DISHES:
        dish_book.create(dish["name"], dish["servings"], dish["ingredients"])
