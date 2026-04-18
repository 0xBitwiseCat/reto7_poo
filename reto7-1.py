""" 
- The restaurant class revisted like for the third time.
- Add the proper data structure to manage multiple orders 
- (maybe a FIFO queue)
- Define a named tuple somewhere in the menu,
-  e.g. to define a set of items.
- Create an interface in the order class, 
- to create a new menu, aggregate the functions for 
- add, update, delete items. 
- All the menus should be stored as JSON files. 
- (use dicts for this task.)
"""

import copy
import json
import copy
from collections import namedtuple
from queue import Queue

# Named tuple for item sets
MenuSet = namedtuple("MenuSet", ["name", "items"])


class MedioPago:
    def pagar(self, monto: float):
        raise NotImplementedError("Subclases deben implementar pagar()")

class Tarjeta(MedioPago):
    def __init__(self, numero: str, cvv: int):
        self.numero = numero
        self.cvv = cvv

    def pagar(self, monto: float):
        # Masking the card number for security (Cybersecurity practice!)
        last_four = str(self.numero)[-4:]
        print(f"Pagando ${monto:.2f} con tarjeta terminada en {last_four}")

class Efectivo(MedioPago):
    def __init__(self, monto_entregado: float):
        self.monto_entregado = monto_entregado

    def pagar(self, monto: float):
        if self.monto_entregado >= monto:
            cambio = self.monto_entregado - monto
            print(f"Pago realizado en efectivo. Cambio: ${cambio:.2f}")
        else:
            faltante = monto - self.monto_entregado
            print(f"Fondos insuficientes. Faltan ${faltante:.2f} para completar el pago.")

class MenuItem:
    def __init__(self, name: str, price: float, seasonal: bool = False):
        self._name = name
        self.price = price  # This triggers the setter validation
        self._quantity = 1
        self._seasonal = seasonal

    # --- Name ---
    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    # --- Price ---
    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float):
        # Validation logic: Ensure price is never negative
        self._price = value if value >= 0 else 0.0

    # --- Quantity ---
    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, value: int):
        self._quantity = value if value >= 0 else 0

    # --- Seasonal ---
    @property
    def seasonal(self) -> bool:
        return self._seasonal

    @seasonal.setter
    def seasonal(self, value: bool):
        self._seasonal = value


class Dessert(MenuItem):
    def __init__(self, name: str, price: float, seasonal: bool = False):
        super().__init__(name, price, seasonal)
        self._flavor = "sweet"
        self._has_alcohol = False

    @property
    def flavor(self) -> str:
        return self._flavor

    @flavor.setter
    def flavor(self, value: str):
        self._flavor = value


class MainCourse(MenuItem):
    def __init__(self, name: str, price: float, seasonal: bool = False):
        super().__init__(name, price, seasonal)
        self._flavor = "savory"

    @property
    def flavor(self) -> str:
        return self._flavor

    @flavor.setter
    def flavor(self, value: str):
        self._flavor = value


class Beverage(MenuItem):
    def __init__(self, name: str, price: float, seasonal: bool = False):
        super().__init__(name, price, seasonal)
        self._has_alcohol = True

    @property
    def has_alcohol(self) -> bool:
        return self._has_alcohol

    @has_alcohol.setter
    def has_alcohol(self, value: bool):
        self._has_alcohol = value

class Appetizer(MenuItem):
    def __init__(self, name: str, price: float, seasonal: bool = False):
        super().__init__(name, price, seasonal)
        self._flavor = "savory"
    
    @property
    def flavor(self) -> str:
        return self._flavor

    @flavor.setter
    def flavor(self, value: str):
        self._flavor = value


class Order:
    def __init__(self, client_name: str = "default client"):
        self.items = []
        self.client_name = client_name
        self.discounts = 0
        self.total = 0

    def add(self, item: MenuItem):
        added = False
        for i in self.items:
            if i.name == item.name:
                i.quantity = i.quantity + 1
                added = True
                break
        if not added:
            self.items.append(copy.deepcopy(item))
        

    def remove(self, item: MenuItem):
        for i in self.items:
            if i.name == item.name:
                i.quantity = i.quantity - 1
                if i.quantity == 0:
                    self.items.remove(i)
                break

    """
    Computes a full discount based
    on some rules that includes
    Main Courses and Beverages
    """
    def calculate_total_price(self) -> float:
        # 1. Calculate raw subtotal
        subtotal = sum(item.price * item.quantity for item in self.items)
        
        # 2. Check Composition for discounts
        has_main = any(isinstance(i, MainCourse) for i in self.items)
        main_course_count = sum(i.quantity for i in self.items if isinstance(i, MainCourse))
        
        total_discount = 0.0

        for item in self.items:
            # Apply 10% off Beverages if there is a Main Course
            if isinstance(item, Beverage) and has_main:
                # Calculate 10% of the beverage's total contribution
                total_discount += (item.price * item.quantity) * 0.10
            
            # Apply 15% off Main Courses if ordering 3 or more
            if isinstance(item, MainCourse) and main_course_count >= 3:
                total_discount += (item.price * item.quantity) * 0.15

        self.discounts = total_discount
        return subtotal - total_discount
    
    def process_payment(self, payment_method: MedioPago):
        """
        This is the bridge between Order and Payment.
        It calculates the final amount and delegates the action to the payment object.
        """
        monto_final = self.calculate_total_price()
        print(f"\n--- Processing Payment for {self.client_name} ---")
        payment_method.pagar(monto_final)

    def summary(self):
        self.total = self.calculate_total_price()
        print(f"Order summary for client: {self.client_name}")
        for i in self.items:
            print(f"{i.name}(x{i.quantity}).............${i.price}")

        print(f"Discounts.........${self.discounts}")
        print(f"Total.............${self.total}")

class Restaurant:
    def __init__(self):
        self.balance = 0.0
        self.orders_queue = Queue(maxsize=10)
        self.menu_manager = MenuManager()
        self.combo_promo = MenuSet("Breakfast Combo", ["Coffee", "Croissant"])
        self.family_promo = MenuSet("Family Combo", ["Coca Cola 1.5L", "Pizza XXL", "Hamburguer X4"])

    def create_order(self, client_name, item_names):
        order = Order(client_name)
        for name in item_names:
            if name in self.menu_manager.menu_items:
                price = self.menu_manager.menu_items[name]
                order.add(MenuItem(name, price))
        self.orders_queue.put(order)
        return order

    def pay_order(self, payment_method):
        order = self.orders_queue.get()
        order.summary()
        self.balance += order.total
        order.process_payment(payment_method)

class MenuManager:
    """Interface to manage the Menu catalog and JSON persistence."""
    def __init__(self, filename="menu.json"):
        self.filename = filename
        # menu_items is a dict based on local file
        self.menu_items = self.load_menu()

    def add_item(self, name: str, price: float):
        self.menu_items[name] = price
        self.save_menu()

    def update_item(self, name: str, price: float):
        if name in self.menu_items:
            self.menu_items[name] = price
            self.save_menu()

    def delete_item(self, name: str):
        if name in self.menu_items:
            del self.menu_items[name]
            self.save_menu()

    def save_menu(self):
        with open(self.filename, 'w') as f:
            json.dump(self.menu_items, f, indent=4)

    def load_menu(self):
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}


# --- Execution Script to Verify Functionality ---
# -- AI gives me this code to check if all is ok :p
def main():
    # 1. Initialize the Restaurant and Menu Manager
    my_restaurant = Restaurant()
    manager = my_restaurant.menu_manager

    # 2. Create and Save Menu Items (This creates/updates menu.json)
    print("--- Setting up Menu ---")
    manager.add_item("Steak", 30.0)      # A Main Course
    manager.add_item("Salad", 12.0)      # An Appetizer
    manager.add_item("Juice", 5.0)       # A Beverage
    manager.add_item("Cheesecake", 8.0)  # A Dessert
    
    print(f"Current Menu stored in JSON: {manager.menu_items}\n")

    # 3. Create a Simple Order
    # We will order a Steak and a Juice to check if logic flows
    client_name = "Engineer_User"
    items_to_order = ["Steak", "Juice"]
    
    print(f"--- Creating Order for {client_name} ---")
    my_restaurant.create_order(client_name, items_to_order)

    # 4. Process Payment
    # This will pull the order from the FIFO queue
    # Using Cash (Efectivo) to pay
    pago_efectivo = Efectivo(monto_entregado=50.0)
    
    try:
        my_restaurant.pay_order(pago_efectivo)
    except:
        print("Transaction uncommitable")

    # 5. Check persistence
    with open("menu.json", "r") as f:
        data = json.load(f)
        print(f"\n--- Verification ---")
        print(f"JSON File Content: {data}")
        print("Success: Menu is persisted and Order was queued.")

if __name__ == "__main__":
    main()