from colorama import Fore, init
from datetime import datetime
import getpass
import hashlib
import jwt
from dotenv import load_dotenv
import os
import re
from operaciones.simulacion_operaciones import SimulacionOperaciones
from operaciones.usuario_operaciones import UsuarioOperaciones
from modelos.Simulacion import Simulacion
from modelos.Usuario import Usuario
from conexion_bd import get_connection

load_dotenv()

# Variable global para guardar id_usuario
global_id_usuario = None

# Sistema de autenticación
def login():
	global global_id_usuario
	global user
	username = input("Usuario: ")
	password = getpass.getpass("Contraseña: ")
	# Hash de la contraseña
	password_hash = hashlib.sha256(password.encode()).hexdigest()
	
	connection = get_connection()
	try:
		cursor = connection.cursor(dictionary=True)
		cursor.execute("SELECT * FROM usuarios WHERE username = %s AND password_hash = %s",
					  (username, password_hash))
		user = cursor.fetchone()
		if user:
			# Obtener id_usuario y almacenarla en un valor probablemente global
			global_id_usuario = user['id']
			# Generar token JWT
			token = jwt.encode(
				{'user_id': user['id'], 'username': user['username']},
				os.getenv('JWT_SECRET', 'your-secret-key'),
				algorithm='HS256'
			)
			# DELETE / ELIMINAR
			print(token)
			return token
		return None
	finally:
		if connection.is_connected():
			cursor.close()
			connection.close()

def menu_principal():
	token = login()
	if not token:
		print("Autenticación fallida")
		return
	
	os.system("cls")

	# Para la librería Colorama:
	init(autoreset=True)
	
	while True:
		print(Fore.YELLOW + "\n=== Sistema de Simulación de Importaciones ===")
		print(Fore.RED + "1. Registrar nueva simulación")
		print(Fore.RED + "2. Listar simulaciones")
		print(Fore.BLUE + "3. Registrar nuevo usuario")
		print(Fore.BLUE + "4. Listar usuarios")
		print(Fore.BLUE + "5. Eliminar usuario")
		print(Fore.BLUE + "6. Actualizar usuario")
		print(Fore.GREEN + "7. Salir")
		
		opcion = input("\nSeleccione una opción: ")
		
		# os.system("cls")
		match opcion:
			case "1":
				registrar_simulacion(token)
			case "2":
				listar_simulaciones(token)
			case "3":
				registrar_usuario(token)
			case "4":
				listar_usuarios(token)			
			case "5":
				eliminar_usuario(token)
			case "6":
				actualizar_usuario(token)
			case "7":
				print(Fore.GREEN + "¡Hasta luego!")
				break
			case _:
				print("Opción no válida")
		os.system("pause")
		os.system("cls")

def input_nv(instruccion):
	valor_ingresado = None
	while not valor_ingresado:
		valor_ingresado = input(instruccion)
		if not valor_ingresado:
			print("Por favor, ingrese un valor.")
	return valor_ingresado

def input_num(instruccion, tipo_num):
	num = None
	while not num:
		valor = input_nv(instruccion)
		if tipo_num == "entero":
			patron = r"\d+"
		elif tipo_num == "decimal":
			patron = r"\d+(?:\.\d{1,2})?"
		num = re.fullmatch(patron, valor)
		if num and num.group() not in ["0", "0.0", "0.00"]:
			num = num.group()
			return num
		else:
			print(f"Por favor, ingrese un número {tipo_num} positivo válido.")
			num = None

def registrar_simulacion(token):
	try:
		unidades = int(input_num(Fore.RED + "\nIngrese cantidad de unidades: ", "entero"))
		costo_unitario_usd = float(input_num(Fore.RED + "Ingrese costo unitario, en dólares: ", "decimal"))
		nombre_articulo = input_nv(Fore.RED + "Ingrese nombre del artículo: ")
		codigo_articulo = input_nv(Fore.RED + "Ingrese código del artículo: ")
		nombre_proveedor = input_nv(Fore.RED + "Ingrese nombre del proveedor: ")
		costo_envio_usd = float(input_num(Fore.RED + "Ingrese costo de envío, en dólares: ", "decimal"))

		# Obtener valor del dólar actual
		valor_dolar_clp = SimulacionOperaciones.obtener_valor_dolar(datetime.now())
		if not valor_dolar_clp:
			print(Fore.RED + "Error al obtener valor del dólar")
			return
		
		total_pedido_usd = unidades * costo_unitario_usd
		total_pedido_clp = total_pedido_usd * valor_dolar_clp
		print(Fore.RED + f"\nTotal de pedido (CLP): \t\t\t{total_pedido_clp:.0f}")
		
		valor_cif_usd = total_pedido_usd + costo_envio_usd
		valor_cif_clp = valor_cif_usd * valor_dolar_clp
		print(Fore.RED + f"Valor CIF (CLP): \t\t\t{valor_cif_clp:.0f}")
		
		costo_envio_clp = costo_envio_usd * valor_dolar_clp
		print(Fore.RED + f"Costo de envío (CLP): \t\t\t{costo_envio_clp:.0f}")
		
		tasa_importacion_aduana_clp = valor_cif_clp * 0.06
		print(Fore.RED + f"Tasa de importación de aduana (CLP): \t{tasa_importacion_aduana_clp:.0f}")
		
		iva_clp = valor_cif_clp * 0.19
		print(Fore.RED + f"IVA (CLP): \t\t\t\t{iva_clp:.0f}")
		
		tasa_mas_iva_clp = tasa_importacion_aduana_clp + iva_clp
		print(Fore.RED + f"Total de impuestos (tasa + IVA) (CLP): \t{tasa_mas_iva_clp:.0f}")
		
		tasa_mas_iva_usd = tasa_mas_iva_clp / valor_dolar_clp
		costo_total_usd = valor_cif_usd + tasa_mas_iva_usd
		print(Fore.RED + f"Costo total (USD): \t\t\t{costo_total_usd}")

		costo_total_clp = costo_total_usd * valor_dolar_clp
		print(Fore.RED + f"Costo total (CLP): \t\t\t{costo_total_clp:.0f}")
		if costo_total_clp > 99999999999:
			print(Fore.RED + "No es posible registrar el valor de Costo total(CLP) en la base de datos, pues es un entero con más de 11 cifras. Por favor, intente ingresar valores de menor magnitud.")
			return

		simulacion = Simulacion(
			unidades=unidades,
			costo_unitario_usd=costo_unitario_usd,
			costo_envio_usd=costo_envio_usd,
			nombre_articulo=nombre_articulo,
			codigo_articulo=codigo_articulo,
			nombre_proveedor=nombre_proveedor,
			costo_total_clp=costo_total_clp,
			valor_dolar_clp=valor_dolar_clp,
			fecha_simulacion=datetime.now(),
			id_usuario=global_id_usuario
		)

		if SimulacionOperaciones.crear_simulacion(simulacion):
			print(Fore.RED + "Simulacion registrada exitosamente")
		else:
			print(Fore.RED + "Error al registrar simulacion")

	except ValueError as e:
		print(Fore.RED + f"Error en el formato de los datos: {e}")
	except Exception as e:
		print(Fore.RED + f"Error inesperado: {e}")

def listar_simulaciones(token):
	simulaciones = SimulacionOperaciones.listar_simulaciones()
	cantidad_sim = int(input_num(Fore.RED + f"¿Cuántas simulaciones desea listar (máximo {len(simulaciones)})? ", "entero"))
	if not simulaciones:
		print(Fore.RED + "No hay simulaciones registradas")
		return
	elif cantidad_sim > len(simulaciones):
		print(Fore.RED + f"Por favor, ingrese un número menor o igual a {len(simulaciones)} (cantidad de simulaciones ingresadas en la base de datos).")
		return

	print(Fore.RED + "\n=== Listado de Simulaciones ===")
	print(Fore.RED + "%3s %-10s %-20s %-20s %-40s %-15s %-20s %-20s %-15s %-20s %-10s" % ("ID", "UNIDADES", "COSTO UNITARIO (USD)", "COSTO ENVÍO (USD)", "NOMBRE ARTÍCULO", "CÓDIGO ARTÍCULO", "NOMBRE PROVEEDOR", "COSTO TOTAL (CLP)", "VALOR DÓLAR (CLP)", "FECHA SIMULACIÓN", "ID USUARIO"))
	print(Fore.RED + "%3s %-10s %-20s %-20s %-40s %-15s %-20s %-20s %-15s %-20s %-10s" % ("---", "--------", "--------------------", "--------------------", "----------------------------------------", "---------------", "--------------------", "--------------------", "---------------", "--------------------", "----------"))
	for i in range(cantidad_sim):
		print(Fore.RED + "%3s %10d %20.2f %20.2f %-40s %-15s %-20s %20.0f %15.2f %20s %10d" % (simulaciones[i].id, simulaciones[i].unidades, simulaciones[i].costo_unitario_usd, simulaciones[i].costo_envio_usd, simulaciones[i].nombre_articulo, simulaciones[i].codigo_articulo, simulaciones[i].nombre_proveedor, simulaciones[i].costo_total_clp, simulaciones[i].valor_dolar_clp, simulaciones[i].fecha_simulacion.strftime("%Y-%m-%d %H:%M:%S"), simulaciones[i].id_usuario))

def registrar_usuario(token):
	try:
		username = input(Fore.BLUE + "Ingrese username: ")
		
		# Buscar usuario con el mismo username
		user_2 = UsuarioOperaciones.buscar_por_username(username)
		if user_2:
			print(Fore.BLUE + "Ya existe un usuario con ese username")
			return		
		
		password = getpass.getpass(Fore.BLUE + "Ingrese password: ")
		# Hash de la contraseña del usuario
		password_hash = hashlib.sha256(password.encode()).hexdigest()

		usuario = Usuario(
			username=username,
			password_hash=password_hash
		)

		if UsuarioOperaciones.crear_usuario(usuario):
			print(Fore.BLUE + "Usuario registrado exitosamente")
		else:
			print(Fore.BLUE + "Error al registrar usuario")
	
	except ValueError as e:
		print(Fore.BLUE + f"Error en el formato de los datos: {e}")
	except Exception as e:
		print(Fore.BLUE + f"Error inesperado: {e}")

def listar_usuarios(token):
	usuarios = UsuarioOperaciones.listar_usuarios()
	if not usuarios:
		print(Fore.BLUE + "No hay usuarios registrados")
		return
	print(Fore.BLUE + "\n=== Listado de Usuarios ===")
	# for usuario in usuarios:
		# print(f"\nID:\t\t{usuario.id}")
		# print(f"Username:\t{usuario.username}")
		# print(f"Password hash:\t{usuario.password_hash}")
	# Una forma alternativa de mostrar los datos podría ser la siguiente:
	print(Fore.BLUE + "%3s %-25s %-64s" % ("ID", "USERNAME", "PASSWORD HASH"))
	print(Fore.BLUE + "%3s %-25s %-64s" % ("---", "-------------------------", "----------------------------------------------------------------"))
	for usuario in usuarios:
		print(Fore.BLUE + "%3s %-25s %-64s" % (usuario.id, usuario.username, usuario.password_hash))

def eliminar_usuario(token):
	try:
		# Primero, listar usuarios para que el usuario sepa cuáles son los ids disponibles
		listar_usuarios(token)

		id = input(Fore.BLUE + "\nIngrese id de usuario a eliminar: ")
		
		# Buscar usuario con el id ingresado
		se_encontro = UsuarioOperaciones.buscar_por_id(id)

		if se_encontro:
			se_elimino = UsuarioOperaciones.eliminar_usuario(id)
			if se_elimino:
				print(Fore.BLUE + "Usuario eliminado exitosamente")
			else:
				print(Fore.BLUE + "Error al eliminar usuario")
		else:
			print(Fore.BLUE + "No existe un usuario con ese id")
			return

	except ValueError as e:
		print(Fore.BLUE + f"Error en el formato de los datos: {e}")
	except Exception as e:
		print(Fore.BLUE + f"Error inesperado: {e}")

def actualizar_usuario(token):
	try:
		# Primero, listar usuarios para que el usuario sepa cuáles son los ids disponibles
		listar_usuarios(token)

		id = input(Fore.BLUE + "\nIngrese ID de usuario a actualizar: ")
		
		# Buscar usuario con el id ingresado
		usuario_original = UsuarioOperaciones.buscar_por_id(id)

		if usuario_original:
			username = input(Fore.BLUE + "Ingrese nuevo username: ")
			password = getpass.getpass(Fore.BLUE + "Ingrese nueva password: ")
			# Hash de la nueva contraseña del usuario
			password_hash = hashlib.sha256(password.encode()).hexdigest()

			usuario_nuevo = Usuario(
			id = usuario_original.id,
			username = username if username else usuario_original.username,
			password_hash = password_hash if password else usuario_original.password_hash
			)
			se_actualizo = UsuarioOperaciones.actualizar_usuario(usuario_nuevo)
			if se_actualizo:
				print(Fore.BLUE + "Usuario actualizado exitosamente")
			else:
				print(Fore.BLUE + "Error al actualizar usuario")
		else:
			print(Fore.BLUE + "No existe un usuario con ese id")
			return

	except ValueError as e:
		print(Fore.BLUE + f"Error en el formato de los datos: {e}")
	except Exception as e:
		print(Fore.BLUE + f"Error inesperado: {e}")

if __name__ == "__main__":
	menu_principal()