from flask import Flask, render_template,request,redirect,url_for,flash
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config["SECRET_KEY"] = "4766539ea38fd12b0f01bccbd9dd7075"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///C:\\Users\\Dom\\PycharmProjects\\lesson1\\warehouse\\database.db"
db = SQLAlchemy(app)
total_price = 0
class Products(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String)
    price = db.Column(db.Integer)
    count = db.Column(db.Integer)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    balance = db.Column(db.Float)

class History(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    record = db.Column(db.String)

with app.app_context():
    db.create_all()

@app.route("/", methods = ['GET','POST'])
def index_view():
    account = Account.query.first()
    balance = account.balance if account else 0.0
    if request.method == 'POST':
        product_to_search = request.form.get('search')
        existing_product_to_search = Products.query.filter(Products.name == product_to_search ).first()
        if existing_product_to_search:
            return redirect(url_for('products_view'))
        else:
            flash('product cannot be found in inventory', category= 'warning')
    return render_template('index.html',balance = balance)

#Adding values entered by user to database.
@app.route("/purchase", methods = ["GET", "POST"])
def purchase_view():
    if request.method == 'POST': #to specify which method is running
        product_name = request.form.get("product_name")
        product_price = request.form.get("product_price",0) #to avoid none type error
        product_quantity = request.form.get("quantity",0)
        try:
            product_price = float(product_price)
            product_quantity = int(product_quantity)
        except ValueError:
            return "invalid input: Price must be a number and quantity must be an integer", 400

        existing_product = Products.query.filter(Products.name == product_name).first()
        if  existing_product:
            existing_product.price = (existing_product.price or 0) + product_price #to avoid none type error.
            existing_product.count = (existing_product.count or 0) + product_quantity
            total_price = product_price * product_quantity
            message_to_add = f"user purchased {product_quantity} new items of {product_name}"
            history1= History(record = message_to_add)
            db.session.add(history1)
        else:
            product = Products(name = product_name,price = product_price,count = product_quantity)
            total_price = product.price * product.count
            message_to_add = f"the newly added product is {product_name} with quantity of {product_quantity} and price of {product_price} "
            history1=History(record=message_to_add)
            db.session.add(history1)
            db.session.add(product)
        account = Account.query.first()
        if not account.balance <=0 and account.balance>=total_price:
            account.balance-=total_price
            flash(f"product has been Purchased succesfully,  {total_price} have been deducted from your account")
        else:
            flash("Insufficient balance, please refund your account", category= 'warning')
        db.session.commit()

        return redirect(url_for('purchase_view'))

    return render_template('purchase.html')
@app.route("/sale", methods=['GET','POST'])
def sale_view():
    if request.method == 'POST':
        product_name_for_sale = request.form.get('product_name')
        product_price_for_sale = request.form.get('product_price')
        product_quantity_for_sale = request.form.get('product_quantity')

        try:
            # Convert the value to an integer
            product_price_for_sale = int(product_price_for_sale)
            product_quantity_for_sale = int(product_quantity_for_sale)
            existing_product = Products.query.filter(Products.name == product_name_for_sale).first()
            account = Account.query.first()
            if not existing_product:
                flash(f"{product_name_for_sale} cannot be found , Please choose a product that exists in the warehouse",
                      category='warning')

            else:
                if existing_product.count >= product_quantity_for_sale:
                    existing_product.count -= product_quantity_for_sale
                    total_sale = product_quantity_for_sale * product_price_for_sale
                    total_sale = int(total_sale)
                    account.balance += total_sale
                    flash(f"the number of {product_name_for_sale} sold is "
                          f"{product_quantity_for_sale} and {total_sale} were added to your balance"
                          f"with new value of {account.balance}")
                    message_to_add = f"user has sold {product_name_for_sale} of quantity {product_quantity_for_sale}"
                    history1 = History(record = message_to_add)
                    db.session.add(history1)
                    if existing_product.count == 0:
                        db.session.delete(existing_product)
                elif existing_product.count < product_quantity_for_sale:
                    flash("you do not have enough items of that product in your warehouse", category='warning')

            db.session.commit()

        except ValueError:
            return "Invalid input: value must be a number.", 400
    return render_template('sale.html')

@app.route("/balance", methods = ['GET','POST'])
def balance_view():
    if request.method == 'POST':
        value_entered = request.form.get('value')
        operation = request.form.get ('operation')
        # Check if the value is None or empty, handle this case
        # if not value_entered:
        #     return "Error: Value is required.", 400  # Return a 400 error with a message

        try:
            # Convert the value to an integer
            value_entered = int(value_entered)

            account = Account.query.first() #retrieve the first account table in the database.
            if not account: #checks if there is no account in the database
                account = Account(balance=0) #if no account create a new one with default value = 0
                db.session.add(account) #the value of the account to the session.
            if operation == 'add':
                account.balance+=value_entered
                  # save all the changes to the database
                message_to_add = f"User added {value_entered} to the account"
                history1=History(record=message_to_add)
                db.session.add(history1)
                db.session.commit()
                flash(f"balance updated, {account.balance}$ added")
                return redirect(url_for('index_view'))
                  # redirect user to index page after updating account balance
            elif operation == 'subtract':
                if not account.balance<=0 and account.balance>=value_entered:
                    account.balance -= value_entered
                    message_to_add = f"The amount of {value_entered} has been deducted from balance"
                    history1 = History(record = message_to_add)
                    db.session.add(history1)
                    db.session.commit()
                    flash(f"balance updated, {value_entered}$ were deducted from account")
                    return redirect(url_for('index_view'))
                else:
                    flash("insufficient balance, please refund your account",category='warning')

        except ValueError:
            return "Invalid input: value must be a number.", 400
    return render_template('balance.html')

@app.route("/listing",methods =['GET','POST'])
def products_view():
    products_from_database = Products.query.all()
    return render_template('products.html',available_products=products_from_database)

@app.route('/history')
def history_view():
    actions = History.query.all()
    return render_template('history.html',actions = actions)








