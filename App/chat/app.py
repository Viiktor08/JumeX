from flask import Flask, request, jsonify
import requests

from flask_cors import CORS
from flask_restful import Resource, Api

from flask_sqlalchemy import SQLAlchemy

from servicios import AnimalFactsService
from controller import MessageController

from flask_praetorian import Praetorian, auth_required, current_user
from datetime import datetime
import logging
import google.generativeai as genai

genai.configure(api_key="AIzaSyCtalRk2K-VMCkdf4_6JLPRl4guTlQnXOc")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mariadb+mariadbconnector://usuario:password@mariadb:3306/flask_database'
app.config['SECRET_KEY'] = 'clave_super_segura'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
guard = Praetorian()
CORS(app, resources={r"/chat": {"origins": ["http://localhost:5000", "http://127.0.0.1:5000", "http://flask_web:5000", "http://localhost:5010", "http://127.0.0.1:5010", "http://flask_web:5010"]}}, supports_credentials=True)

animal_service = AnimalFactsService()
message_controller = MessageController(animal_service)

class SBOM(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    ruta = db.Column(db.String(512), nullable=False)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyecto.id'), nullable=False)

    proyecto = db.relationship("Proyecto", backref="sboms")
    
class Proyecto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    fecha = db.Column(db.Date, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)


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

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    proyectos = db.relationship('Proyecto', backref='usuario', lazy=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    es_admin = db.Column(db.Boolean, default=False)
    
    def __init__(self, nombre, apellidos, email, password):
        self.nombre = nombre
        self.apellidos = apellidos
        self.email = email
        self.password = guard.hash_password(password)
        self.proyectos = []
    
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
api = Api(app)


class Chat(Resource):
    @auth_required
    def get(self):
        try:
            proyecto_id = request.args.get('proyecto_id', type=int)
            if not proyecto_id:
                return {'error': 'Se requiere proyecto_id'}, 400
                
            mensajes = Mensaje.query.filter_by(proyecto_id=proyecto_id).order_by(Mensaje.fecha).all()
            logger.info(f"Recuperados {len(mensajes)} mensajes para el proyecto {proyecto_id}")
            return jsonify([mensaje.to_dict() for mensaje in mensajes])
        except Exception as e:
            logger.error(f"Error al obtener mensajes: {str(e)}")
            return {'error': str(e)}, 500
        
    @auth_required
    def post(self):
        try:
            data = request.get_json()
            proyecto_id = data.get('proyecto_id')
            mensaje = data.get('message')

            if not proyecto_id or not mensaje:
                return {'error': 'Se requiere proyecto_id y message'}, 400

            logger.info(f"Guardando mensaje para el proyecto {proyecto_id}: {mensaje}")

            mensaje_usuario = Mensaje(
                proyecto_id=proyecto_id,
                contenido=mensaje,
                es_bot=False
            )
            db.session.add(mensaje_usuario)

            # Preparar contexto
            proyecto = Proyecto.query.get(proyecto_id)
            sbom = SBOM.query.filter_by(proyecto_id=proyecto_id).first()
            contexto = f"Proyecto: {proyecto.nombre}\nDescripción: {proyecto.descripcion or 'Sin descripción'}\n"
            if sbom:
                try:
                    with open(sbom.ruta, 'r', encoding='utf-8') as f:
                        contenido_sbom = f.read()[:15000]  # Límite de seguridad de Gemini
                        contexto += f"\nContenido SBOM:\n{contenido_sbom}"
                except Exception as e:
                    contexto += "\n[Error al leer SBOM]"

            # Prompt para Gemini
            prompt = f"""
Eres un asistente inteligente y versátil.

Por defecto, actúas como un experto en **seguridad de componentes IoT**, ayudando a interpretar vulnerabilidades, evaluar riesgos en SBOMs y aconsejar buenas prácticas de protección.

Sin embargo, si el usuario te pregunta sobre cualquier otro tema, también debes responder de manera útil, clara y precisa, sin rechazar la conversación.

---

📦 **Contexto del proyecto**:
{contexto}

🧑‍💻 **Usuario**:
{mensaje}

🤖 **Asistente**:
"""

            # Llamada a Gemini
            model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")
            response = model.generate_content(prompt)
            respuesta = response.text.strip()

            mensaje_bot = Mensaje(
                proyecto_id=proyecto_id,
                contenido=respuesta,
                es_bot=True
            )
            db.session.add(mensaje_bot)
            db.session.commit()

            logger.info(f"Mensajes guardados correctamente. IDs: {mensaje_usuario.id}, {mensaje_bot.id}")

            return jsonify({
                'response': respuesta,
                'mensaje_id': mensaje_usuario.id,
                'respuesta_id': mensaje_bot.id
            })

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al llamar a Gemini: {str(e)}")
            return {'error': str(e)}, 500


api.add_resource(Chat, '/chat')

if __name__ == "__main__":
    with app.app_context():
        logger.info("Creando tablas de la base de datos...")
        db.create_all()
        logger.info("Tablas creadas correctamente")
    app.run(host='0.0.0.0', port=5000, debug=True)