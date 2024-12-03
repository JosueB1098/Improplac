from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from datetime import datetime
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), index=True, unique=True)
    password_hash = db.Column(db.String(255))
    carrito = db.relationship('Carrito', backref='usuario', uselist=False)

    def __repr__(self):
        return '<User {}>'.format(self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)




class Categoria(db.Model):
    __tablename__ = 'categoria'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(64), index=True)
    descripcion = db.Column(db.String(64), index=True)
    productos = relationship("Producto", back_populates="categoria")  # Relación inversa

class Producto(db.Model):
    __tablename__ = 'producto'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(64), index=True)
    descripcion = db.Column(db.String(256), index=True)
    cantidad = db.Column(db.Integer)
    precio = db.Column(db.Float, index=True)
    categoria_id = db.Column(db.Integer, ForeignKey('categoria.id'))  # Clave foránea
    categoria = relationship("Categoria", back_populates="productos")  # Relación
    imagen = db.Column(db.LargeBinary)
    en_oferta = db.Column(db.Boolean, default=False)
    descuento = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Producto {self.nombre}>'

class Carrito(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    productos = db.relationship('ProductoEnCarrito', backref='carrito', lazy=True)
    completado = db.Column(db.Boolean, default=False)

class ProductoEnCarrito(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    carrito_id = db.Column(db.Integer, db.ForeignKey('carrito.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    fecha_agregado = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    producto = db.relationship('Producto', backref='en_carrito', lazy=True)

class Persona(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), nullable=False, unique=True)
    direccion = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(15), nullable=False)
    cedula = db.Column(db.String(15), nullable=False, unique=True)
    ciudad = db.Column(db.String(100), nullable=False)

    # Relación uno a muchos con Factura
    facturas = db.relationship('Factura', backref='persona', lazy=True)

class Factura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    carrito_id = db.Column(db.Integer, db.ForeignKey('carrito.id'), nullable=False)
    persona_id = db.Column(db.Integer, db.ForeignKey('persona.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, default=db.func.current_timestamp())
    numero_pedido = db.Column(db.String(20), unique=True, nullable=True)
    estado = db.Column(db.String(20), index=True)

    # Relación muchos a uno con Carrito
    carrito = db.relationship('Carrito', backref='facturas', lazy=True)

class FacturaProducto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    factura_id = db.Column(db.Integer, db.ForeignKey('factura.id'), nullable=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=True)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    precio = db.Column(db.Float, nullable=False)

    # Relación muchos a uno con Factura
    factura = db.relationship('Factura', backref='productos', lazy=True)

    # Relación muchos a uno con Producto
    producto = db.relationship('Producto', backref='facturas', lazy=True)

class Notificacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mensaje = db.Column(db.String(255), nullable=False)
    leida = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    correo_usuario = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<Notificacion {self.mensaje}>'