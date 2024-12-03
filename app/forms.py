from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField,FloatField,SelectField,SubmitField, FileField,EmailField
from wtforms.validators import DataRequired
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
import re
from app.models import Producto,Categoria

class formcategoria (FlaskForm):
    nombre= StringField('nombre categoría',validators=[DataRequired()])
    descripcion=StringField('descripcion',validators=[DataRequired()])
    submit= SubmitField('Crear categoria')


class RegistrationForm(FlaskForm):
    email = StringField('Correo electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[
        DataRequired(),
        Length(min=8),
        # Validador personalizado para verificar la fortaleza de la contraseña
        lambda form, field: bool(re.match(r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*()-_+=])[0-9a-zA-Z!@#$%^&*()-_+=]{8,128}$', field.data)),
        EqualTo('confirm_password', message='Las contraseñas deben coincidir.')
    ])
    confirm_password = PasswordField('Confirmar contraseña', validators=[DataRequired()])
    submit = SubmitField('Registrarse')

    def validate_password(self, password):
        if not re.match(r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*()-_+=])[0-9a-zA-Z!@#$%^&*()-_+=]{8,128}$', password.data):
            raise ValidationError('La contraseña debe contener al menos una letra mayúscula, una letra minúscula, un número y un carácter especial.')

class LoginForm(FlaskForm):
    email = StringField('Correo electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar sesión')

class formproducto(FlaskForm):
    nombre = StringField('Nombre del Producto', validators=[DataRequired()])
    descripcion = StringField('Descripción', validators=[DataRequired()])
    cantidad = IntegerField('Cantidad', validators=[DataRequired()])
    precio = FloatField('Precio', validators=[DataRequired()])
    categoria = SelectField('Categoría', choices=[('pisos', 'Pisos'), ('pisos', 'Pisos')], validators=[DataRequired()])
    imagen = FileField('Imagen')
    submit = SubmitField('Crear producto')

class PersonaForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    correo = EmailField('Correo', validators=[DataRequired(), Email()])
    direccion = StringField('Dirección', validators=[DataRequired(), Length(max=200)])
    telefono = StringField('Teléfono', validators=[DataRequired(), Length(max=15)])  # Ajusta el máximo según tus necesidades
    cedula = StringField('Número de Cédula', validators=[DataRequired(), Length(max=20)])
    ciudad = StringField('Ciudad', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Registrar Persona')

class EditarPersonaForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    direccion = StringField('Dirección', validators=[DataRequired()])
    telefono = StringField('Teléfono', validators=[DataRequired()])
    cedula = StringField('Cédula', validators=[DataRequired()])
    ciudad = StringField('Ciudad', validators=[DataRequired()])
    submit = SubmitField('Guardar Cambios')

class CrearPersonaForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    direccion = StringField('Dirección', validators=[DataRequired(), Length(max=200)])
    telefono = StringField('Teléfono', validators=[DataRequired(), Length(max=15)])
    cedula = StringField('Cédula', validators=[DataRequired(), Length(max=15)])
    ciudad = StringField('Ciudad', validators=[DataRequired(), Length(max=100)])

class EditarCategoriaForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    descripcion = StringField('Descripción', validators=[DataRequired()])

class EditarProductoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    descripcion = StringField('Descripción')
    precio = FloatField('Precio', validators=[DataRequired()])
    cantidad = IntegerField('Cantidad', validators=[DataRequired()])
    categoria_id = SelectField('Categoría', coerce=int, validators=[DataRequired()])
    imagen = FileField('Imagen')

    def __init__(self, *args, **kwargs):
        super(EditarProductoForm, self).__init__(*args, **kwargs)
        # Llenar el SelectField con las categorías existentes
        self.categoria_id.choices = [(categoria.id, categoria.nombre) for categoria in Categoria.query.all()]