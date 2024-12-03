import base64
from cmath import e
import random
from app import app
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from io import BytesIO
from flask import render_template,send_file, make_response
from werkzeug.utils import secure_filename
from flask_paginate import Pagination
from app.forms import formproducto,formcategoria,RegistrationForm,LoginForm, PersonaForm,EditarPersonaForm,CrearPersonaForm,EditarCategoriaForm,EditarProductoForm
from app.models import Producto,Categoria,User,Carrito,ProductoEnCarrito,Persona, Factura,FacturaProducto,Notificacion
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from flask_session import Session
import os
import string
from flask import flash, redirect, url_for, request,jsonify
from flask_login import current_user
from flask_login import LoginManager
from flask_wtf.csrf import CSRFError
from sqlalchemy.exc import IntegrityError
import pdfkit
from sqlalchemy import extract
import logging
login_manager = LoginManager()
login_manager.init_app(app)



@login_manager.user_loader
def load_user(user_id):
    try:
        # Convertir user_id a entero y obtener el usuario
        user = User.query.get(int(user_id))
        # Imprimir el user_id para depuración
        print(f"Loaded user_id: {user_id}")
        return user
    except ValueError:
        # En caso de que la conversión falle, registrar el error
        print(f"Error al convertir user_id: {user_id}")
        return None


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Inicio de sesión exitoso.', 'success')

            # Verificar si el usuario es el admin
            if form.email.data == 'admin.improplac@example.com':
                return redirect(url_for('dashboard'))  # Redirige a la página de administración
            else:
                return redirect(url_for('index'))  # Redirige a la página principal

        else:
            flash('Correo electrónico o contraseña incorrectos.', 'danger')
    context = get_context_data()

    return render_template('login.html', ** context, form=form)

@app.route('/logout')
@login_required  # Asegúrate de que el usuario esté logueado
def logout():
    logout_user()  # Cierra la sesión del usuario
    flash('Has cerrado sesión exitosamente.', 'success')  # Mensaje de éxito
    return redirect(url_for('index'))  # Redirige a la página principal





@app.route('/registro', methods=['GET', 'POST'])
def registro():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('El correo electrónico ya está registrado. Por favor, utiliza otro.')
            return redirect(url_for('registro'))

        new_user = User(email=form.email.data)
        new_user.set_password(form.password.data)

        db.session.add(new_user)
        db.session.commit()

        flash('¡Registro exitoso! Ahora puedes iniciar sesión.')
        return redirect(url_for('login_page'))

    return render_template('registro.html', form=form)






@app.route('/update_cart_quantity/<int:producto_id>/<action>', methods=['POST'])
def update_cart_quantity(producto_id, action):
    if not current_user.is_authenticated:
        return 'No autorizado', 403

    carrito = current_user.carrito
    item = next((prod for prod in carrito.productos if prod.producto_id == producto_id), None)  # Buscar el item

    if not item:
        return 'Producto no encontrado en el carrito', 404

    if action == 'increment':
        item.cantidad += 1  # Incrementar la cantidad
    elif action == 'decrement':
        if item.cantidad > 1:  # Evitar que la cantidad sea menor a 1
            item.cantidad -= 1
        else:
            return 'La cantidad no puede ser menor a 1', 400
    else:
        return 'Acción no válida', 400

    # Calcular subtotal, IVA y total
    subtotal = 0
    for prod in carrito.productos:
        producto = Producto.query.get(prod.producto_id)
        if producto:
            subtotal += producto.precio * prod.cantidad

    iva = subtotal * 0.12  # Suponiendo un IVA del 12%
    total = subtotal + iva

    db.session.commit()  # Guardar cambios en la base de datos

    # Devolver los nuevos valores como JSON
    return {
        'subtotal': subtotal,
        'iva': iva,
        'total': total
    }, 200  # OK


@app.route('/agregar_al_carrito/<int:producto_id>', methods=['POST'])
def agregar_al_carrito(producto_id):
    if not current_user.is_authenticated:
        flash('Necesitas iniciar sesión para agregar productos al carrito.', 'warning')
        return redirect(url_for('login_page'))  # Asegúrate de que 'login_page' sea el nombre del endpoint correcto

    # Obtener el carrito del usuario, o crear uno si no existe
    carrito = current_user.carrito
    if not carrito:
        carrito = Carrito(usuario_id=current_user.id)
        db.session.add(carrito)
        db.session.commit()

    # Verificar si el producto ya está en el carrito
    producto_en_carrito = ProductoEnCarrito.query.filter_by(carrito_id=carrito.id, producto_id=producto_id).first()
    if producto_en_carrito:
        producto_en_carrito.cantidad += 1
    else:
        producto_en_carrito = ProductoEnCarrito(carrito_id=carrito.id, producto_id=producto_id, cantidad=1)
        db.session.add(producto_en_carrito)

    db.session.commit()

    flash('Producto agregado al carrito exitosamente.', 'success')
    return redirect(url_for('catalogo'))


@app.route('/remove_from_cart/<int:producto_id>', methods=['POST'])
def remove_from_cart(producto_id):
    # Lógica para eliminar el producto del carrito
    # Ejemplo:
    carrito = current_user.carrito  # O cómo estés accediendo al carrito
    producto = ProductoEnCarrito.query.filter_by(producto_id=producto_id, carrito_id=carrito.id).first()
    if producto:
        db.session.delete(producto)
        db.session.commit()

    # Redirige de vuelta al carrito o a la página deseada
    return redirect(url_for('carrito'))  # Asegúrate de que 'carrito' es el nombre correcto del endpoint

@app.route('/actualizar_stock/<int:producto_id>', methods=['POST'])
def actualizar_stock(producto_id):
    if not current_user.is_authenticated:
        flash('Necesita iniciar sesión para actualizar el stock.', 'warning')
        return redirect(url_for('login_page'))

    producto = Producto.query.get(producto_id)
    if producto:
        nueva_cantidad = request.form.get('cantidad', type=int)
        if nueva_cantidad is not None:
            producto.cantidad = nueva_cantidad
            db.session.commit()
            flash('Cantidad actualizada con éxito.', 'success')
        else:
            flash('Cantidad no válida.', 'danger')
    else:
        flash('Producto no encontrado.', 'danger')

    return redirect(url_for('dashboard'))
def obtener_productos_del_carrito():
    # Suponiendo que tienes un modelo de Carrito y ProductoEnCarrito
    carrito = current_user.carrito  # Obtén el carrito del usuario autenticado
    if carrito is None:
        return []  # Devuelve una lista vacía si el carrito es None
    return carrito.productos  # Devuelve la lista de productos en el carrito
 # Devuelve la lista de productos en el carrito

def calcular_subtotal(productos):
    subtotal = sum(item.producto.precio * item.cantidad for item in productos)  # Cambiar item.precio por item.producto.precio
    return subtotal

@app.context_processor
def inject_cart_count():
    if current_user.is_authenticated:
        carrito = Carrito.query.filter_by(usuario_id=current_user.id).first()
        if carrito:
            cart_count = sum(item.cantidad for item in carrito.productos)
        else:
            cart_count = 0
    else:
        cart_count = 0
    return dict(cart_count=cart_count)



def calcular_iva(subtotal, tasa_iva=0.15):  # 12% de IVA por defecto
    return subtotal * tasa_iva










def get_context_data():
    categorias = Categoria.query.all()  # Obtén todas las categorías
    return {'categorias': categorias}




def get_context_data_noti():
    # Obtener el correo del usuario logeado
    correo_usuario = current_user.email

    # Consultar las notificaciones del usuario logeado
    notificaciones = Notificacion.query.filter_by(correo_usuario=correo_usuario).order_by(Notificacion.timestamp.desc()).all()

    # Construir el contexto
    return {
        'notificaciones': notificaciones
    }



# Define una ruta para la página de inicio
@app.route('/')
def index():
    context = get_context_data()  # Llama a la función

    return render_template('index.html', **context)  # Desempaqueta las categorías


@app.errorhandler(401)
def unauthorized_error(error):
    return render_template('unauthorized.html'), 401



@app.route('/admin')
@login_required
def admin():
    context = get_facturas_context()
    if current_user.email == 'admin.improplac@example.com':
        return render_template('dashboard.html',**context)
    else:
        return unauthorized_error(None)


@app.route('/dashboard')
@login_required
def dashboard():
    context = get_facturas_context()
    if not current_user.is_authenticated:
        flash('Necesita iniciar sesión para ver el panel de control.', 'warning')
        return redirect(url_for('login_page'))

    # Contar productos y usuarios
    total_productos = Producto.query.count()
    total_usuarios = User.query.count()

    # Obtener productos con cantidad menor a 10
    productos_bajo_stock = Producto.query.filter(Producto.cantidad < 10).all()

    # Calcular el total de ventas
    total_ventas = db.session.query(db.func.sum(Factura.total)).scalar() or 0
    total_ventas = float(total_ventas)
    total_ventas_formatted = "${:,.2f}".format(total_ventas)

    # Obtener los productos más vendidos (máximo 10)
    productos_mas_vendidos_query = db.session.query(
        Producto,
        db.func.sum(FacturaProducto.cantidad).label('total_vendido')
    ).join(FacturaProducto, Producto.id == FacturaProducto.producto_id
    ).group_by(Producto.id
    ).order_by(db.func.sum(FacturaProducto.cantidad).desc()
    ).limit(10).all()

    productos_mas_vendidos = [(producto, total_vendido) for producto, total_vendido in productos_mas_vendidos_query]

    # Obtener estadísticas de los productos más vendidos por mes
    ventas_mensuales = db.session.query(
        db.func.to_char(Factura.fecha, 'YYYY-MM').label('mes'),
        db.func.sum(Factura.total).label('total_ventas')
    ).group_by(db.func.to_char(Factura.fecha, 'YYYY-MM')).all()

    # Generar gráfico de ventas mensuales
    labels = [venta[0] for venta in ventas_mensuales]
    data = [float(venta[1]) for venta in ventas_mensuales]

    # Pasar datos a la plantilla
    return render_template('dashboard.html',
                          total_productos=total_productos,
                          total_usuarios=total_usuarios,
                          productos_bajo_stock=productos_bajo_stock,
                          total_ventas=total_ventas_formatted,
                          productos_mas_vendidos=productos_mas_vendidos,
                          labels=labels,
                          data=data, **context)


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return jsonify({'error': 'Token CSRF inválido o ausente'}), 400


def get_facturas_context():
    # Obtener la cantidad de facturas pendientes
    facturas_pendientes_count = Factura.query.filter(Factura.estado == 'Pendiente').count()


    # Crear un diccionario con los datos relacionados con las facturas
    context = {
        'facturas_pendientes_count': facturas_pendientes_count,
        # Puedes agregar más datos relacionados con las facturas aquí si es necesario
    }

    return context


@app.route('/usuarios', methods=['GET'])
def usuarios():
    context = get_facturas_context()
    buscar = request.args.get('buscar', '')
    page = request.args.get('page', 1, type=int)

    if buscar:
        userdata = Persona.query.filter(
            Persona.nombre.ilike(f'%{buscar}%') |
            Persona.cedula.ilike(f'%{buscar}%')
        ).paginate(page=page, per_page=10)
    else:
        userdata = Persona.query.paginate(page=page, per_page=10)

    return render_template('usuarios.html', personas=userdata, **context)


@app.route('/categorias', methods=['GET'])
def categorias():
    context = get_facturas_context()
    buscar = request.args.get('buscar', '')
    page = request.args.get('page', 1, type=int)

    if buscar:
        categorias = Categoria.query.filter(Categoria.nombre.ilike(f'%{buscar}%')).paginate(page=page, per_page=10)
    else:
        categorias = Categoria.query.paginate(page=page, per_page=10)

    return render_template('categorias.html', categorias=categorias, buscar=buscar, **context)







@app.route('/somos')
def somos():
    context = get_context_data()  # Llama a la función
    return render_template('somos.html', **context)

@app.route('/sucursales')
def sucursales():
    context = get_context_data()
    return render_template('sucursales.html', **context)

@app.route('/carrusel')
def carrusel():
    context = get_facturas_context()
    return render_template('carrusel.html',**context)



@app.route('/productos', methods=['GET'])
def productos():
    context = get_facturas_context()
    buscar = request.args.get('buscar', '')
    page = request.args.get('page', 1, type=int)

    if buscar:
        productos = Producto.query.filter(Producto.nombre.ilike(f'%{buscar}%')).paginate(page=page, per_page=10)
    else:
        productos = Producto.query.paginate(page=page, per_page=10)

    return render_template('productos.html', productos=productos, buscar=buscar, **context)

def convertir_imagen_base64(imagen_binaria):
    if isinstance(imagen_binaria, bytes):
        return base64.b64encode(imagen_binaria).decode('utf-8')
    else:
        raise TypeError("Expected a bytes-like object, got {0}".format(type(imagen_binaria)))

@app.template_filter('b64encode')
def b64encode_filter(data):
    if isinstance(data, bytes):
        return base64.b64encode(data).decode('utf-8')
    return ''

@app.route('/nuevo', methods=['GET'])
def nuevo():
    productos = Producto.query.all()
    for prod in productos:
        prod.imagen = convertir_imagen_base64(prod.imagen)
    return render_template('nuevo.html', productos=productos)


@app.route('/individual/<int:producto_id>')
def individual(producto_id):
    context = get_context_data()
    prod = Producto.query.get_or_404(producto_id)
    return render_template('individual.html', **context, producto=prod)




@app.route('/catalogo', defaults={'categoria_nombre': None})
@app.route('/catalogo/<string:categoria_nombre>')
def catalogo(categoria_nombre):
    if categoria_nombre:
        productos = (
            db.session.query(Producto)
            .join(Categoria)
            .filter(Categoria.nombre == categoria_nombre)
            .all()
        )
    else:
        productos = Producto.query.all()

    context = get_context_data()

    # Convertir imágenes a base64 solo si existen

    return render_template('catalogo.html', **context, productos=productos, categoria_nombre=categoria_nombre)



@app.route('/nuevo_productos', methods=['GET', 'POST'])
def nuevo_productos():
    context = get_facturas_context()
    form = formproducto()
    categorias = Categoria.query.all()  # Obtén todas las categorías de la base de datos
    form.categoria.choices = [(categoria.id, categoria.nombre) for categoria in categorias]  # Ajusta las opciones del SelectField

    if form.validate_on_submit():
        # Obtén la categoría seleccionada usando el ID
        categoria = Categoria.query.get(form.categoria.data)  # Asegúrate de que esto sea el ID de la categoría

        # Maneja la imagen
        imagen = None
        if 'imagen' in request.files:
            imagen_file = request.files['imagen']
            if imagen_file:  # Verifica si se ha subido un archivo
                imagen = imagen_file.read()  # Lee el archivo como bytes

        # Crea el producto
        productos = Producto(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            cantidad=form.cantidad.data,
            precio=form.precio.data,
            categoria=categoria,  # Asigna la instancia de Categoria
            imagen=imagen
        )

        db.session.add(productos)
        try:
            db.session.commit()
            flash('Producto creado exitosamente', 'success')
            return redirect(url_for('productos'))  # Asegúrate de que 'productos' es el nombre correcto de tu vista
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el producto: {}'.format(str(e)), 'danger')

    return render_template('nuevoproducto.html', form=form, **context )


@app.route('/nuevo_categoria', methods=['GET', 'POST'])
def nuevo_categoria():
    context = get_facturas_context()
    form = formcategoria()
    if form.validate_on_submit():
        categorias = Categoria(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
        )
        db.session.add(categorias)
        try:
            db.session.commit()
            flash('Categoría creado exitosamente', 'success')
            return redirect(url_for('categorias'))  # Asegúrate de que 'admin' es el nombre correcto de tu vista
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el categoria: {}'.format(str(e)), 'danger')

    return render_template('crearcategoria.html', form=form,**context)



@app.route('/eliminar_producto/<int:producto_id>', methods=['POST'])
def eliminar_producto(producto_id):
    productos = Producto.query.get_or_404(producto_id)
    try:
        db.session.delete(productos)
        db.session.commit()
        flash('Producto eliminada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar el producto: {}'.format(str(e)), 'danger')
    return redirect(url_for('productos'))

@app.route('/eliminar_categoria/<int:categoria_id>', methods=['POST'])
def eliminar_categoria(categoria_id):
    categ = Categoria.query.get_or_404(categoria_id)
    try:
        db.session.delete(categ)
        db.session.commit()
        flash('Categoría eliminada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar la categoría: {}'.format(str(e)), 'danger')
    return redirect(url_for('categorias'))

@app.route('/eliminar_persona/<int:persona_id>', methods=['POST'])
def eliminar_persona(persona_id):
    persona = Persona.query.get_or_404(persona_id)
    try:
        db.session.delete(persona)
        db.session.commit()
        flash('Persona eliminada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar la persona: {}'.format(str(e)), 'danger')
    return redirect(url_for('usuarios'))


@app.route('/carrito')
def carrito():
    if not current_user.is_authenticated:
        flash('Necesita iniciar sesión para ver el carrito.', 'warning')
        return redirect(url_for('login_page'))

    # Obtener el carrito del usuario actual y asegurarse de que no esté completado
    carrito = current_user.carrito



    # Obtener los productos del carrito
    productos = carrito.productos if carrito else []

    # Calcular subtotal, IVA y total
    subtotal = 0
    totalmaximo=0
    for prod in productos:
        producto = Producto.query.get(prod.producto_id)
        if producto:
            subtotal += producto.precio * prod.cantidad * (1 - 0.15)
            totalmaximo += producto.precio * prod.cantidad

    iva = round(totalmaximo * 0.15, 2)  # Supongamos que el IVA es del 12%
    total = round(subtotal + iva, 2)

    # Obtener cualquier otro contexto necesario
    context = get_context_data()
    context.update({
        'productos': productos,
        'subtotal': format(subtotal, '.2f'),
        'iva': format(iva, '.2f'),
        'total': format(total, '.2f'),
    })

    return render_template('carritocompras.html', **context)



@app.route('/search', methods=['GET'])
def search():
    context = get_context_data()
    query = request.args.get('q')
    productos = Producto.query.filter(Producto.nombre.ilike(f'%{query}%')).all()
    return render_template('catalogo.html', productos=productos, **context)

def calcular_materiales_cielo_pvc_25(metros_cuadrados):
    primarios = round(metros_cuadrados * 0.224, 0)
    secundarios = primarios * 2
    angulos = primarios * 2 + 1
    tornillos_estructura = round(secundarios * 8)
    cielo_pvc = round(metros_cuadrados / 1.49)
    remate_pvc = round(metros_cuadrados * 0.11)
    union_pvc = round(metros_cuadrados * 0.01)
    clavos = round(remate_pvc * 31)
    tornillo_plancha = round(cielo_pvc * 12)

    return {
        'primarios': primarios,
        'secundarios': secundarios,
        'angulos': angulos,
        'tornillos_estructura': tornillos_estructura,
        'cielo_pvc': cielo_pvc,
        'remate_pvc': remate_pvc,
        'union_pvc': union_pvc,
        'clavos': clavos,
        'tornillo_plancha': tornillo_plancha
    }

def calcular_materiales_cielo_pvc_30(metros_cuadrados):
    primarios = round(metros_cuadrados * 0.224, 0)
    secundarios = primarios * 2
    angulos = primarios * 2 + 1
    tornillos_estructura = round(secundarios * 8)
    cielo_pvc = round(metros_cuadrados / 1.69)
    remate_pvc = round(metros_cuadrados * 0.09)
    union_pvc = round(metros_cuadrados * 0.01)
    clavos = round(remate_pvc * 31)
    tornillo_plancha = round(cielo_pvc * 12)

    return {
        'primarios': primarios,
        'secundarios': secundarios,
        'angulos': angulos,
        'tornillos_estructura': tornillos_estructura,
        'cielo_pvc': cielo_pvc,
        'remate_pvc': remate_pvc,
        'union_pvc': union_pvc,
        'clavos': clavos,
        'tornillo_plancha': tornillo_plancha
    }

def calcular_materiales_piso_pvc(numero_barrederas, piso_pvc_metro, area_instalar):
    piezas_pvc = round(area_instalar / piso_pvc_metro, 2)
    barrederas = round(area_instalar / numero_barrederas, 2)

    return {
        'piezas_pvc': piezas_pvc,
        'barrederas': barrederas
    }

@app.route('/calculadora', methods=['GET', 'POST'])
def calculadora():
    context = get_context_data()
    materiales_25cm = {}
    materiales_30cm = {}
    materiales_piso = {}
    tipo = request.form.get('tipo')  # '25cm', '30cm', o 'piso'

    if request.method == 'POST':
        if tipo == '25cm':
            metros_cuadrados = float(request.form.get('metros_cuadrados', 0))
            materiales_25cm = calcular_materiales_cielo_pvc_25(metros_cuadrados)
        elif tipo == '30cm':
            metros_cuadrados = float(request.form.get('metros_cuadrados', 0))
            materiales_30cm = calcular_materiales_cielo_pvc_30(metros_cuadrados)
        elif tipo == 'piso':
            numero_barrederas = float(request.form.get('numero_barrederas', 0))
            piso_pvc_metro = float(request.form.get('piso_pvc_metro', 0))
            area_instalar = float(request.form.get('area_instalar', 0))
            materiales_piso = calcular_materiales_piso_pvc(numero_barrederas, piso_pvc_metro, area_instalar)

    return render_template('calculadora.html',**context,  materiales_25cm=materiales_25cm, materiales_30cm=materiales_30cm, materiales_piso=materiales_piso)


def obtener_carrito_actual():
    if not current_user.is_authenticated:
        return None  # O maneja el caso cuando el usuario no está logueado

    # Obtener el carrito del usuario actual
    return Carrito.query.filter_by(usuario_id=current_user.id).first()


CIUDADES_ECUADOR = [
    ("Quito", "Quito"),
    ("Guayaquil", "Guayaquil"),
    ("Cuenca", "Cuenca"),
    ("Santo Domingo", "Santo Domingo"),
    ("Machala", "Machala"),
    ("Manta", "Manta"),
    ("Portoviejo", "Portoviejo"),
    ("Ambato", "Ambato"),
    ("Riobamba", "Riobamba"),
    ("Loja", "Loja"),
    ("Ibarra", "Ibarra"),
    ("Latacunga", "Latacunga"),
    ("Esmeraldas", "Esmeraldas"),
    ("Tulcán", "Tulcán"),
    ("Otavalo", "Otavalo"),
    ("Azogues", "Azogues"),
    ("Biblián", "Biblián"),
    ("La Troncal", "La Troncal"),
    ("Guaranda", "Guaranda"),
    ("San Miguel", "San Miguel"),
    ("Chillanes", "Chillanes"),
    ("Santa Rosa", "Santa Rosa"),
    ("Huaquillas", "Huaquillas"),
    ("Pasaje", "Pasaje"),
    ("Zaruma", "Zaruma"),
    ("Arenillas", "Arenillas"),
    ("Baños de Agua Santa", "Baños de Agua Santa"),
    ("Pelileo", "Pelileo"),
    ("Nueva Loja", "Nueva Loja"),
    ("Shushufindi", "Shushufindi"),
    ("Cuyabeno", "Cuyabeno"),
    ("Puerto Ayora", "Puerto Ayora"),
    ("Puerto Baquerizo Moreno", "Puerto Baquerizo Moreno"),
    ("Puerto Villamil", "Puerto Villamil"),
    ("Catamayo", "Catamayo"),
    ("Macará", "Macará"),
    ("Vilcabamba", "Vilcabamba"),
    ("Babahoyo", "Babahoyo"),
    ("Quevedo", "Quevedo"),
    ("Ventanas", "Ventanas"),
    ("Vinces", "Vinces"),
    ("Chone", "Chone"),
    ("Jipijapa", "Jipijapa"),
    ("Montecristi", "Montecristi"),
    ("Macas", "Macas"),
    ("Gualaquiza", "Gualaquiza"),
    ("Sucúa", "Sucúa"),
    ("Tena", "Tena"),
    ("Archidona", "Archidona"),
    ("Misahuallí", "Misahuallí"),
    ("Coca", "Coca"),
    ("Dayuma", "Dayuma"),
    ("Pompeya", "Pompeya"),
    ("Puyo", "Puyo"),
    ("Shell", "Shell"),
    ("Arajuno", "Arajuno"),
    ("Sangolquí", "Sangolquí"),
    ("Machachi", "Machachi"),
    ("Cayambe", "Cayambe"),
    ("San Antonio de Pichincha", "San Antonio de Pichincha"),
    ("La Libertad", "La Libertad"),
    ("Salinas", "Salinas"),
    ("La Concordia", "La Concordia"),
    ("Guano", "Guano"),
    ("Penipe", "Penipe"),
    ("Alausí", "Alausí"),
    ("Chunchi", "Chunchi"),
    ("Zamora", "Zamora"),
    ("Yantzaza", "Yantzaza"),
    ("Nangaritza", "Nangaritza"),
]

@app.route('/datospago', methods=['GET', 'POST'])
@login_required  # Asegúrate de que el usuario esté logueado
def datospago():

    productos = obtener_productos_del_carrito()
    if not productos:
        flash('Tu carrito está vacío. Por favor, agrega productos antes de proceder a realizar el pedido.', 'warning')
        return redirect(url_for('carrito'))

    subtotal = calcular_subtotal(productos) * (1 - 0.15)
    totalmaximo =calcular_subtotal(productos)
    iva = calcular_iva(totalmaximo)
    total = (subtotal + iva)

    form = PersonaForm()
    form.ciudad.choices = CIUDADES_ECUADOR

    # Obtener el correo electrónico del usuario logueado
    user_email = current_user.email

    # Buscar la persona con el correo del usuario logueado
    persona = Persona.query.filter_by(correo=user_email).first()

    if persona:
        if form.validate_on_submit():
            try:
                # Actualizar los datos de la persona existente
                persona.nombre = form.nombre.data
                persona.direccion = form.direccion.data
                persona.telefono = form.telefono.data
                persona.cedula = form.cedula.data
                persona.ciudad = form.ciudad.data

                db.session.commit()
                flash('Los datos han sido actualizados exitosamente.', 'success')
                return redirect(url_for('factura'))  # Redirige para mostrar la factura
            except IntegrityError:
                db.session.rollback()  # Hacer rollback en caso de error
                flash('Error: Ya existe un registro con la misma cédula.', 'danger')
                return redirect(url_for('datospago'))

    else:
        if form.validate_on_submit():
            try:
                # Verificar si ya existe un registro con la misma cédula
                if Persona.query.filter_by(cedula=form.cedula.data).first():
                    # Si la cédula ya existe, no creamos un nuevo registro y redirigimos a la página de factura
                    flash('Ya existe un registro con la misma cédula. Los datos serán actualizados.', 'warning')
                    # Actualizar los datos de la persona existente en la base de datos
                    persona = Persona.query.filter_by(cedula=form.cedula.data).first()
                    persona.nombre = form.nombre.data
                    persona.correo = form.correo.data
                    persona.direccion = form.direccion.data
                    persona.telefono = form.telefono.data
                    persona.ciudad = form.ciudad.data
                    db.session.commit()
                    return redirect(url_for('factura'))  # Redirige a la página de factura

                # Crear nuevo registro de persona
                persona = Persona(
                    nombre=form.nombre.data,
                    correo=form.correo.data,
                    direccion=form.direccion.data,
                    telefono=form.telefono.data,
                    cedula=form.cedula.data,
                    ciudad=form.ciudad.data
                )
                db.session.add(persona)
                db.session.commit()

                flash('La persona ha sido registrada exitosamente.', 'success')
                return redirect(url_for('factura'))  # Redirige a la página de factura
            except IntegrityError:
                db.session.rollback()  # Hacer rollback en caso de error
                flash('Error: Ya existe un registro con la misma cédula.', 'danger')
                return redirect(url_for('datospago'))

    # Rellenar el formulario con los datos existentes si los hay
    if persona:
        form.nombre.data = persona.nombre
        form.correo.data = persona.correo
        form.direccion.data = persona.direccion
        form.telefono.data = persona.telefono
        form.cedula.data = persona.cedula
        form.ciudad.data = persona.ciudad

    context = {
        'productos': productos,
        'subtotal': format(subtotal, '.2f'),
        'iva': format(iva, '.2f'),
        'total': format(total, '.2f'),
        'form': form
    }

    return render_template('datospagar.html', **context)


@app.route('/factura')
@login_required
def factura():
    productos_carrito = obtener_productos_del_carrito()
    if not productos_carrito:
        flash('Tu carrito está vacío. No se puede generar la orden de pedido.', 'warning')
        return redirect(url_for('carrito'))

    # Obtener el usuario actual
    user_email = current_user.email
    persona = Persona.query.filter_by(correo=user_email).first()

    if not persona:
        flash('No se encontraron datos de la persona. Por favor, completa tus datos de registro.', 'warning')
        return redirect(url_for('datospago'))

    # Calcular subtotal, IVA y total
    subtotal = calcular_subtotal(productos_carrito) * (1 - 0.15)
    totalmaximo=calcular_subtotal(productos_carrito)
    iva = calcular_iva(totalmaximo)
    total = subtotal + iva

    # Generar un número de orden de pedido aleatorio
    numero_orden = random.randint(10000, 99999)

    context = {
        'persona': persona,
        'productos': productos_carrito,
        'subtotal': subtotal,
        'iva': format(iva, '.2f'),
        'total': total,
        'numero_orden': numero_orden
    }

    return render_template('factura.html', **context)

@app.route('/finalizar_pedido', methods=['POST'])
@login_required
def finalizar_pedido():
    carrito = current_user.carrito

    if carrito is None or carrito.id is None:
        flash('No hay productos en el carrito o el carrito no tiene un ID válido.', 'warning')
        return redirect(url_for('catalogo'))

    productos_carrito = carrito.productos

    if not productos_carrito:
        flash('El carrito está vacío.', 'warning')
        return redirect(url_for('catalogo'))

    total = sum(item.producto.precio * item.cantidad for item in productos_carrito)

    persona = Persona.query.filter_by(correo=current_user.email).first()
    if persona is None:
        flash('No se pudo encontrar la información de la persona asociada.', 'error')
        return redirect(url_for('catalogo'))

    try:
        # Generar un número de pedido único
        prefijo = "PED"
        numeros = ''.join(random.choices(string.digits, k=8))
        numero_pedido = f"{prefijo}{numeros}"

        # Crear una nueva factura
        factura = Factura(
            carrito_id=carrito.id,
            persona_id=persona.id,
            total=total,
            numero_pedido=numero_pedido,
            estado='Pendiente'  # Asignar estado de pedido a 'Pendiente'
        )
        db.session.add(factura)
        db.session.commit()
        print(f"Factura creada: {factura}")

        # Añadir productos a la factura
        for item in productos_carrito:
            factura_producto = FacturaProducto(
                factura_id=factura.id,
                producto_id=item.producto_id,
                cantidad=item.cantidad,
                precio=item.producto.precio
            )
            db.session.add(factura_producto)
        db.session.commit()
        print("Productos añadidos a la factura.")

        # Actualizar el stock de los productos
        for item in productos_carrito:
            producto_db = Producto.query.filter_by(id=item.producto_id).first()
            if producto_db:
                producto_db.cantidad -= item.cantidad
                db.session.add(producto_db)
        db.session.commit()
        print("Stock de productos actualizado.")

        # Marcar los productos del carrito como procesados
        for item in productos_carrito:
            db.session.delete(item)
        db.session.commit()
        print("Productos del carrito eliminados.")

        # Marcar el carrito como completado
        carrito.completado = True
        db.session.add(carrito)
        db.session.commit()
        print("Carrito marcado como completado.")

        flash('¡Tu pedido ha sido procesado exitosamente! Hemos recibido tu solicitud y estamos trabajando para preparar y enviar tus productos lo antes posible. ¡Gracias por elegirnos!', 'success')

    except IntegrityError as e:
        db.session.rollback()
        flash('Hubo un error al procesar tu pedido. Por favor, intenta de nuevo.', 'error')
        print(f'Error de Integridad: {e}')
        print("Datos en la base de datos después del error:")
        facturas = Factura.query.all()
        for f in facturas:
            print(f.id, f.carrito_id, f.persona_id, f.total)

    return redirect(url_for('catalogo'))


@app.route('/perfil')
@login_required
def perfil():
    persona = Persona.query.filter_by(correo=current_user.email).first()

    if persona is None:
        flash('No se pudo encontrar la información de la persona asociada.', 'error')
        return redirect(url_for('index'))

    facturas = Factura.query.filter_by(persona_id=persona.id).all()

    # Formatear el total de cada factura a dos decimales
    for factura in facturas:
        factura.total_formateado = "{:.2f}".format(factura.total)

    return render_template('perfiluser.html', facturas=facturas)


from datetime import datetime
from sqlalchemy import extract


@app.route('/pedidos', methods=['GET', 'POST'])
@login_required
def pedidos():
    context = get_facturas_context()
    # Obtener parámetros de la consulta para los filtros
    page = request.args.get('page', 1, type=int)
    mes = request.args.get('mes', type=int)
    estado = request.args.get('estado', type=str)

    # Filtrar las facturas según los parámetros recibidos
    query = Factura.query.join(Persona)

    # Filtrar para incluir solo fechas hasta la fecha actual
    query = query.filter(Factura.fecha <= datetime.now())

    if mes:
        # Filtrar por mes usando 'extract'
        query = query.filter(extract('month', Factura.fecha) == mes)

    if estado:
        # Filtrar por estado
        query = query.filter(Factura.estado == estado)

    # Ordenar por año y mes de forma decreciente
    query = query.order_by(
        extract('year', Factura.fecha).desc(),
        extract('month', Factura.fecha).desc(),
    extract('day', Factura.fecha).desc()
    )

    # Obtener las facturas paginadas
    facturas = query.paginate(page=page, per_page=10)

    # Formatear el total de cada factura a dos decimales
    for factura in facturas.items:
        factura.total_formateado = "{:.2f}".format(factura.total)
        # Aquí accede al nombre de la persona a través de la relación
        factura.persona_nombre = factura.persona.nombre

    # Cálculos para mostrar el total de pedidos y el monto total
    total_pedidos = Factura.query.filter(Factura.fecha <= datetime.now()).count()
    total_monto = Factura.query.filter(Factura.fecha <= datetime.now()).with_entities(db.func.sum(Factura.total)).scalar() or 0

    return render_template('adminpedidos.html', facturas=facturas, total_pedidos=total_pedidos, total_monto=total_monto, **context)

@app.route('/eliminar_pedido/<int:id>', methods=['POST'])
@login_required
def eliminar_pedido(id):
    # Obtener la factura con el ID proporcionado
    factura = Factura.query.get(id)

    # Verificar si la factura existe
    if factura is None:
        flash('Factura no encontrada.', 'error')
        return redirect(url_for('pedidos'))

    # Eliminar la factura (esto también debería eliminar los productos asociados gracias a cascade='all, delete-orphan')
    db.session.delete(factura)
    try:
        db.session.commit()
        flash('Pedido eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Ocurrió un error al eliminar el pedido.', 'error')
        print(e)

    return redirect(url_for('pedidos'))


@app.route('/actualizar_estado_pedido/<int:id>', methods=['POST'])
@login_required
def actualizar_estado_pedido(id):
    estado = request.form.get('estado')
    factura = Factura.query.get_or_404(id)
    factura.estado = estado
    db.session.commit()

    # Crear una notificación
    usuario = Persona.query.get(factura.persona_id)  # Obtén la persona asociada con la factura
    if usuario:
        mensaje = f'El estado del pedido {factura.numero_pedido} ha sido actualizado a {estado}.'
        notificacion = Notificacion(
            mensaje=mensaje,
            correo_usuario=usuario.correo  # Usa el correo electrónico del usuario
        )
        db.session.add(notificacion)
        db.session.commit()

    flash('El estado del pedido ha sido actualizado y se ha creado una notificación.', 'success')
    return redirect(url_for('pedidos'))


@app.route('/editar_persona/<int:persona_id>', methods=['GET', 'POST'])
def editar_persona(persona_id):
    # Obtener la persona desde la base de datos
    context = get_facturas_context()
    persona = Persona.query.get_or_404(persona_id)

    # Crear el formulario de edición
    form = EditarPersonaForm(obj=persona)

    # Si el formulario se envía y es válido
    if form.validate_on_submit():
        # Actualizar los datos de la persona
        persona.nombre = form.nombre.data
        persona.direccion = form.direccion.data
        persona.telefono = form.telefono.data
        persona.cedula = form.cedula.data
        persona.ciudad = form.ciudad.data

        # Guardar los cambios en la base de datos
        try:
            db.session.commit()
            flash('Persona actualizada exitosamente', 'success')
            return redirect(url_for('usuarios'))  # Redirige a la lista de personas (o la URL que prefieras)
        except Exception as e:
            db.session.rollback()
            flash(f'Ocurrió un error al actualizar la persona: {e}', 'danger')

    # Si la solicitud es GET o el formulario no es válido, mostramos el formulario con los datos actuales
    return render_template('editarpersona.html', persona=persona, form=form, **context)


@app.route('/editar_categoria/<int:categoria_id>', methods=['GET', 'POST'])
def editar_categoria(categoria_id):
    context = get_facturas_context()
    categoria = Categoria.query.get_or_404(categoria_id)
    form = EditarCategoriaForm(obj=categoria)  # Cargar los datos actuales de la categoría

    if form.validate_on_submit():
        categoria.nombre = form.nombre.data
        categoria.descripcion = form.descripcion.data

        try:
            db.session.commit()
            flash('Categoría actualizada exitosamente.', 'success')
            return redirect(url_for('categorias'))  # Redirige a la página de lista de categorías
        except Exception as e:
            db.session.rollback()
            flash('Hubo un error al actualizar la categoría.', 'danger')

    return render_template('editar_categoria.html', form=form, categoria=categoria, **context)

@app.route('/crear_persona', methods=['GET', 'POST'])
def crear_persona():
    context = get_facturas_context()
    form = CrearPersonaForm()
    if form.validate_on_submit():
        # Crear una nueva persona con los datos del formulario
        nueva_persona = Persona(
            nombre=form.nombre.data,
            direccion=form.direccion.data,
            telefono=form.telefono.data,
            cedula=form.cedula.data,
            ciudad=form.ciudad.data
        )
        # Agregar la nueva persona a la base de datos
        db.session.add(nueva_persona)
        db.session.commit()

        # Redirigir a la lista de personas
        return redirect(url_for('usuarios'))

    return render_template('crearpersona.html', form=form, **context)


@app.route('/editar_producto/<int:producto_id>', methods=['GET', 'POST'])
def editar_producto(producto_id):
    context = get_facturas_context()
    producto = Producto.query.get_or_404(producto_id)
    form = EditarProductoForm(obj=producto)

    if form.validate_on_submit():
        producto.nombre = form.nombre.data
        producto.descripcion = form.descripcion.data
        producto.precio = form.precio.data
        producto.cantidad = form.cantidad.data
        producto.categoria_id = form.categoria_id.data

        # Verificar si se cargó una nueva imagen
        if form.imagen.data:
            # Obtener el archivo de imagen
            imagen = form.imagen.data
            # Leer la imagen como binario
            imagen_binaria = imagen.read()
            # Actualizar el campo imagen con los datos binarios
            producto.imagen = imagen_binaria

        try:
            db.session.commit()
            flash('Producto actualizado exitosamente.', 'success')
            return redirect(url_for('productos'))  # Redirige a la página de lista de productos
        except Exception as e:
            db.session.rollback()
            flash('Hubo un error al actualizar el producto.', 'danger')

    return render_template('editar_producto.html', form=form, producto=producto, **context)

@app.route('/editar_stock_producto/<int:producto_id>', methods=['POST'])
def editar_stock_producto(producto_id):

    nuevo_stock = request.form.get('nuevo_stock')
    if nuevo_stock is not None:
        producto = Producto.query.get_or_404(producto_id)
        producto.cantidad = int(nuevo_stock)
        db.session.commit()
        flash(f'Stock de {producto.nombre} actualizado correctamente.', 'success')
    else:
        flash('Error al actualizar el stock.', 'danger')
    return redirect(url_for('dashboard'))


@app.route('/pedido/<int:id>/descargar', methods=['GET'])
@login_required
def descargar_pedido(id):
    # Obtener la factura y sus productos
    factura = Factura.query.get_or_404(id)
    persona = factura.persona  # Acceso directo a la persona asociada a la factura
    productos = factura.productos  # Productos asociados a la factura

    # Configuración del PDF
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle(f"Pedido_{factura.numero_pedido}")

    # Datos de la Empresa
    empresa_ruc = "RUC: 1805350475"
    empresa_direccion = "Vía a San Luis, barrio La Floresta"
    empresa_telefono = "Tel: 098498356"
    fecha_emision = factura.fecha.strftime('%d/%m/%Y')  # Fecha de emisión de la factura

    # Logo de la Empresa (ruta del logo en static)
    logo_path = "app/static/img/improplac.png"  # Ruta del logo
    pdf.drawImage(logo_path, 50, 750, width=100, height=50)

    # Encabezado: Datos de la Empresa
    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(400, 745, empresa_ruc)
    pdf.drawString(400, 730, empresa_direccion)
    pdf.drawString(400, 715, empresa_telefono)

    # Línea horizontal para separar el encabezado
    pdf.setLineWidth(1)
    pdf.line(50, 700, 550, 700)

    # Número de Factura y Fecha de Emisión
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, 680, f"Pedido No: {factura.numero_pedido}")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(400, 680, f"Fecha: {fecha_emision}")

    # Datos del Cliente
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 650, f"Cliente: {persona.nombre}")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, 635, f"Cédula: {persona.cedula}")  # Ajusté la coordenada Y para evitar solapamiento
    pdf.drawString(50, 620, f"Dirección: {persona.direccion}")
    pdf.drawString(50, 605, f"Teléfono: {persona.telefono}")  # Ajusté la coordenada Y
    pdf.drawString(50, 590, f"Email: {persona.correo}")  # Ajusté la coordenada Y

    # Título para detalles de pedido
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, 570, f"Detalles del Pedido")

    # Tabla de productos
    data = [["Producto", "Cantidad", "Precio Unitario", "Subtotal"]]
    total_pedido = 0

    for fp in productos:
        subtotal = fp.cantidad * fp.precio
        data.append([
            fp.producto.nombre,
            str(fp.cantidad),
            f"${fp.precio:.2f}",
            f"${subtotal:.2f}"
        ])
        total_pedido += subtotal

    # Añadir fila de total
    data.append(["", "", "Total", f"${total_pedido:.2f}"])

    # Crear tabla
    table = Table(data, colWidths=[200, 100, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),  # Fondo azul oscuro
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Texto en blanco
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Alinear el texto al centro
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Líneas de la cuadrícula en negro
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Fuente en negrita
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Espaciado en la parte inferior
    ]))

    # Dibujar la tabla en el PDF
    table.wrapOn(pdf, 50, 480)  # Ajusté la posición para que no se solape
    table.drawOn(pdf, 50, 430)  # Ajusté la posición de la tabla

    # Pie de página
    pdf.setFont("Helvetica", 8)
    pdf.drawString(50, 50, "Gracias por su compra. Para más información, contacte a nuestro servicio al cliente.")

    # Finalizar el PDF
    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    # Enviar PDF como respuesta
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="Factura_{factura.numero_pedido}.pdf"'
    return response


@app.route('/productos_en_oferta', methods=['GET'])
def productos_en_oferta():
    context = get_facturas_context()
    # Filtrar productos que están en oferta
    productos = Producto.query.filter_by(en_oferta=True).all()
    return render_template('productos_en_oferta.html', productos=productos,**context)

@app.route('/quitar_oferta/<int:producto_id>', methods=['POST'])
def quitar_oferta(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    producto.en_oferta = False
    db.session.commit()
    return redirect(url_for('productos_en_oferta'))

