from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

###  Models  ####

# ORDER_PRODUCT RELATIONAL TABLE
order_product = db.Table(
    'order_product',
    db.Column('order_id', db.Integer, db.ForeignKey('order.order_id')),
    db.Column('product_id', db.Integer, db.ForeignKey('product.product_id')),
    db.Column('quantity', db.Integer, nullable=False)
)



# CUSTOMER MODEL
class Customer(db.Model, UserMixin):
    __tablename__ = "customer"

    customer_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255), unique=False, nullable=False)
    last_name = db.Column(db.String(255), unique=False, nullable=False)
    username = db.Column(db.String(255), unique=True, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    hashed_password = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def create(self):
      db.session.add(self)
      db.session.commit()
      return self

    def to_dict(self):
      return {
        'first name': self.first_name,
        'last name': self.last_name,
        'username': self.username,
        'address': self. address,
        'email': self. email
      }

    @property
    def password(self):
        return self.hashed_password

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def get_id(self):
        return str(self.customer_id)


# PRODUCT MODEL
class Product(db.Model):
    __tablename__ = "product"
    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255))
    product_desc = db.Column(db.String(255))
    in_stock = db.Column(db.Integer, nullable=False )
    product_price = db.Column(db.Float, nullable=False )
    product_category = db.Column(db.String(255))
    product_brand = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime)

    def create(self):
      db.session.add(self)
      db.session.commit()
      return self

    def __repr__(self):
        return '' % self.id

# ORDER MODEL
class Order(db.Model):
    __tablename__ = "order"
    order_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.customer_id"))
    product_id = db.Column(db.Integer, db.ForeignKey("product.product_id"))
    customer = db.relationship("Customer", backref="orders")
    product = db.relationship("Product", backref="orders")

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self
    def __repr__(self):
        return '' % self.id

# REVIEW MODEL
class Review(db.Model):
    __tablename__ = "review"
    review_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.customer_id"))
    product_id = db.Column(db.Integer, db.ForeignKey("product.product_id"))
    rating = db.Column(db.Float)
    comment = db.Column(db.String(255))
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    customer = db.relationship("Customer", backref="customer_table")
    product = db.relationship("Product", backref="product_table")

    def create(self):
      db.session.add(self)
      db.session.commit()
      return self

    def __repr__(self):
        return '' % self.id
