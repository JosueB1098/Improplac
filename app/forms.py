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
def validar_cedula_ecuador(cedula):
    """
    Verifica si una cédula ecuatoriana es válida.
    """
    if len(cedula) != 10 or not cedula.isdigit():
        return False

    provincia = int(cedula[:2])
    if provincia < 1 or provincia > 24:
        return False

    digitos = list(map(int, cedula))
    coeficientes = [2, 1] * 5
    suma = 0

    for i in range(9):
        producto = digitos[i] * coeficientes[i]
        suma += producto if producto < 10 else producto - 9

    verificador = 10 - (suma % 10) if suma % 10 != 0 else 0
    return verificador == digitos[-1]

def validar_telefono_ecuador(telefono):
    """
    Verifica si un número de teléfono ecuatoriano es válido.
    """
    if len(telefono) not in [9, 10] or not telefono.isdigit():
        return False

    if len(telefono) == 9 and telefono.startswith('2'):  # Teléfonos fijos
        return True

    if len(telefono) == 10 and telefono.startswith('09'):  # Celulares
        return True

    return False
class PersonaForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(min=3, max=100)])
    correo = StringField('Correo', validators=[DataRequired(), Email()])
    direccion = StringField('Dirección', validators=[DataRequired(), Length(min=5, max=200)])
    telefono = StringField('Teléfono', validators=[DataRequired(), Length(min=9, max=10)])
    cedula = StringField('Cédula', validators=[DataRequired(), Length(min=10, max=10)])
    ciudad = SelectField('Ciudad', choices=[], validators=[DataRequired()])
    submit = SubmitField('Guardar')

    def validate_cedula(form, field):
        if not validar_cedula_ecuador(field.data):
            raise ValidationError('La cédula ingresada no es válida.')

    def validate_telefono(form, field):
        if not validar_telefono_ecuador(field.data):
            raise ValidationError('El número de teléfono ingresado no es válido.')

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