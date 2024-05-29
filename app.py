from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from sqlalchemy import desc, or_
from model import db, Customer, Product, Order, Review, order_product
import datetime
import secrets
from sqlalchemy import or_
from flask_login import login_user, login_manager, current_user, LoginManager, login_required
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///product_retail.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#app.config['WTF_CSRF_SECRET_KEY'] = secrets.token_hex(16)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

with app.app_context():
    db.create_all()

#LOGIN/MAIN

@login_manager.user_loader
def load_user(user_id):
    # Load the user object from the database based on the user_id
    return Customer.query.get(int(user_id))


@app.route('/')
def landing_page():
    return render_template('landing.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/signup/success', methods=['POST'])
def signup_success():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    username = request.form['username']
    address = request.form['address']
    email = request.form['email']
    hashed_password = request.form['hashed_password']

    # Generate the hashed password
    hashed_password = generate_password_hash(hashed_password)

    customer = Customer(
        first_name=first_name,
        last_name=last_name,
        username=username,
        address=address,
        email=email,
        hashed_password=hashed_password,
    )
    db.session.add(customer)
    db.session.commit()

    # Retrieve the success message from the form data
    success_message = request.form.get('success_message2')

    return render_template('signup_success.html', success_message=success_message)


@app.route('/signup', methods=['GET', 'POST'])
def render_signup_form():
    if request.method == 'POST':
        return signup_success()
    else:
        return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Retrieve the user from the database based on the email
        user = Customer.query.filter_by(email=email).first()
        if user and user.password == password:
            # Store user session
            session['user_id'] = user.id

            # Redirect the user to the dashboard or home page
            return redirect(url_for('dashboard'))
        if user and check_password_hash(user.password, password):
            # If the user exists and the password matches, log the user in
            login_user(user)

            # Redirect to the next page if available, or the dashboard/home page
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                return redirect('/dashboard')
        else:
            # If authentication fails, show an error message
            return render_template('login.html', error='Invalid email or password')

    return render_template('login.html')


@app.route('/logout', methods=['POST'])
def logout():
    # Clear the session data
    session.clear()

    # Redirect the user to the login page
    return redirect(url_for('login'))

#CUSTOMER
@app.route('/dashboard/customer')
@login_required
def customer():
    customers = Customer.query.all()
    customer_dict = {'customers': [customer.to_dict() for customer in customers]}
    return customer_dict

@app.route('/dashboard/customer/<int:id>/')
@login_required
def customer_home(id):
    customers = Customer.query.all()
    return 'customer id route'

#REVIEW

#review landing page/how-to
@app.route('/dashboard/reviews/')
@login_required
def reviews():
    return render_template('reviews.html')

#add
@app.route('/dashboard/reviews/added', methods=['POST'])
@login_required
def create_review():
    customer_id = request.form['customer_id']
    product_id = request.form['product_id']
    rating = request.form['rating']
    comment = request.form['comment']
    created_at = datetime.datetime.now()

    review = Review(
        
        customer_id=customer_id,
        product_id=product_id,
        rating=rating,
        comment=comment,
        created_at=created_at
    )
    db.session.add(review)
    db.session.commit()

    # Retrieve the success message from the form data
    success_message = request.form.get('success_message')

    return render_template('review_created.html', success_message=success_message)


@app.route('/dashboard/reviews/add', methods=['GET', 'POST'])
@login_required
def render_add_review_form():
    if request.method == 'POST':
        return create_review()
    else:
        return render_template('add_review.html')

# viewing all customer reviews
@app.route('/dashboard/reviews/view', methods=['GET'])
@login_required
def view_reviews():
    reviews = Review.query.all()
    review_list = []
    for review in reviews:
        review_data = {
            'review_id': review.review_id,
            'customer_id': review.customer_id,
            'product_id': review.product_id,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at
        }
        review_list.append(review_data)
    
    return jsonify({'reviews': review_list}), 200

@app.route('/dashboard/reviews/search', methods=['GET'])
@login_required
def search_reviews():
    search_query = request.args.get('q', '') 
    results = Review.query.filter(or_(Review.customer.has(Customer.username.ilike(f'%{search_query}%')),
                                      Review.product.has(Product.product_name.ilike(f'%{search_query}%')))).all()
    
    serialized_results = [{'review_id': result.review_id,
                       'customer_id': result.customer_id,
                       'product_id': result.product_id,
                       'rating': result.rating,
                       'comment': result.comment,
                       'created_at': result.created_at,
                       'updated_at': result.updated_at} for result in results]
    
    return jsonify(serialized_results)

# Update a review record
@app.route('/dashboard/reviews/<int:review_id>', methods=['PUT'])
@login_required
def update_review(review_id):
    # Retrieve the review from the database
    review = Review.query.get(review_id)
    if not review:
        return jsonify({'message': 'Review not found'}), 404

    # Update the review attributes based on the request data
    data = request.get_json()
    if 'rating' in data:
        review.rating = data['rating']
    if 'comment' in data:
        review.comment = data['comment']
    if 'customer_id' in data:
        review.customer_id = data['customer_id']
    if 'product_id' in data:
        review.product_id = data['product_id']
    review.updated_at = datetime.datetime.now()
    
    # Save the changes to the database
    try:
        db.session.commit()
        return jsonify({'message': 'Review updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error updating review', 'error': str(e)}), 500

#PRODUCTS

#product landing page/how-to
@app.route('/dashboard/products/')
@login_required
def products():
    return render_template('products.html')

@app.route('/dashboard/products/view')
@login_required
def view_products():
    return render_template('view_products.html')

@app.route('/dashboard/products/view/search')
@login_required
def search_product():
    return render_template('search_product.html')

# Update a product record
@app.route('/dashboard/products/update', methods=['GET', 'POST'])
@login_required
def render_update_product_form():
    success_message = None

    if request.method == 'POST':
        # Process the form data and update the product in the database
        # ...

        # Set the success message
        success_message = 'Product updated successfully'

        # Redirect back to the update page
        return redirect('/products/update')

    return render_template('update_product.html', success_message=success_message)

@app.route('/dashboard/products/delete', methods=['GET', 'DELETE', 'POST'])
@login_required
def render_delete_product():
    return render_template('delete_product.html')

#add
@app.route('/dashboard/products/added', methods=['POST'])
@login_required
def create_product():
    product_name = request.form['product_name']
    product_desc = request.form['product_desc']
    in_stock = request.form['in_stock']
    product_price = request.form['product_price']
    product_category = request.form['product_category']
    product_brand = request.form['product_brand']
    updated_at = datetime.datetime.now()

    product = Product(
        
        product_name=product_name,
        product_desc=product_desc,
        in_stock=in_stock,
        product_price=product_price,
        product_category=product_category,
        product_brand=product_brand,
        updated_at=updated_at
    )
    db.session.add(product)
    db.session.commit()

    # Retrieve the success message from the form data
    success_message = request.form.get('success_message')

    return render_template('product_created.html', success_message=success_message)


@app.route('/dashboard/products/add', methods=['GET', 'POST'])
@login_required
def render_add_product_form():
    if request.method == 'POST':
        return create_product()
    else:
        return render_template('add_product.html')

#View products
@app.route('/dashboard/products/view/sortby=<string:category>/', methods=['GET'])
@login_required
def product_sort(category):

    match(category):
        case "id":
            results = db.session.execute(db.select(Product).order_by( desc("product_id"))).scalars()
            
        case "stock":
            results = db.session.execute(db.select(Product).order_by( desc("in_stock"))).scalars()
            
        case "price":
            results = db.session.execute(db.select(Product).order_by( desc("product_price"))).scalars()

        case _ :
            return "invalid query!"
        
    # Serialize the results into a list of dictionaries
    serialized_results = [{'product_id': result.product_id,
                           'product_name': result.product_name,
                           'in_stock': result.in_stock,
                           'product_price': result.product_price,
                           'product_desc' : result.product_desc,
                           'product_category': result.product_category,
                           'product_brand': result.product_brand,
                           'updated_at': result.updated_at} for result in results]

    return render_template('product_sort.html', products=serialized_results)

#search products
@app.route('/dashboard/products/view/search/display', methods=['GET'])
@login_required
def search_products():
    # Get the search query from the request parameters
    search_query = request.args.get('q', '')

    # Perform the search query on the Product model
    products = Product.query.filter(
        or_(
            Product.product_name.ilike(f'%{search_query}%'),
            Product.product_desc.ilike(f'%{search_query}%'),
            Product.product_category.ilike(f'%{search_query}%'),
            Product.product_brand.ilike(f'%{search_query}%')
        )
    ).all()

    # Serialize the products into a JSON response
    product_list = []
    for product in products:
        product_data = {
            'product_id': product.product_id,
            'product_name': product.product_name,
            'product_desc': product.product_desc,
            'in_stock': product.in_stock,
            'product_price': product.product_price,
            'product_category': product.product_category,
            'product_brand': product.product_brand,
            'updated_at': product.updated_at
        }
        product_list.append(product_data)

    return jsonify({'products': product_list})


# Update a product record
@app.route('/dashboard/products/update/updating', methods=['POST'])
@login_required
def update_product():
    # Retrieve the product ID from the request data
    product_id = request.form.get('product_id')
    
    # Retrieve the product from the database
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    # Update the product attributes based on the request data
    product.product_name = request.form.get('product_name')
    product.product_desc = request.form.get('product_desc')
    product.in_stock = request.form.get('in_stock')
    product.product_price = request.form.get('product_price')
    product.product_category = request.form.get('product_category')
    product.product_brand = request.form.get('product_brand')
    product.updated_at = datetime.datetime.now()
        
     # Save the changes to the database
    try:
        
        db.session.commit()
        return redirect(url_for('update_success'))
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error updating product', 'error': str(e)}), 500

@app.route('/dashboard/products/update/success')
@login_required
def update_success():
    return render_template('update_success.html')


@app.route('/dashboard/products/delete/deleting', methods=['DELETE', 'POST'])
@login_required
def delete_product():
    # Retrieve the product ID from the request data
    product_id = request.form.get('product_id')

    # Retrieve the product from the database
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    # Delete the product from the database
    db.session.delete(product)
    db.session.commit()

    return redirect(url_for('delete_success'))

@app.route('/dashboard/products/delete/success')
@login_required
def delete_success():
    return render_template('delete_success.html')


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)