import mysql.connector

nameBanco= "test"

def initializeDatabase():
        mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",
        database=nameBanco
        )

        mycursor = mydb.cursor()

        mycursor.execute("""
                CREATE TABLE IF NOT EXISTS users(
                id INT NOT NULL AUTO_INCREMENT,
                name VARCHAR (30) NOT NULL,
                email VARCHAR (30) NOT NULL,
                vendedor ENUM('V','C') DEFAULT 'C',
                cpf_cnpj VARCHAR (14) NOT NULL,
                password VARCHAR (66) NOT NULL,
                PRIMARY KEY (id)
                );
        """)
        mycursor.execute("""
                CREATE TABLE IF NOT EXISTS endereco(
                id INT NOT NULL AUTO_INCREMENT,
                user INT NOT NULL,
                cep VARCHAR (9) NOT NULL,
                uf CHAR (2) NOT NULL,
                cidade VARCHAR (30) NOT NULL,
                rua VARCHAR (40) NOT NULL,
                numero SMALLINT,
                PRIMARY KEY (id),
                FOREIGN KEY (user) REFERENCES users(id)
                );
        """)    
        mycursor.execute("""
                CREATE TABLE IF NOT EXISTS products(
                id  INT NOT NULL AUTO_INCREMENT,
                name VARCHAR (30) NOT NULL,
                descricao VARCHAR (300),
                quantity INT NOT NULL,
                valor FLOAT NOT NULL,
                user INT NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY (user) REFERENCES users(id)
                );
        """)
        mycursor.execute("""
                CREATE TABLE IF NOT EXISTS images(
                id  INT NOT NULL AUTO_INCREMENT,
                product INT NOT NULL,
                image LONGTEXT NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY (product) REFERENCES products(id)
                );
        """) 
        mycursor.execute("""
                CREATE TABLE IF NOT EXISTS ordens(
                id INT NOT NULL AUTO_INCREMENT,
                product INT NOT NULL,
                user INT NOT NULL,
                valor FLOAT NOT NULL,
                statos ENUM('A','T','E') DEFAULT 'A',
                date DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                FOREIGN KEY (product) REFERENCES products(id),
                FOREIGN KEY (user) REFERENCES users(id)
                );
        """)    
        mycursor.execute("""
                CREATE TABLE IF NOT EXISTS favoritos(
                id INT NOT NULL AUTO_INCREMENT,
                product INT NOT NULL,
                user INT NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY (product) REFERENCES products(id),
                FOREIGN KEY (user) REFERENCES users(id)
                );
        """)    
        mycursor.execute("""
                CREATE TABLE IF NOT EXISTS historico(
                id INT NOT NULL AUTO_INCREMENT,
                product INT NOT NULL,
                user INT NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY (product) REFERENCES products(id),
                FOREIGN KEY (user) REFERENCES users(id)
                );
        """)
        mycursor.execute("""
                CREATE TABLE IF NOT EXISTS cart(
                id INT NOT NULL AUTO_INCREMENT,
                quantity INT NOT NULL,
                product INT NOT NULL,
                user INT NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY (product) REFERENCES products(id),
                FOREIGN KEY (user) REFERENCES users(id)
                );
        """)
        mycursor.execute("""
                CREATE TABLE IF NOT EXISTS hashtags(
                id INT NOT NULL AUTO_INCREMENT,
                product INT NOT NULL,
                hashtag VARCHAR (15) NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY (product) REFERENCES products(id)
                );
        """)
        mycursor.close()
        mydb.close()
        print('db:',nameBanco,'\n-----------------------online-----------------------')
initializeDatabase()

