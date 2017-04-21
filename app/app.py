from flask import Flask, render_template, request
from nutritionix import Nutritionix
import pandas as pd
import numpy as np


nix = Nutritionix(app_id='6fb672d6', api_key='7f302d3d7ef120d41979e92a6831e472')

app = Flask(__name__)

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html',
                           products = total_products(),
                           all_list = all_items_list(),
                           avgs = average_calories(),
                           index = index_ingredients(),
                           indexdf = ingredientsdf()
                           )

# REQUIREMENT 1: return total number of Juicy Juice products in JSON format.
def total_products():
    juice = nix.search().nxql(filters={'brand_id':'51db37d0176fe9790a899db2'}).json()
    total = (juice['total'])
    return total

def all_items_list():
    juicyjuice = nix.search().nxql(filters={'brand_id':'51db37d0176fe9790a899db2'},
                                    fields=['item_id',
                                            'item_name',
                                            'item_description',
                                            'nf_ingredient_statement',
                                            'nf_calories',
                                            'nf_serving_size_qty',
                                            'nf_serving_size_unit',
                                            'nf_servings_per_container']).json()
    allitems = []
    for hit in juicyjuice['hits']:
        individual_item = dict(
            _id = hit['fields']['item_id'],
            name = hit['fields']['item_name'],
            description = hit['fields']['item_description'],
            calories = hit['fields']['nf_calories'],
            calories_per_serv = ((hit['fields']['nf_calories'])/(hit['fields']['nf_serving_size_qty'])),
            ingredients = hit['fields']['nf_ingredient_statement'].split(','),
            serv_quant = hit['fields']['nf_serving_size_qty'],
            serv_unit = hit['fields']['nf_serving_size_unit'],
            container_serv = hit['fields']['nf_servings_per_container']
        )
        allitems.append(individual_item)
    return allitems

# REQUIREMENT 2: return avg. calories per fluid ounce in JSON format.
def average_calories():
    allitems = all_items_list()
    count = 0
    total_cal = 0
    for item in allitems:
        if (item['serv_unit'] == 'fl oz'):
            count = count + 1
            total_cal = total_cal + item['calories_per_serv']
    avg = (total_cal/count)
    return avg

def index_ingredients():
    items = all_items_list()
    all_ingredients = []
    for item in items:
        for i in item['ingredients']:
            each = dict(Product = item['name'],
                       Ingredient = i)
            all_ingredients.append(each)
    ingdf = pd.DataFrame(all_ingredients)
    ingdf['Ingredient']=ingdf['Ingredient'].str.replace('and', '')
    ingdf['Ingredient']=ingdf['Ingredient'].str.rstrip('.')
    ingdf2 = pd.DataFrame(ingdf.where(ingdf['Ingredient'].str.contains('Water'))).dropna()
    ingdf['Ingredient']=ingdf['Ingredient'].str.replace('Water','')
    ingdf2.reset_index(inplace=True)
    del ingdf2['index']
    del ingdf2['Ingredient']
    ingdf2.insert(0, 'Ingredient', 'Water')
    a = ingdf.append(ingdf2)
    a = a.applymap(lambda x: np.nan if isinstance(x, str) and x.isspace() else x)
    a = a.dropna()
    a.reset_index(inplace=True)
    del a['index']
    a['Ingredient'] = a['Ingredient'].str.replace('(','')
    a['Ingredient'] = a['Ingredient'].str.replace(')','')
    a['Ingredient'] = pd.Series(a['Ingredient']).str.strip()
    return a.to_html(index=False)

def ingredientsdf():
    items = all_items_list()
    all_ingredients = []
    for item in items:
        for i in item['ingredients']:
            each = dict(Product = item['name'],
                       Ingredient = i)
            all_ingredients.append(each)
    ingdf = pd.DataFrame(all_ingredients)
    ingdf['Ingredient']=ingdf['Ingredient'].str.replace('and', '')
    ingdf['Ingredient']=ingdf['Ingredient'].str.rstrip('.')
    ingdf2 = pd.DataFrame(ingdf.where(ingdf['Ingredient'].str.contains('Water'))).dropna()
    ingdf['Ingredient']=ingdf['Ingredient'].str.replace('Water','')
    ingdf2.reset_index(inplace=True)
    del ingdf2['index']
    del ingdf2['Ingredient']
    ingdf2.insert(0, 'Ingredient', 'Water')
    a = ingdf.append(ingdf2)
    a = a.applymap(lambda x: np.nan if isinstance(x, str) and x.isspace() else x)
    a = a.dropna()
    a.reset_index(inplace=True)
    del a['index']
    a['Ingredient'] = a['Ingredient'].str.replace('(','')
    a['Ingredient'] = a['Ingredient'].str.replace(')','')
    a['Ingredient'] = pd.Series(a['Ingredient']).str.strip()
    return a

def search(a, ingred):
    bools = []
    for element in a['Ingredient']:
        if element == ingred:
            bools.append(True)
        else:
            bools.append(False)
    return pd.DataFrame(a['Product'][bools].unique())

@app.route('/select', methods=['POST'])
def select():
    a = ingredientsdf()
    ing = request.form['Ingredient']
    ing = str(ing)
    if ing != '':
        a = search(a, ing)
    a.columns = ['Product']
    return a.to_html(index=False)


if __name__ == '__main__':
    app.run(port=5000, debug=True)

