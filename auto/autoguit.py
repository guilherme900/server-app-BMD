from os import system
from socket import gethostname,gethostbyname

diretorio = 'C:/Users/guilh/Documents/GitHub/severid/index.html'
re ='http://'+gethostbyname(gethostname())+':5000/'
arquivo = open(diretorio, 'w+',encoding="utf-8")
arquivo.write(re)
arquivo.close()

system('C:/Users/guilh/Documents/.FACUDADE/periodos/8-periodo/T_G_I_2/tra/tcc/pro-server/auto/auto.bat')
print(re)
