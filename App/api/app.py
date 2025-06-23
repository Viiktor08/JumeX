from flask import Flask, request, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api
from flask_cors import CORS
from datetime import datetime
from flask_praetorian import Praetorian, auth_required, roles_required, current_user
from sqlalchemy.sql import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mariadb+mariadbconnector://usuario:password@mariadb:3306/flask_database'
app.config['SECRET_KEY'] = 'clave_super_segura'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_ACCESS_LIFETIME'] = 7200  # 2 hora
app.config['JWT_REFRESH_LIFETIME'] = 86400  # 24 horas
app.config['JWT_TOKEN_LOCATION'] = ['cookies']

db = SQLAlchemy(app)
CORS(app, supports_credentials=True)
guard = Praetorian()
api = Api(app)


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    proyectos = db.relationship('Proyecto', backref='usuario', lazy=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    es_admin = db.Column(db.Boolean, default=False)
    
    def __init__(self, nombre, apellidos, email, password, es_admin):
        self.nombre = nombre
        self.apellidos = apellidos
        self.email = email
        self.password = guard.hash_password(password)
        self.proyectos = []
        self.es_admin = es_admin
    
    @property
    def rolenames(self):
        return ['admin'] if self.es_admin else ['user']

    @property
    def identity(self):
        return self.id

    @classmethod
    def lookup(cls, email):
        return cls.query.filter_by(email=email).one_or_none()

    @classmethod
    def identify(cls, id):
        return cls.query.get(id)
    
guard.init_app(app, Usuario)

class Proyecto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    fecha = db.Column(db.Date, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    # Criterios de aceptabilidad
    vuln_total_max = db.Column(db.Integer, nullable=True)
    solucionabilidad_min = db.Column(db.Integer, nullable=True)
    nivel_maximo = db.Column(db.String(20), nullable=True)
    formula_combinada = db.Column(db.String(200), nullable=True)
    # Para el informe
    ruta_ultimo_reporte = db.Column(db.String(512), nullable=True)

class SBOM(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    ruta = db.Column(db.String(512), nullable=False)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyecto.id'), nullable=False)

    proyecto = db.relationship("Proyecto", backref="sboms")

class Mensaje(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyecto.id'), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    es_bot = db.Column(db.Boolean, default=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    proyecto = db.relationship('Proyecto', backref=db.backref('mensajes', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'proyecto_id': self.proyecto_id,
            'contenido': self.contenido,
            'es_bot': self.es_bot,
            'fecha': self.fecha.isoformat()
        }

# Recursos
class UsuarioList(Resource):
    @roles_required('admin')
    def get(self):
        usuarios = Usuario.query.all()
        return [{"id": u.id, "nombre": u.nombre, "apellidos": u.apellidos, "email": u.email} for u in usuarios]

    @roles_required('admin')
    def post(self):
        data = request.get_json()
        nombre = data.get('nombre')
        apellidos = data.get('apellidos')
        email = data.get('email')
        password = data.get('password')
        
        usuario = Usuario(nombre=nombre, apellidos=apellidos, email=email, password=password)
        db.session.add(usuario)
        db.session.commit()
        return {'id': usuario.id, 'nombre': usuario.nombre, 'apellidos': usuario.apellidos, 'email': usuario.email}, 201

class ProyectoList(Resource):
    @auth_required
    def get(self):
        if current_user().es_admin:
            proyectos = Proyecto.query.all()
        else:
            proyectos = Proyecto.query.filter_by(usuario_id=current_user().id).all()
        return [{"id": p.id, "nombre": p.nombre, "usuario_id": p.usuario_id, "descripcion": p.descripcion, "fecha": p.fecha.strftime('%d-%m-%Y'), "ruta_ultimo_reporte": p.ruta_ultimo_reporte} for p in proyectos], 200

    @auth_required
    def post(self):
        data = request.get_json()
        nuevo = Proyecto(
            nombre=data['nombre'], 
            usuario_id=current_user().id, 
            descripcion=data.get('descripcion'), 
            fecha=datetime.strptime(data['fecha'], '%d-%m-%Y').date(),
            vuln_total_max=data.get('vuln_total_max'),
            solucionabilidad_min=data.get('solucionabilidad_min'),
            nivel_maximo=data.get('nivel_maximo'),
            formula_combinada=data.get('formula_combinada')
        )
        db.session.add(nuevo)
        db.session.commit()
        return {
            "id": nuevo.id,
            "nombre": nuevo.nombre,
            "usuario_id": nuevo.usuario_id,
            "descripcion": nuevo.descripcion,   
            "fecha": nuevo.fecha.strftime('%d-%m-%Y'),
            "vuln_total_max": nuevo.vuln_total_max,
            "solucionabilidad_min": nuevo.solucionabilidad_min,
            "nivel_maximo": nuevo.nivel_maximo,
            "formula_combinada": nuevo.formula_combinada
        }, 201
        
class UsuarioEditar(Resource):
    @roles_required('admin')
    def put(self, id):
        usuario = Usuario.query.get_or_404(id)
        data = request.get_json()
        usuario.nombre = data.get("nombre", usuario.nombre)
        usuario.apellidos = data.get("apellidos", usuario.apellidos)
        usuario.email = data.get("email", usuario.email)
        db.session.commit()
        return {"id": usuario.id, "nombre": usuario.nombre, "apellidos": usuario.apellidos, "email": usuario.email}
    
    @roles_required('admin')
    def get(self, id):
        usuario = Usuario.query.get_or_404(id)
        return {
            'id': usuario.id,
            'nombre': usuario.nombre,
            'apellidos': usuario.apellidos,
            'email': usuario.email
        }, 200

class UsuarioEliminar(Resource):
    @roles_required('admin')
    def delete(self, id):
        usuario = Usuario.query.get_or_404(id)
        db.session.delete(usuario)
        db.session.commit()
        return '', 204

class ProyectoEditar(Resource):
    @auth_required
    def put(self, id):
        proyecto = Proyecto.query.get_or_404(id)
        data = request.get_json()
        proyecto.nombre = data.get("nombre", proyecto.nombre)
        proyecto.descripcion = data.get("descripcion", proyecto.descripcion)
        proyecto.vuln_total_max = data.get("vuln_total_max", proyecto.vuln_total_max)
        proyecto.solucionabilidad_min = data.get("solucionabilidad_min", proyecto.solucionabilidad_min)
        proyecto.nivel_maximo = data.get("nivel_maximo", proyecto.nivel_maximo)
        proyecto.formula_combinada = data.get("formula_combinada", proyecto.formula_combinada)
        db.session.commit()
        return {
            "id": proyecto.id,
            "nombre": proyecto.nombre,
            "descripcion": proyecto.descripcion,
            "vuln_total_max": proyecto.vuln_total_max,
            "solucionabilidad_min": proyecto.solucionabilidad_min,
            "nivel_maximo": proyecto.nivel_maximo,
            "formula_combinada": proyecto.formula_combinada
        }
    
    @auth_required    
    def get(self, id):
        proyecto = Proyecto.query.get_or_404(id)
        return {
            'id': proyecto.id,
            'nombre': proyecto.nombre,
            'descripcion': proyecto.descripcion,
            'fecha': proyecto.fecha.strftime("%Y-%m-%d"),
            'usuario_id': proyecto.usuario_id,
            'vuln_total_max': proyecto.vuln_total_max,
            'solucionabilidad_min': proyecto.solucionabilidad_min,
            'nivel_maximo': proyecto.nivel_maximo,
            'formula_combinada': proyecto.formula_combinada
        }, 200

class ProyectoEliminar(Resource):
    @auth_required
    def delete(self, id):
        proyecto = Proyecto.query.get_or_404(id)
        sbom = SBOM.query.filter_by(proyecto_id=id).first()
        if sbom:        
            db.session.delete(sbom)
        Mensaje.query.filter_by(proyecto_id=id).delete()
        db.session.delete(proyecto)
        db.session.commit()
        return '', 204
    
class LoginResource(Resource):
    def post(self):
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")
        try:
            user = guard.authenticate(email, password)
        except Exception as e:
            print(f"Error al autenticar: {e}")
            return {'message': 'Credenciales inválidas'}, 401
        
        access_token = guard.encode_jwt_token(user)
        
        response = make_response(jsonify({"ok": True}), 200)
        response.set_cookie("access_token", access_token, httponly=True, samesite='Lax', secure=True)
        return response
    
class MeResource(Resource):
    @auth_required
    def get(self):
        user = current_user()
        return {"email": user.email, "es_admin": user.es_admin, "nombre": user.nombre, "apellidos": user.apellidos, "id": user.id}, 200

# Usuario
api.add_resource(UsuarioList, '/usuarios')
api.add_resource(UsuarioEditar, '/usuarios/editar/<int:id>')
api.add_resource(UsuarioEliminar, '/usuarios/eliminar/<int:id>')

# Proyecto
api.add_resource(ProyectoList, '/proyectos')
api.add_resource(ProyectoEditar, '/proyectos/editar/<int:id>')
api.add_resource(ProyectoEliminar, '/proyectos/eliminar/<int:id>')

api.add_resource(LoginResource, '/login')
api.add_resource(MeResource, '/me')

if __name__ == '__main__':
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        
        # Añadir las nuevas columnas si no existen
        try:
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE proyecto 
                    ADD COLUMN IF NOT EXISTS vuln_total_max INTEGER,
                    ADD COLUMN IF NOT EXISTS solucionabilidad_min INTEGER,
                    ADD COLUMN IF NOT EXISTS nivel_maximo VARCHAR(20),
                    ADD COLUMN IF NOT EXISTS formula_combinada VARCHAR(200),
                    ADD COLUMN IF NOT EXISTS ruta_ultimo_reporte VARCHAR(512)
                """))
                conn.commit()
        except Exception as e:
            print(f"Error al actualizar la estructura de la base de datos: {e}")
        
        db.session.commit()
    app.run(host='0.0.0.0', port=5000, debug=True)
