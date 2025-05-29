import mongoengine as me
from faker import Faker
import random
from datetime import datetime, timedelta
import pyotp # For User model's set_password_reset_token, not directly used for seeding password
from werkzeug.security import generate_password_hash

# Import your models (adjust the path if your script is not in the root or app folder)
# Assuming your models are in app.models
from app.models import User, Shop, Product, Item, ProductPayload, Transaction, PasswordResetToken, Invitation

# --- Configuration ---
MONGODB_URI = "mongodb+srv://chapaeresso1:WV56PLhZwIIYkYQQ@stock-smart.irziv.mongodb.net/" # Replace with your MongoDB URI and DB name
DB_NAME = "stock-smart" # Replace with your database name

try:
    me.disconnect_all() # Disconnect all existing connections
except Exception as e:
    print(f"No existing connection to disconnect or error during disconnect: {e}")
    
# --- Connect to MongoDB ---
me.connect(db=DB_NAME, host=MONGODB_URI)

fake = Faker()

# --- Helper Functions ---
def clear_collections():
    """Clears all relevant collections. Use with caution!"""
    print("Clearing collections...")
    Item.objects.delete()
    Transaction.objects.delete()
    Product.objects.delete()
    User.objects.filter(role__in=["employee", "owner"]).delete() # Avoid deleting other user types if any
    Shop.objects.delete()
    PasswordResetToken.objects.delete()
    Invitation.objects.delete()
    print("Collections cleared.")

PRODUCT_CATEGORIES = ["Electronics", "Books", "Clothing", "Home Goods", "Groceries", "Cosmetics", "Toys", "Sports"]

def create_fake_user(role, shop_instance=None, shops_instances=None, password="password123"):
    user = User(
        name=fake.name(),
        email=fake.unique.email(),
        password=password, # Password will be hashed by the model's __init__
        role=role,
        isVerified=True
    )
    if role == "owner":
        if shops_instances:
            user.shops = shops_instances
    elif role == "employee":
        if shop_instance:
            user.shop = shop_instance
    user.save()
    return user

def create_fake_shop(owner_instance):
    shop = Shop(
        name=fake.company() + " Store",
        address=fake.address(),
        owner=owner_instance
    )
    shop.save()
    return shop

def create_fake_product(shop_instance, is_serialized):
    product = Product(
        name=fake.bs().capitalize() + " " + random.choice(["Gadget", "Tool", "Device", "Kit", "Set", "Apparel"]),
        shop=shop_instance,
        price=round(random.uniform(5.0, 500.0), 2),
        quantity=0, # Initial quantity is 0, will be updated by items or restock
        threshold=random.randint(5, 20),
        isSerialized=is_serialized,
        description=fake.sentence(nb_words=10),
        category=random.choice(PRODUCT_CATEGORIES),
        image_url=f"https://picsum.photos/seed/{fake.word()}/200/300" # Placeholder image
    )
    product.save()
    return product

def create_fake_item(product_instance):
    if not product_instance.isSerialized:
        print(f"Warning: Trying to create item for non-serialized product {product_instance.name}")
        return None
    item = Item(
        product=product_instance,
        barcode=fake.unique.ean13()
    )
    # The Item's save method should increment the product's quantity
    item.save()
    return item

def create_fake_transaction(shop_instance, user_instance):
    transaction_type = random.choice(["sale", "restock"])
    products_in_shop = list(Product.objects(shop=shop_instance))
    if not products_in_shop:
        return None

    num_products_in_transaction = random.randint(1, min(3, len(products_in_shop)))
    selected_products_for_payload = random.sample(products_in_shop, num_products_in_transaction)

    payload_items = []
    transaction_total = 0

    for prod in selected_products_for_payload:
        barcodes_for_payload = []
        if transaction_type == "sale":
            if prod.quantity <= 0:
                continue # Skip if no stock
            txn_quantity = random.randint(1, max(1, prod.quantity // 2 if prod.quantity > 1 else 1) ) # Sell up to half of stock

            if prod.isSerialized:
                items_to_sell = list(Item.objects(product=prod).limit(txn_quantity))
                if len(items_to_sell) < txn_quantity: # Not enough specific items
                    txn_quantity = len(items_to_sell)
                if not items_to_sell:
                    continue

                for item_to_sell in items_to_sell:
                    barcodes_for_payload.append(item_to_sell.barcode)
                    item_to_sell.delete() # This should decrement product.quantity
                # prod.reload() # Ensure quantity is updated if item.delete() doesn't do it immediately for the object in memory
            else:
                prod.quantity -= txn_quantity
                prod.save()

        elif transaction_type == "restock":
            txn_quantity = random.randint(5, 50)
            if prod.isSerialized:
                for _ in range(txn_quantity):
                    new_item = create_fake_item(prod) # This increments product.quantity
                    if new_item:
                        barcodes_for_payload.append(new_item.barcode)
                # prod.reload()
            else:
                prod.quantity += txn_quantity
                prod.save()
        
        if txn_quantity > 0:
            payload_item = ProductPayload(
                product_id=str(prod.id),
                name=prod.name,
                category=prod.category,
                quantity=txn_quantity,
                price=prod.price,
                isSerialized=prod.isSerialized,
                barcodes=barcodes_for_payload
            )
            payload_items.append(payload_item)
            transaction_total += prod.price * txn_quantity
            prod.reload() # get the latest quantity

    if not payload_items:
        return None # No valid items for transaction

    transaction = Transaction(
        shop=shop_instance,
        user=user_instance,
        transaction_type=transaction_type,
        payload=payload_items,
        total=round(transaction_total, 2),
        date=fake.date_time_between(start_date="-6m", end_date="now", tzinfo=None)
    )
    transaction.save()
    return transaction

# --- Main Seeding Logic ---
def seed_data():
    print("Starting data seeding...")

    # --- Create Owners and Shops ---
    num_owners = 2
    num_shops_per_owner = 1
    all_shops = []
    owner_users = []

    for i in range(num_owners):
        owner = create_fake_user(role="owner")
        owner_users.append(owner)
        owner_shops = []
        for j in range(num_shops_per_owner):
            shop = create_fake_shop(owner_instance=owner)
            all_shops.append(shop)
            owner_shops.append(shop)
        owner.shops = owner_shops # Assign shops to owner
        owner.save()
        print(f"Created Owner {owner.email} with {len(owner_shops)} shop(s).")

    # --- Create Employees ---
    num_employees_per_shop = 2
    employee_users = []
    for shop in all_shops:
        for _ in range(num_employees_per_shop):
            employee = create_fake_user(role="employee", shop_instance=shop)
            employee_users.append(employee)
        print(f"Created {num_employees_per_shop} employees for Shop {shop.name}.")
    
    all_users = owner_users + employee_users

    # --- Create Products and Items ---
    num_products_per_shop = 10 # 5 serialized, 5 non-serialized
    all_products = []

    for shop in all_shops:
        print(f"Creating products for Shop: {shop.name}")
        # Serialized products
        for _ in range(num_products_per_shop // 2):
            product = create_fake_product(shop_instance=shop, is_serialized=True)
            all_products.append(product)
            # Create initial stock of items for serialized products
            initial_item_stock = random.randint(5, 15)
            print(f"  Creating {initial_item_stock} items for serialized product: {product.name}")
            for _ in range(initial_item_stock):
                create_fake_item(product_instance=product)
            product.reload() # ensure quantity is updated
            print(f"  Product {product.name} (Serialized) created with {product.quantity} items.")

        # Non-serialized products
        for _ in range(num_products_per_shop // 2):
            product = create_fake_product(shop_instance=shop, is_serialized=False)
            # For non-serialized, initial quantity comes from a "restock" transaction later or set here
            product.quantity = random.randint(20, 100) # Initial stock for non-serialized
            product.save()
            all_products.append(product)
            print(f"  Product {product.name} (Non-Serialized) created with quantity {product.quantity}.")


    # --- Create Transactions ---
    num_transactions_total = 100 # Aim for roughly this many transactions
    created_transactions_count = 0
    print(f"\nCreating approximately {num_transactions_total} transactions...")

    for _ in range(num_transactions_total):
        if not all_shops or not all_users:
            print("No shops or users available to create transactions.")
            break
        
        target_shop = random.choice(all_shops)
        # Users associated with the shop or owners
        possible_users = [u for u in all_users if (u.role == "owner" and target_shop in u.shops) or (u.role == "employee" and u.shop == target_shop)]
        if not possible_users:
            # Fallback to any user if no specific user found (should not happen with current logic)
            possible_users = all_users 
        
        if not possible_users:
            print(f"No users available for shop {target_shop.name} to create transaction.")
            continue

        acting_user = random.choice(possible_users)
        
        txn = create_fake_transaction(shop_instance=target_shop, user_instance=acting_user)
        if txn:
            created_transactions_count +=1
            if created_transactions_count % 10 == 0:
                print(f"  Created {created_transactions_count} transactions...")
    
    print(f"\n--- Seeding Complete ---")
    print(f"Total Owners: {User.objects(role='owner').count()}")
    print(f"Total Employees: {User.objects(role='employee').count()}")
    print(f"Total Shops: {Shop.objects.count()}")
    print(f"Total Products: {Product.objects.count()}")
    print(f"Total Items (for serialized products): {Item.objects.count()}")
    print(f"Total Transactions: {Transaction.objects.count()}")

if __name__ == "__main__":
    # WARNING: This will clear data. Comment out if you want to append.
    # clear_collections() 
    
    seed_data()
    print("Fake data generation finished.")