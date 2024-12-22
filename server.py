import auto.autoguit
import database.initializeDatabase as IDB   

from time                            import sleep
from flask                           import Flask, request, jsonify,render_template,redirect
from waitress                        import serve
from flask_cors                      import CORS
import hashlib
import mysql.connector
import traceback

mydb = mysql.connector.connect(
host="localhost",
user="root",
password="1234",
database= IDB.nameBanco
)
db = mydb.cursor()

app = Flask(__name__)
CORS(app)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


#-------------------------------------------------------------------------
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name     = data.get('name')
    email    = data.get('email')
    vendedor = data.get('isSeller')
    cpf_cnpj = data.get('cpfCnpj')
    password = data.get('password')

    if vendedor:
        vendedor = "V"
    else:
        vendedor ="C"
    db.execute("SELECT email FROM users WHERE email =%s",(email,))
    result = db.fetchall()
    if result:
        return jsonify({'message': 'Usuário já existe!'}), 400
    
    hash = hash_password(email+password)
    db.execute("INSERT INTO users (name, email,vendedor,cpf_cnpj,password) VALUES (%s,%s,%s,%s,%s)",
               (name, email,vendedor,cpf_cnpj,hash))
    mydb.commit()
    return jsonify({'data':hash}), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    tokey = data.get('tokey')
    email = data.get('email')
    password = data.get('password')
    #print('tokey login:',tokey)
    mydb.commit()
    db.execute("SELECT name,email,vendedor,cpf_cnpj,password FROM users WHERE password = %s", (tokey,))
    result = db.fetchall()
    #print('result login  t:',result)
    if result:
        result = result[0]
        data ={'name': result[0], 'email': result[1],'vendedor':result[2],'cpfCnpj':result[3],'password':result[4]}
        return jsonify(data), 200
    
    db.execute("SELECT name,email,vendedor,cpf_cnpj,password FROM users WHERE email = %s", (email,))
    result = db.fetchall()
    if result:
        result = result[0]
        data ={'name': result[0], 'email': result[1],'vendedor':result[2],'cpfCnpj':result[3],'password':result[4]}
        if  result[4] == hash_password(email+password):
            return jsonify(data), 200
    return jsonify({'message': 'E-mail ou senha inválidos!'}), 401

@app.route('/valid', methods=['POST'])
def valid():
    data = request.get_json()
    tokey    = data.get('tokey')
    password = data.get('password')
    mydb.commit()
    db.execute("SELECT email FROM users WHERE password = %s", (tokey,))
    email = db.fetchall()[0][0]
    hash = hash_password(email+password)   
    db.execute("SELECT email FROM users WHERE password = %s", (hash,))
    result = db.fetchall()
    if result:
        return jsonify({'res':'ok'}), 200
    else:
        return jsonify({'res':'false'}), 200

@app.route('/updateuser', methods=['POST'])
def updateuser():
    data = request.get_json()
    tokey    = data.get('tokey')
    name     = data.get('name')
    email    = data.get('email')
    password = data.get('password')
    if tokey and name and email and password:
        hash = hash_password(email+password)            
        db.execute("UPDATE users SET name = %s,email = %s, password = %s WHERE password =%s",
                (name,email,hash,tokey))
        mydb.commit()
        return jsonify({'tokey':hash}), 200
    return jsonify({"error": "Falha ao atualizar perfil"}), 500

@app.route('/deletuser', methods=['POST'])
def deletuser():
    try:
        data = request.get_json()
        if 'tokey' not in data:
            return jsonify({"error": "Usuário não informado"}), 400
        tokey = data.get('tokey')
        password = data.get('password')

        db.execute("SELECT email FROM users WHERE password = %s", (tokey,))
        email = db.fetchall()[0][0]
        print('tokey: ',tokey,'\nemail: ',email,'\npassword: ',password)

        #db.execute("UPDATE user SET email = %s,password = %s WHERE id =%s",(email,'perfildeletado',id))

        return jsonify({'mensagem':'perfil deletado'}), 200

    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({"error": "Falha ao deletar perfil"}), 500

#-------------------------------------------------------------------------
@app.route('/setendereco', methods=['POST'])
def setendereco():
    try:
        data = request.get_json()
        if 'tokey' not in data:
            return jsonify({"error": "Usuário não informado"}), 400
        tokey = data.get('tokey')
        cep = data.get('cep')
        uf = data.get('uf')
        cidade = data.get('cidade')
        rua = data.get('rua')
        numero = data.get('numero')
        #print('tokey:',tokey,'cep:',cep,'uf:',uf,"cidade:",cidade,'rua:',rua,'numero:',numero)
        
        db.execute("SELECT id FROM users WHERE password = %s", (tokey,))
        result = db.fetchall()

        if not result:
            return jsonify({"error": "Usuário não encontrado"}), 404
        user_id = result[0][0]
        db.execute("SELECT id, cep, uf, cidade, rua,numero FROM endereco WHERE user = %s", (user_id,))
        result = db.fetchall()
        if result:    
            db.execute("UPDATE endereco SET cep = %s,uf = %s,cidade = %s, rua = %s, numero = %s WHERE user =%s",
            (cep,uf,cidade,rua,numero,user_id))
            mydb.commit()
            return jsonify({"message": "endereço atualizado"}), 200
    
        db.execute("INSERT INTO endereco (user,cep,uf,cidade,rua,numero) VALUES (%s,%s,%s,%s,%s,%s)",
            (user_id,cep,uf,cidade,rua,numero))
        mydb.commit()
        return jsonify({"message": "endereço registrado"}), 200

    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({"error": "Falha ao registrar endereco"}), 500

@app.route('/getendereco', methods=['POST'])
def getendereco():
    try:
        data = request.get_json()
        if 'tokey' not in data:
            return jsonify({"error": "Usuário não informado"}), 400
        tokey = data.get('tokey')

        db.execute("SELECT id FROM users WHERE password = %s", (tokey,))
        result = db.fetchall()
        if not result:
            return jsonify({"error": "Usuário não encontrado"}), 404
        user_id = result[0][0]

        
        db.execute("SELECT id, cep, uf, cidade, rua,numero FROM endereco WHERE user = %s", (user_id,))
        result = db.fetchall()
        if not result:
            return jsonify({"cidade": "Nenhum endereço encontrado"}), 200
        

        result = result[0]
        data ={'cep': result[1],'uf':result[2],'cidade':result[3],'rua':result[4],'numero':result[5]}
        return jsonify(data), 200

    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({"error": "Falha ao recuperar endereco"}), 500

#-------------------------------------------------------------------------
@app.route('/uploadproducts', methods=['POST'])
def uploadProducts():
    data = request.get_json()

    if  'images' not in data:
        return jsonify({"error": "sem imagen"}), 400
    tokey = data.get('tokey')
    name = data.get('name')
    hashtags = data.get('hashtags')
    description = data.get('description')
    quantity = data.get('quantity')
    valor = data.get('valor')
    images_base64 = data.get('images')

    try: # armazenar os dados do produto e as imagens no db
        db.execute("SELECT id FROM users WHERE password = %s", (tokey,))
        result = db.fetchall()[0][0]
        
        db.execute("INSERT INTO products (name,descricao,quantity,valor,user) VALUES (%s,%s,%s,%s,%s)",
        (name, description,quantity,float(valor),result))
        mydb.commit()
        result = db.lastrowid

        try:
            hashtags = hashtags.split('#')
            for v in hashtags:
                if v:
                    db.execute("INSERT INTO hashtags (product,hashtag) VALUES (%s,%s)",(result,v))
                    mydb.commit()
        except Exception as e:
            print(f"Error hashtags: {e}")
        for v in images_base64:
            db.execute("INSERT INTO images (product,image) VALUES (%s,%s)",(result,v))
            mydb.commit()
        return jsonify({"mensagem": "Produto cadastrado"}), 200

    except Exception as e:
        print(f"Error decoding image: {e}")
        return jsonify({"error": "Tente novamente mais tarde"}), 400
    
@app.route('/getproducts', methods=['POST'])
def getproducts():
    try:
        data = request.get_json()


        if 'tokey' not in data:
            return jsonify({"error": "Usuário não informado"}), 400

        tokey = data.get('tokey')

        
        db.execute("SELECT id FROM users WHERE password = %s", (tokey,))
        result = db.fetchall()

        
        if not result:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        user_id = result[0][0]

        
        db.execute("SELECT id, name, descricao, quantity, valor FROM products WHERE user = %s", (user_id,))
        products = db.fetchall()

        if not products:
            return jsonify({"message": "Nenhum produto encontrado"}), 200

        
        product_list = []

        for product in products:
            
            product_dict = {
                'id': product[0],
                'name': product[1],
                'hashtags':'',
                'description': product[2],
                'quantity': product[3],
                'value': product[4],
                'images': []  
            }

            
            db.execute("SELECT image FROM images WHERE product = %s", (product[0],))
            image_results = db.fetchall()

            db.execute("SELECT hashtag FROM hashtags WHERE product = %s", (product[0],))
            hashtags_results = db.fetchall()

            hashtags=''
            if hashtags_results:
                for v in hashtags_results:
                    hashtags+=('#'+v[0])
                product_dict['hashtags'] = hashtags

            axu = []
            if image_results:
                for image in image_results:
                    v = image[0]
                    axu.append(v)
                product_dict['images'] = axu

            if '#f40b9c945c4f80a' not in hashtags:
                product_list.append(product_dict)

        
        return jsonify(product_list), 200

    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({"error": "Falha ao recuperar produtos"}), 500

@app.route('/getproduct', methods=['POST'])
def getproduct():
    try:
        data = request.get_json()
        id = data.get('id')

    
        db.execute("SELECT name, descricao, quantity, valor FROM products WHERE id = %s", (id,))
        product = db.fetchall()[0]

        if not product:
            return jsonify({"message": "Nenhum produto encontrado"}), 200

        product_dict = {
            'id': id,
            'name': product[0],
            'hashtags':'',
            'description': product[1],
            'quantity': product[2],
            'value': product[3],
            'images': []  
        }

        
        db.execute("SELECT image FROM images WHERE product = %s", (id,))
        image_results = db.fetchall()

        db.execute("SELECT hashtag FROM hashtags WHERE product = %s", (id,))
        hashtags_results = db.fetchall()

        hashtags=''
        if hashtags_results:
            for v in hashtags_results:
                hashtags+=('#'+v[0])
            product_dict['hashtags'] = hashtags

        axu = []
        if image_results:
            for image in image_results:
                v = image[0]
                axu.append(v)
            product_dict['images'] = axu

        if '#f40b9c945c4f80a' not in hashtags:
            return jsonify(product_dict), 200
        
        return jsonify({"message": "Nenhum produto encontrado"}), 200

    except Exception as e:
        print(f"Erro produto: {e}")
        return jsonify({"error": "Falha ao recuperar produto"}), 500
@app.route('/getquantity', methods=['POST'])
def getquantity():
    try:
        data = request.get_json()
        id = data.get('id')
    
        db.execute("SELECT quantity FROM products WHERE id = %s", (id,))
        product = db.fetchall()
        print(product)
        if product:
            return jsonify({'estoque':product}), 200
        return jsonify({'estoque':2}), 200
    except Exception as e:
        print(f"Erro quantity: {e}")
        return jsonify({"error": "Falha ao recuperar produto"}), 500

@app.route('/updateproducts', methods=['POST'])
def updateproducts():
    data = request.get_json()

    if  'images' not in data:
        return jsonify({"error": "sem produto"}), 400
    tokey = data.get('tokey')
    id = data.get('id')
    name = data.get('name')
    hashtags = data.get('hashtags')
    description = data.get('description')
    quantity = data.get('quantity')
    valor = data.get('valor')
    images_base64 = data.get('images')

    try: # armazenar os dados do produto e as imagens no db
        db.execute("SELECT id FROM users WHERE password = %s", (tokey,))
        result = db.fetchall()[0][0]
        if result:
            db.execute("UPDATE products SET name = %s,descricao = %s,quantity = %s, valor = %s WHERE id =%s",
            (name,description,quantity,float(valor),id))
            mydb.commit()
            db.execute("DELETE FROM images WHERE product =%s",[id])
            mydb.commit()
            db.execute("DELETE FROM hashtags WHERE product =%s",[id])
            mydb.commit()
            try:
                hashtags = hashtags.split('#')
                for v in hashtags:
                    if v:
                        db.execute("INSERT INTO hashtags (product,hashtag) VALUES (%s,%s)",(id,v))
                        mydb.commit()
            except Exception as e:
                print(f"Error hashtags: {e}")
            for v in images_base64:
                db.execute("INSERT INTO images (product,image) VALUES (%s,%s)",(id,v))
                mydb.commit()
            return jsonify({"mensagem": "Produto atualizado"}), 200
        
        return jsonify({"error": "Tente novamente mais tarde"}), 400

    except Exception as e:
        print(f"Error decoding image: {e}")
        return jsonify({"error": "Tente novamente mais tarde"}), 400

@app.route('/deletproducts', methods=['POST'])
def deletproducts():
    data = request.get_json()

    tokey = data.get('tokey')
    id = data.get('id_product')

    try: 
        db.execute("SELECT id FROM users WHERE password = %s", (tokey,))
        result = db.fetchall()[0][0]
        if result:
            v = 'f40b9c945c4f80a'
            db.execute("DELETE FROM hashtags WHERE product =%s",[id])
            mydb.commit()
            db.execute("INSERT INTO hashtags (product,hashtag) VALUES (%s,%s)",(id,v))
            mydb.commit()
            return jsonify({"mensagem": "Produto deletado"}), 200
        
        return jsonify({"error": "Tente novamente mais tarde"}), 400

    except Exception as e:
        print(f"Error decoding: {e}")
        return jsonify({"error": "Tente novamente mais tarde"}), 400

@app.route('/getproductscliente', methods=['POST'])
def getproductscliente():
    try:
        data = request.get_json()
        if 'cep' not in data:
            db.execute("SELECT id, name, descricao, quantity, valor FROM products ")
            products = db.fetchall()
            if not products:
                return jsonify({"message": "Nenhum produto encontrado"}), 200
            
            product_list = []
            for product in products:
                product_dict = {
                    'id': product[0],
                    'name': product[1],
                    'description': product[2],
                    'quantity': product[3],
                    'value': product[4],
                    'images': []
                }
                db.execute("SELECT image FROM images WHERE product = %s", (product[0],))
                image_results = db.fetchall()
                sleep(0.02)
                db.execute("SELECT hashtag FROM hashtags WHERE product = %s", (product[0],))
                hashtags_results = db.fetchall()

                hashtags=''
                if hashtags_results:
                    for v in hashtags_results:
                        hashtags+=('#'+v[0])
                    product_dict['hashtags'] = hashtags

                axu = []
                if image_results:
                    for image in image_results:
                        v = image[0]
                        axu.append(v)
                    product_dict['images'] = axu

                if '#f40b9c945c4f80a' not in hashtags:
                    product_list.append(product_dict)
                
            return jsonify(product_list), 200
        else:
            cep = data.get('cep')
            cep_prefix = cep[:3]
            #print(cep_prefix)
            db.execute("""SELECT p.id, p.name, p.descricao, p.quantity, p.valor
                            FROM products p JOIN endereco e ON p.user = e.user
                            WHERE e.cep LIKE %s""",(f'{cep_prefix}%',))
            products = db.fetchall()
            if not products:
                return jsonify({"message": "Nenhum produto encontrado"}), 200
            
            product_list = []
            for product in products:
                product_dict = {
                    'id': product[0],
                    'name': product[1],
                    'description': product[2],
                    'quantity': product[3],
                    'value': product[4],
                    'images': []
                }
                db.execute("SELECT image FROM images WHERE product = %s", (product[0],))
                image_results = db.fetchall()
                sleep(0.02)
                db.execute("SELECT hashtag FROM hashtags WHERE product = %s", (product[0],))
                hashtags_results = db.fetchall()

                hashtags=''
                if hashtags_results:
                    for v in hashtags_results:
                        hashtags+=('#'+v[0])
                    product_dict['hashtags'] = hashtags

                axu = []
                if image_results:
                    for image in image_results:
                        v = image[0]
                        axu.append(v)
                    product_dict['images'] = axu

                if '#f40b9c945c4f80a' not in hashtags:
                    product_list.append(product_dict)
                
            return jsonify(product_list), 200
    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({"error": "Falha ao recuperar produtos"}), 500
   
#-------------------------------------------------------------------------

@app.route('/addcart', methods=['POST'])
def addcart():
    try:
        data = request.get_json()
        tokey = data.get('tokey')
        produto =data.get('id')
        quantity = data.get('quantity')



        mydb.commit()
        db.execute("SELECT id FROM users WHERE password = %s", (tokey,))
        result = db.fetchall()

        db.execute("SELECT id,quantity FROM cart WHERE product = %s", (produto,))
        product = db.fetchall()
        if product:
            if quantity ==0:
                quantity = product[0][1]+1
            db.execute("UPDATE cart SET quantity = %s WHERE id =%s",
            (quantity,product[0][0]))
            mydb.commit()
        else:
            db.execute("INSERT INTO cart (quantity,product,user) VALUES (%s,%s,%s)",
            (1,produto,result[0][0]))
            mydb.commit()
        
        return jsonify("product_list"), 200
    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({"error": "Falha ao recuperar produtos"}), 500

@app.route('/getcart', methods=['POST'])
def getcart():
    try:
        data = request.get_json()
        tokey = data.get('tokey')


        mydb.commit()
        db.execute("SELECT id FROM users WHERE password = %s", (tokey,))
        result = db.fetchall()

        db.execute("SELECT id,quantity,product FROM cart WHERE user = %s", (result[0][0],))
        cart = db.fetchall()
        product_list = []

        for item in cart:
            db.execute("SELECT name,valor FROM products WHERE id = %s", (item[2],))
            products = db.fetchall()

            if products:
                product_dict = {
                    'id': item[0], 
                    'produto':item[2],
                    'name': products[0][0],
                    'value': products[0][1],
                    'quantity': item[1], 
                }

                product_list.append(product_dict)
        return jsonify(product_list), 200

    
    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({"error": "Falha ao recuperar produtos"}), 500

@app.route('/removecart', methods=['POST'])
def removecart():
    try:
        data = request.get_json()
        tokey = data.get('tokey')
        cart = data.get('id')


        mydb.commit()
        db.execute("SELECT id FROM users WHERE password = %s", (tokey,))
        result = db.fetchall()
        if result:
            db.execute("DELETE FROM cart WHERE id = %s", (cart,))
            mydb.commit()
        return jsonify('deletado'), 200

    
    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({"error": "Falha ao recuperar produtos"}), 500

@app.route('/editcart', methods=['POST'])
def editcart():
    try:
        data = request.get_json()
        tokey = data.get('tokey')
        cart = data.get('id')
        quantity = data.get('quantity')

        mydb.commit()
        db.execute("SELECT id FROM users WHERE password = %s", (tokey,))
        result = db.fetchall()
        if result:
            db.execute("UPDATE cart SET quantity = %s  WHERE id = %s", (quantity,cart,))
            mydb.commit()
        return jsonify('atualizado'), 200

    
    except Exception as e:
        error_message = traceback.format_exc()
        print(f"Erro ao atualizar cart: {error_message}")
        return jsonify({"error": "Falha ao atualizar cart"}), 500

#-------------------------------------------------------------------------

@app.route('/mcompras', methods=['POST'])
def getcompras():
    data = request.get_json()
    tokey = data.get('tokey')
    if not tokey:
        return jsonify({'message': 'sem user!'}), 200
    mydb.commit()
    query = """SELECT o.valor,o.date,p.id AS product_id, p.name,i.image FROM ordens o 
        JOIN products p ON o.product = p.id 
        JOIN images i ON i.product = p.id
        JOIN users u ON o.user = u.id
        WHERE u.password = %s AND o.statos = 'T' AND i.id = (SELECT MIN(id) FROM images WHERE product = p.id)
    """
    db.execute(query, (tokey,))
    results = db.fetchall()
    if not results:
        return jsonify({'message': 'sem result!'}), 200
    list_conproa=[]
    for row in results:
        data ={'valor': row[0], 'data': str(row[1]),'id_produto':row[2],'nome_produto':row[3],'image':row[4]}
        list_conproa.append(data)
    return jsonify(list_conproa), 200

#-------------------------------------------------------------------------

@app.route('/ordem', methods=['POST'])
def ordem():
    try:
        data = request.get_json()
        tokey = data.get('tokey')


        mydb.commit()
        db.execute("SELECT id FROM users WHERE password = %s", (tokey,))
        user_id = db.fetchall()[0][0]
        
        db.execute("SELECT id,quantity,product FROM cart WHERE user = %s", (user_id,))
        cart = db.fetchall()
        for item in cart:
            db.execute("SELECT quantity,valor FROM products WHERE id = %s", (item[2],))
            products = db.fetchall()
            cont = products[0][0]-item[1]
            if cont < 1:
                print(cont)
                cont =1
            db.execute("UPDATE products SET quantity = %s WHERE id =%s",
            (cont,item[2]))
            mydb.commit()
            for i in range(item[1]):
                db.execute("INSERT INTO ordens (product,user,valor,statos) VALUES (%s,%s,%s,%s)",
                (item[2],user_id,products[0][1],'A',))
                mydb.commit()
        
        
        db.execute("DELETE FROM cart WHERE user = %s", (user_id,))
        mydb.commit()
        return jsonify('atualizado'), 200

    
    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({"error": "Falha ao recuperar produtos"}), 500

@app.route('/getordens', methods=['POST'])
def getordens():
    try:
        data = request.get_json()
        tokey = data.get('tokey')


        mydb.commit()
        db.execute("SELECT id FROM users WHERE password = %s", (tokey,))
        user_id = db.fetchall()[0][0]

        db.execute("SELECT id,name FROM products WHERE id = %s", (user_id,))
        products = db.fetchall()
        if not products:
            return jsonify({'message': 'vazil!'}), 200
        product_list=[]
        for product in products:

            db.execute("SELECT id,user,statos,valor FROM ordens WHERE  product= %s", (product[0],))
            ordens = db.fetchall()
            if ordens:
                for ordem in ordens:
                    if ordem[2]=='A':
                        db.execute("SELECT id,name,email,cpf_cnpj FROM users WHERE  id= %s", (ordem[1],))
                        id_cli = db.fetchall()[0]

                        db.execute("SELECT id,cep,uf,cidade,rua,numero FROM endereco WHERE  user= %s", (id_cli[0],))
                        ende_cli = db.fetchall()[0]
                        mydb.commit()
                        ordem_dict = {
                            'id': ordem[0],
                            'id_pro':product[0],
                            'name_pro':product[1],
                            'valor_pro':ordem[3],
                            'id_cli': id_cli[0],
                            'name_cli': id_cli[1],
                            'email_cli':id_cli[2],
                            'cpf_cli': id_cli[3],
                            'id_end': ende_cli[0],
                            'cep_end': ende_cli[1],
                            'uf_end': ende_cli[2],
                            'cidade': ende_cli[3],
                            'rua': ende_cli[4],
                            'numero':ende_cli[5],
                        }
                        
                        product_list.append(ordem_dict)
        if product_list:      
            return jsonify(product_list), 200
        else:
            return jsonify({'message': 'vazil!'}), 200

    
    except Exception as e:
        error_message = traceback.format_exc()
        print(f"Erro ao recuperar ordens: {error_message}")
        return jsonify({"error": "Falha ao recuperar ordens"}), 500

@app.route('/getordense', methods=['POST'])
def getordense():
    try:
        data = request.get_json()
        tokey = data.get('tokey')


        mydb.commit()
        db.execute("SELECT id FROM users WHERE password = %s", (tokey,))
        user_id = db.fetchall()[0][0]

        db.execute("SELECT id,name FROM products WHERE id = %s", (user_id,))
        products = db.fetchall()
        if not products:
            return jsonify({'message': 'vazil!'}), 200
        product_list=[]
        for product in products:

            db.execute("SELECT id,user,statos,valor FROM ordens WHERE  product= %s", (product[0],))
            ordens = db.fetchall()
            if ordens:
                for ordem in ordens:
                    if ordem[2]=='T':
                        db.execute("SELECT id,name,email,cpf_cnpj FROM users WHERE  id= %s", (ordem[1],))
                        id_cli = db.fetchall()[0]

                        db.execute("SELECT id,cep,uf,cidade,rua,numero FROM endereco WHERE  user= %s", (id_cli[0],))
                        ende_cli = db.fetchall()[0]
                        mydb.commit()
                        ordem_dict = {
                            'id': ordem[0],
                            'id_pro':product[0],
                            'name_pro':product[1],
                            'valor_pro':ordem[3],
                            'id_cli': id_cli[0],
                            'name_cli': id_cli[1],
                            'email_cli':id_cli[2],
                            'cpf_cli': id_cli[3],
                            'id_end': ende_cli[0],
                            'cep_end': ende_cli[1],
                            'uf_end': ende_cli[2],
                            'cidade': ende_cli[3],
                            'rua': ende_cli[4],
                            'numero':ende_cli[5],
                        }
                        
                        product_list.append(ordem_dict)
        if product_list:      
            return jsonify(product_list), 200
        else:
            return jsonify({'message': 'vazil!'}), 200

    
    except Exception as e:
        error_message = traceback.format_exc()
        print(f"Erro ao recuperar ordens: {error_message}")
        return jsonify({"error": "Falha ao recuperar ordens"}), 500

@app.route('/getordensf', methods=['POST'])
def getordensf():
    try:
        data = request.get_json()
        tokey = data.get('tokey')


        mydb.commit()
        db.execute("SELECT id FROM users WHERE password = %s", (tokey,))
        user_id = db.fetchall()[0][0]

        db.execute("SELECT id,name FROM products WHERE id = %s", (user_id,))
        products = db.fetchall()
        if not products:
            return jsonify({'message': 'vazil!'}), 200
        product_list=[]
        for product in products:

            db.execute("SELECT id,user,statos,valor FROM ordens WHERE  product= %s", (product[0],))
            ordens = db.fetchall()
            if ordens:
                for ordem in ordens:
                    if ordem[2]=='E':
                        db.execute("SELECT id,name,email,cpf_cnpj FROM users WHERE  id= %s", (ordem[1],))
                        id_cli = db.fetchall()[0]

                        db.execute("SELECT id,cep,uf,cidade,rua,numero FROM endereco WHERE  user= %s", (id_cli[0],))
                        ende_cli = db.fetchall()[0]
                        mydb.commit()
                        ordem_dict = {
                            'id': ordem[0],
                            'id_pro':product[0],
                            'name_pro':product[1],
                            'valor_pro':ordem[3],
                            'id_cli': id_cli[0],
                            'name_cli': id_cli[1],
                            'email_cli':id_cli[2],
                            'cpf_cli': id_cli[3],
                            'id_end': ende_cli[0],
                            'cep_end': ende_cli[1],
                            'uf_end': ende_cli[2],
                            'cidade': ende_cli[3],
                            'rua': ende_cli[4],
                            'numero':ende_cli[5],
                        }
                        
                        product_list.append(ordem_dict)
        if product_list:      
            return jsonify(product_list), 200
        else:
            return jsonify({'message': 'vazil!'}), 200

    
    except Exception as e:
        error_message = traceback.format_exc()
        print(f"Erro ao recuperar ordens: {error_message}")
        return jsonify({"error": "Falha ao recuperar ordens"}), 500

@app.route('/enviado', methods=['POST'])
def enviado():
    try:
        data = request.get_json()
        tokey = data.get('tokey')
        id = data.get('id')


        mydb.commit()
        db.execute("SELECT id FROM users WHERE password = %s", (tokey,))
        user_id = db.fetchall()[0][0]
        if not user_id:
            return jsonify({'message': 'sem user!'}), 200
        
        db.execute("UPDATE ordens SET statos = %s  WHERE id = %s", ('T',id,))
        mydb.commit()
        return jsonify({'message': 'ok!'}), 200

    
    except Exception as e:
        error_message = traceback.format_exc()
        print(f"Erro ao recuperar ordens: {error_message}")
        return jsonify({"error": "Falha ao recuperar ordens"}), 500

@app.route('/pesquisa', methods=['POST'])
def pesquisa():
    try:
        data = request.get_json()
        cep = data.get('cep')
        hashtag =data.get('hashtags')
        if not hashtag:
            return jsonify({"message": "Nenhum produto encontrado"}), 200
        hashtags =hashtag.split('#')
        for c,it in enumerate(hashtags):
            if not it:
                hashtags[c]='1'
        cep_prefix = cep[:3]
        db.execute("""
            SELECT p.id, p.name, p.descricao, p.quantity, p.valor
            FROM products p
            JOIN endereco e ON p.user = e.user
            LEFT JOIN hashtags h ON p.id = h.product
            WHERE e.cep LIKE %s
            AND h.hashtag IN ({})
        """.format(','.join(['%s'] * len(hashtags))), (f'{cep_prefix}%',*hashtags))
        products = db.fetchall()
        if not products:
            return jsonify({"message": "Nenhum produto encontrado"}), 200
        
        product_list = []
        for product in products:
            product_dict = {
                'id': product[0],
                'name': product[1],
                'hashtags':'',
                'description': product[2],
                'quantity': product[3],
                'value': product[4],
                'images': []
            }
            db.execute("SELECT image FROM images WHERE product = %s", (product[0],))
            image_results = db.fetchall()
            sleep(0.02)
            db.execute("SELECT hashtag FROM hashtags WHERE product = %s", (product[0],))
            hashtags_results = db.fetchall()

            hashtags=''
            if hashtags_results:
                for v in hashtags_results:
                    hashtags+=('#'+v[0])
                product_dict['hashtags'] = hashtags
            if image_results:
                product_dict['images'] = [image_results[0][0]]
            
            if '#f40b9c945c4f80a' not in hashtags:
                product_list.append(product_dict)
                
            return jsonify(product_list), 200
    except Exception as e:
        error_message = traceback.format_exc()
        print(f"Erro ao recuperar ordens: {error_message}")
        return jsonify({"error": "Falha ao recuperar produtos"}), 500



#-------------------------------web_teste--------------------------------------
def gerajsom(d):
    r = [{'id': item[0], 'name': item[1],'email':item[2],'cpfCnpj':item[4]} for item in d]
    return r

@app.route('/',methods=['GET'])
def page():
    mydb.commit()
    db.execute("SELECT * FROM users")
    result = db.fetchall()
    result = gerajsom(result)
    return render_template('teste.html',data=result)

@app.route('/page/<page_id>',methods =['POST'])
def updatepage(page_id):
    data =str(request.get_data())[1:-1]
    data = data.split('&')
    aux = [v.split('=')[1] for v in data]
    #print('aux updatepage:',aux)    
    data ={'name': aux[0], 'email': aux[1],'cpfCnpj':aux[2]}
    name     = data.get('name')
    email    = data.get('email')
    cpfCnpj = data.get('cpfCnpj')
    db.execute("UPDATE users SET name = %s,email = %s,cpf_cnpj = %s WHERE id =%s",(name,email,cpfCnpj,page_id))
    mydb.commit()
    return redirect('/')

@app.route('/delete/<delete_id>')
def deletepage(delete_id):
    db.execute("DELETE FROM users WHERE id =%s",[delete_id])
    mydb.commit()
    return redirect('/')


#-----------------------------------fim--------------------------------------------
if __name__ == '__main__':
    #app.run(debug=True) 
    serve(app, host="0.0.0.0", port=5000)
