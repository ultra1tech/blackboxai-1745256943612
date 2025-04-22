from database import SessionLocal
import models

def seed_categories():
    db = SessionLocal()
    try:
        # Check if categories already exist
        if db.query(models.Category).first():
            print("Categories already exist, skipping seeding...")
            return

        # Create main categories
        categories = [
            {"name": "Fashion", "description": "Clothing, shoes, and accessories"},
            {"name": "Home Decor", "description": "Furniture, art, and home accessories"},
            {"name": "Electronics", "description": "Gadgets, devices, and accessories"},
            {"name": "Books", "description": "Books, magazines, and publications"},
            {"name": "Handmade", "description": "Handcrafted items and artisanal products"},
            {"name": "Local Foods", "description": "Regional and specialty food items"},
            {"name": "Beauty", "description": "Cosmetics, skincare, and beauty products"},
            {"name": "Sports", "description": "Sports equipment and athletic gear"}
        ]

        for category_data in categories:
            category = models.Category(**category_data)
            db.add(category)
            print(f"Added category: {category_data['name']}")

        # Create some subcategories for Fashion
        fashion = db.query(models.Category).filter(models.Category.name == "Fashion").first()
        if fashion:
            fashion_subcategories = [
                {"name": "Men's Clothing", "description": "Men's apparel", "parent_id": fashion.id},
                {"name": "Women's Clothing", "description": "Women's apparel", "parent_id": fashion.id},
                {"name": "Accessories", "description": "Fashion accessories", "parent_id": fashion.id},
                {"name": "Shoes", "description": "Footwear", "parent_id": fashion.id}
            ]
            
            for subcat_data in fashion_subcategories:
                subcat = models.Category(**subcat_data)
                db.add(subcat)
                print(f"Added subcategory: {subcat_data['name']}")

        db.commit()
        print("Categories seeded successfully!")

    except Exception as e:
        print(f"Error seeding categories: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_categories()
