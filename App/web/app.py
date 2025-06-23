from flask import Flask, render_template, request, redirect, url_for, flash, make_response, jsonify, json, send_file
import requests
from datetime import date, datetime
from flask_praetorian import Praetorian
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from nvdlib import searchCVE

from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mariadb+mariadbconnector://usuario:password@mariadb:3306/flask_database"
app.config['SECRET_KEY'] = 'clave_super_segura'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
app.config['SECRET_KEY'] = 'clave_super_segura'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

API_URL = "http://flask_api:5000"

guard = Praetorian()
token = None
CORS(app,  resources={r"/*": {"origins": "*"}}, supports_credentials=True) 

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
        
@app.route('/')
def index():
    token = request.cookies.get('access_token')
    usuario = None
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_URL}/me", headers=headers)
        if response.status_code == 200:
            usuario = response.json()
    return render_template('index.html', usuario=usuario)

@app.route('/chat', methods=['POST', 'GET'])
def chat():
    usuarios = []
    proyectos = []
    proyecto_activo_id = None  # <--- define aquí

    token = request.cookies.get('access_token')
    if not token:
        flash('Debes iniciar sesión para acceder al chat', 'warning')
        return redirect(url_for('login'))

    headers = {'Authorization': f'Bearer {token}'}
    try:
        response = requests.get(f'{API_URL}/proyectos', headers=headers)
        usuario = requests.get(f"{API_URL}/me", headers=headers).json()
        if response.status_code == 200:
            proyectos = response.json()
        elif response.status_code == 401:
            flash('Sesión expirada, por favor vuelve a iniciar sesión', 'warning')
            return redirect(url_for('login'))
    except requests.exceptions.RequestException:
        proyectos = []

    return render_template('chat.html', proyectos=proyectos, usuario=usuario)

# -------------------- AUTENTICACIÓN --------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            response = requests.post(f'{API_URL}/login', json={'email': email, 'password': password})
            if response.status_code == 200:
                token = response.cookies.get('access_token')
                response = make_response(redirect(url_for('index')))
                response.set_cookie('access_token', token, httponly=True, samesite='Lax')
                flash('Inicio de sesión exitoso', 'success')
                return response
            else:
                flash('Credenciales incorrectas', 'warning')
        except requests.exceptions.RequestException:
            flash('Error de conexión con el servidor', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    token = request.cookies.get('access_token')
    if not token:
        flash('No hay sesión iniciada', 'warning')
        return redirect(url_for('login'))
    response = make_response(redirect(url_for('login')))
    response.set_cookie('access_token', '', expires=0)
    flash('Sesión cerrada correctamente', 'success')
    return response

# -------------------- USUARIOS --------------------

@app.route('/usuarios')
def usuarios():
    usuarios = []
    try:
        token = request.cookies.get('access_token')
        if token:
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(f'{API_URL}/usuarios', headers=headers)
            usuario = requests.get(f"{API_URL}/me", headers=headers).json()
            if response.status_code == 200:
                usuarios = response.json()
            elif response.status_code == 401:
                flash('Sesión expirada, por favor vuelve a iniciar sesión', 'warning')
                return redirect(url_for('login'))
            else:
                flash('No tienes permisos para acceder', 'warning')
                return redirect(url_for('index'))
        else:
            flash('Debes iniciar sesión para crear un usuario', 'warning')
    except requests.exceptions.RequestException:
        flash('Error al obtener usuarios', 'danger')
    return render_template('usuarios.html', usuarios=usuarios, usuario=usuario)

@app.route('/usuarios/nuevo', methods=['GET', 'POST'])
def nuevo_usuario():
    token = request.cookies.get('access_token')
    if not token:
        flash('Debes iniciar sesión para crear un usuario', 'warning')
        return redirect(url_for('login'))

    headers = {'Authorization': f'Bearer {token}'}
    usuario = requests.get(f"{API_URL}/me", headers=headers).json()
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellidos = request.form['apellidos']
        email = request.form['email']
        password = request.form['password']
        try:
            response = requests.post(f'{API_URL}/usuarios', json={
                'nombre': nombre,
                'apellidos': apellidos,
                'email': email,
                'password': password
            }, headers=headers)
            
            if response.status_code == 201:
                flash('Usuario creado con éxito', 'success')
            else:
                flash('Error al crear usuario', 'warning')
        except requests.exceptions.RequestException:
            flash('Fallo al conectar con la API', 'danger')
        return redirect(url_for('usuarios'))

    try:
        response = requests.get(f'{API_URL}/usuarios', headers=headers)
        if response.status_code == 200:
            usuarios = response.json()
        else:
            usuarios = []
            flash('No tienes permisos para acceder', 'warning')
            return redirect(url_for('index'))
    except requests.exceptions.RequestException:
        usuarios = []
        flash('Error al conectar con la API', 'danger')
    return render_template('nuevo_usuario.html', usuarios=usuarios, usuario=usuario)

@app.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    token = request.cookies.get('access_token')
    if not token:
        flash('Debes iniciar sesión para crear un usuario', 'warning')
        return redirect(url_for('login'))

    headers = {'Authorization': f'Bearer {token}'}
    if request.method == 'POST':
        nuevo_nombre = request.form['nombre']
        nuevo_apellidos = request.form['apellidos']
        nuevo_email = request.form['email']
        try:
            response = requests.put(f'{API_URL}/usuarios/editar/{id}', json={
                'nombre': nuevo_nombre,
                'apellidos': nuevo_apellidos,
                'email': nuevo_email
            }, headers=headers)
            if response.status_code == 200:
                flash('Usuario actualizado', 'success')
            else:
                flash('Error al actualizar el usuario', 'warning')
        except requests.exceptions.RequestException:
            flash('Fallo al conectar con la API', 'danger')
        return redirect(url_for('usuarios'))
    try:
        response_usuario = requests.get(f'{API_URL}/usuarios/editar/{id}', headers=headers)
        response_usuarios = requests.get(f'{API_URL}/usuarios', headers=headers)
        if response_usuario.status_code == 200 and response_usuarios.status_code == 200:
            usuario = response_usuario.json()
            usuarios = response_usuarios.json()
        else:
            usuario = {}
            usuarios = []
            flash('Error al obtener el usuario o los usuarios', 'warning')
    except requests.exceptions.RequestException:
        usuario = {}
        usuarios = []
        flash('Error al conectar con la API', 'danger')
    return render_template('editar_usuario.html', usuario=usuario, usuarios=usuarios, usuario_activo_id=id)

@app.route('/usuarios/eliminar/<int:id>', methods=['GET'])
def eliminar_usuario(id):
    token = request.cookies.get('access_token')
    if not token:
        flash('Debes iniciar sesión para crear un usuario', 'warning')
        return redirect(url_for('login'))

    headers = {'Authorization': f'Bearer {token}'}
    try:
        response = requests.delete(f'{API_URL}/usuarios/eliminar/{id}', headers=headers)
        if response.status_code == 204:
            flash('Usuario eliminado correctamente', 'success')
        else:
            flash('Error al eliminar usuario', 'danger')
    except requests.exceptions.RequestException:
        flash('No se pudo conectar al microservicio', 'danger')
    return redirect(url_for('usuarios'))

# -------------------- PROYECTOS --------------------

@app.route("/proyectos")
def listar_proyectos():
    proyectos = []
    try:
        token = request.cookies.get('access_token')
        if token:
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(f'{API_URL}/proyectos', headers = headers)
            usuario = requests.get(f"{API_URL}/me", headers=headers).json()
            if response.status_code == 200:
                proyectos = response.json()
            elif response.status_code == 401:
                flash('Sesión expirada, por favor vuelve a iniciar sesión', 'warning')
                return redirect(url_for('login'))
            else:
                flash('Error al obtener proyectos', 'warning')
        else:
            flash('No se ha proporcionado un token de acceso', 'warning')
    except requests.exceptions.RequestException:
        flash('Error al obtener proyectos', 'danger')
    return render_template("proyectos.html", proyectos=proyectos, usuario=usuario)

@app.route('/proyectos/nuevo', methods=['GET', 'POST'])
def nuevo_proyecto():
    token = request.cookies.get('access_token')
    if not token:
        flash('Debes iniciar sesión para crear un proyecto', 'warning')
        return redirect(url_for('login'))

    headers = {'Authorization': f'Bearer {token}'}
    
    usuarios = []
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        fecha = date.today().strftime("%d-%m-%Y")
        try:
            response = requests.post(f'{API_URL}/proyectos', json={
                'nombre': nombre,
                'descripcion': descripcion,
                'fecha': fecha,
                'vuln_total_max': int(request.form['vuln_total_max']),
                'solucionabilidad_min': int(request.form['solucionabilidad_min']),
                'nivel_maximo': request.form['nivel_maximo'],
                'formula_combinada': request.form['formula_combinada']
            }, headers=headers)
            
            if response.status_code == 201:
                flash('Proyecto creado con éxito', 'success')
                return redirect(url_for('chat'))
            else:
                flash('Error al crear el proyecto', 'warning')
        except requests.exceptions.RequestException:
            flash('Error al conectar con la API', 'danger')
        return redirect(url_for('chat'))
    try:
        usuario = requests.get(f"{API_URL}/me", headers=headers).json()
        if usuario['es_admin']:
            response_usuarios = requests.get(f'{API_URL}/usuarios', headers=headers)
            if response_usuarios.status_code == 200:
                usuarios = response_usuarios.json()
            else:
                usuarios = []
        response_proyectos = requests.get(f'{API_URL}/proyectos', headers=headers)
        if response_proyectos.status_code == 200:
            proyectos = response_proyectos.json()
        else:
            proyectos = []
            flash('Error al obtener usuarios o proyectos', 'warning')
            return redirect(url_for('index'))
    except requests.exceptions.RequestException:
        usuarios = []
        proyectos = []
        flash('Error al conectar con la API', 'danger')
    return render_template('nuevo_proyecto.html', usuarios=usuarios, proyectos=proyectos, usuario=usuario, proyecto_activo_id=id)

@app.route('/proyectos/editar/<int:id>', methods=['GET', 'POST'])
def editar_proyecto(id):
    token = request.cookies.get('access_token')
    if not token:
        flash('Debes iniciar sesión para crear un usuario', 'warning')
        return redirect(url_for('login'))

    headers = {'Authorization': f'Bearer {token}'}
    if request.method == 'POST':
        try:
            response = requests.put(f'{API_URL}/proyectos/editar/{id}', json={
                'nombre': request.form['nombre'],
                'descripcion': request.form['descripcion'],
                'vuln_total_max': int(request.form['vuln_total_max']),
                'solucionabilidad_min': int(request.form['solucionabilidad_min']),
                'nivel_maximo': request.form['nivel_maximo'],
                'formula_combinada': request.form['formula_combinada']
            }, headers=headers)
            if response.status_code == 200:
                flash('Proyecto actualizado', 'success')
                return redirect(url_for('chat'))
            else:
                flash('No se pudo actualizar el proyecto', 'warning')
        except requests.exceptions.RequestException:
            flash('Error al conectar con la API', 'danger')
        return redirect(url_for('chat'))
    try:
        respuesta_proyecto = requests.get(f'{API_URL}/proyectos/editar/{id}', headers=headers)
        respuesta_proyectos = requests.get(f'{API_URL}/proyectos', headers=headers)
        usuario = requests.get(f"{API_URL}/me", headers=headers).json()
        if respuesta_proyecto.status_code == 200 and respuesta_proyectos.status_code == 200:
            proyecto = respuesta_proyecto.json()
            sbom = SBOM.query.filter_by(proyecto_id=proyecto["id"]).first()
            proyectos = respuesta_proyectos.json()
        else:
            proyecto = {}
            proyectos = []
            flash('Error al obtener el proyecto o los proyectos', 'warning')
    except requests.exceptions.RequestException:
        proyecto = {}
        proyectos = []
        flash('Error al conectar con la API', 'danger')
    return render_template('editar_proyecto.html', proyecto=proyecto , proyectos=proyectos, proyecto_activo_id=id, usuario=usuario, sbom=sbom)

@app.route('/proyectos/eliminar/<int:id>', methods=['GET'])
def eliminar_proyecto(id):
    token = request.cookies.get('access_token')
    if not token:
        flash('Debes iniciar sesión para crear un usuario', 'warning')
        return redirect(url_for('login'))

    headers = {'Authorization': f'Bearer {token}'}
    try:
        res = requests.delete(f'{API_URL}/proyectos/eliminar/{id}', headers=headers)
        if res.status_code == 204:
            flash('Proyecto eliminado correctamente', 'success')
        else:
            flash('No se pudo eliminar el proyecto', 'warning')
    except requests.exceptions.RequestException:
        flash('Error al conectar con la API', 'danger')
    return redirect(url_for('listar_proyectos'))

@app.route("/subir-sbom", methods=["POST", "OPTIONS"])
def subir_sbom():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

    proyecto_id = request.form.get("proyecto_id")
    archivo = request.files.get("sbom")

    if not proyecto_id:
        return jsonify({"error": "Faltan id"}), 400
    if not archivo:
        return jsonify({"error": "Faltan archivo"}), 400

    path = os.path.join(app.config['UPLOAD_FOLDER'], f"{proyecto_id}_{archivo.filename}")
    archivo.save(path)

    nuevo_sbom = SBOM(
        nombre=archivo.filename,
        ruta=path,
        proyecto_id=int(proyecto_id)
    )
    sbom = SBOM.query.filter_by(proyecto_id=proyecto_id).first()
    if sbom is not None:
        db.session.delete(sbom)
        db.session.commit()
    db.session.add(nuevo_sbom)
    db.session.commit()
    
    return jsonify({"message": "SBOM subido correctamente", "nombre": archivo.filename})

from datetime import datetime
from flask import send_from_directory
import os

niveles_cvss = {
    "bajo": 3.9,
    "medio": 6.9,
    "alto": 8.9,
    "critico": 10
}

def cvss_float(valor):
    try:
        return float(valor)
    except (ValueError, TypeError):
        return 0.0

@app.route('/analizar-sbom', methods=['POST'])
def analizar_sbom():
    proyecto_id = request.form.get("proyecto_id")
    sbom = SBOM.query.filter_by(proyecto_id=proyecto_id).first()
    if sbom is None:
        return jsonify({"error": "¡ERROR! Debes subir un SBOM para analizar"}), 400
    sbom_path = sbom.ruta

    with open(sbom_path, 'r') as f:
        sbom_data = json.load(f)

    def obtener_puntuacion_cvss(cve):
        try:
            if hasattr(cve.metrics, "cvssMetricV31"):
                return cve.metrics.cvssMetricV31[0].cvssData.baseScore
            elif hasattr(cve.metrics, "cvssMetricV2"):
                return cve.metrics.cvssMetricV2[0].cvssData.baseScore
        except Exception:
            pass
        return "N/A"

    def evaluar_solucionabilidad(cve):
        try:
            versiones_seguras = []
            referencias_utiles = []

            for node in getattr(cve.configurations, "nodes", []):
                for match in getattr(node, "cpeMatch", []):
                    if getattr(match, "vulnerable", True) is False:
                        versiones_seguras.append(match.criteria)

            for ref in getattr(cve, "references", []):
                if any(keyword in ref.url.lower() for keyword in ["patch", "fix", "commit", "update"]):
                    referencias_utiles.append(ref.url)

            solucionable = len(versiones_seguras) > 0 or len(referencias_utiles) > 0
            detalles = {
                "versiones_seguras": versiones_seguras,
                "referencias_utiles": referencias_utiles
            }
            return solucionable, detalles

        except Exception:
            return False, {}

    cves_encontradas = []
    lineas_txt = []

    for componente in sbom_data.get("components", []):
        cpe = componente.get("cpe")
        if not cpe:
            continue
        try:
            resultados = searchCVE(cpeName=cpe)
            for r in resultados:
                nombre=componente.get("name")
                puntuacion = obtener_puntuacion_cvss(r)
                solucionable, detalles = evaluar_solucionabilidad(r)
                descripcion = next((d.value for d in r.descriptions if d.lang == "en"), "")
                cve_data = {
                    "componente": nombre,
                    "id": r.id,
                    "descripcion": descripcion,
                    "puntuacion": puntuacion,
                    "solucionable": solucionable
                }
                if solucionable:
                    cve_data["detalles_solucion"] = detalles
                cves_encontradas.append(cve_data)

                # Guardar en la BD si tienes un modelo Mensaje
                nuevo_mensaje = Mensaje(
                    contenido=f"Componente: {nombre}. {r.id}: {descripcion} Puntuacion {puntuacion} Solucionable: {solucionable}",
                    proyecto_id=proyecto_id,
                    es_bot=True
                )
                db.session.add(nuevo_mensaje)

                # Agregar línea al archivo
                lineas_txt.append(f"Componente: {nombre}.\nCVE: {r.id}\nDescripción: {descripcion}\nPuntuación: {puntuacion}\n")
                if solucionable:
                    if detalles['versiones_seguras']:
                        lineas_txt.append("Versiones seguras:\n" + "\n".join(detalles['versiones_seguras']) + "\n")
                    if detalles['referencias_utiles']:
                        lineas_txt.append("Referencias útiles:\n" + "\n".join(detalles['referencias_utiles']) + "\n")
                else:
                    lineas_txt.append("Solución: No disponible\n")
                lineas_txt.append("-" * 40 + "\n")

        except Exception as e:
            print(f"Error procesando {cpe}: {e}")

    db.session.commit()  # Guardar todo en BD

    # Calcular si cumple o no
    cumple = True
    motivos = []

    proyecto = Proyecto.query.get(proyecto_id)


    if proyecto.vuln_total_max is not None and len(cves_encontradas) > proyecto.vuln_total_max:
        cumple = False
        motivos.append(f"Exceso de vulnerabilidades encontradas ({len(cves_encontradas)} > {proyecto.vuln_total_max})")

    if proyecto.nivel_maximo and any(cvss_float(cve.get("puntuacion", 0)) > niveles_cvss.get(proyecto.nivel_maximo.lower(), 10) for cve in cves_encontradas):        
        cumple = False
        motivos.append(f"Vulnerabilidades con nivel mayor al permitido ({proyecto.nivel_maximo})")

    if proyecto.solucionabilidad_min is not None:
        solucionables = sum(1 for cve in cves_encontradas if cve.get("solucionable", False))
        porcentaje_sol = (solucionables / len(cves_encontradas) * 100) if cves_encontradas else 100
        if porcentaje_sol < proyecto.solucionabilidad_min:
            cumple = False
            motivos.append(f"Solucionabilidad insuficiente ({porcentaje_sol:.2f}% < {proyecto.solucionabilidad_min}%)")

    # Construir mensaje
    mensaje_cumplimiento = ""
    if cumple:
        mensaje_cumplimiento = "El proyecto CUMPLE con los criterios establecidos.\n\n"
    else:
        mensaje_cumplimiento = "El proyecto NO CUMPLE con los criterios establecidos:\n"
        for m in motivos:
            mensaje_cumplimiento += f"- {m}\n"
        mensaje_cumplimiento += "\n"

    # Insertar al principio del archivo
    lineas_txt.insert(0, mensaje_cumplimiento)
    nuevo_mensaje_criterios = Mensaje(
        contenido=mensaje_cumplimiento,
        proyecto_id=proyecto_id,
        es_bot=True
    )
    db.session.add(nuevo_mensaje_criterios)
    db.session.commit()

    # Crear archivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"reporte_{proyecto.nombre}_{timestamp}.txt".replace(" ", "_")
    ruta_archivo = os.path.join("reportes", nombre_archivo)
    os.makedirs("reportes", exist_ok=True)
    with open(ruta_archivo, "w") as f:
        f.writelines(lineas_txt)
    
    proyecto.ruta_ultimo_reporte = ruta_archivo
    db.session.commit()

    criterios_data = {
        "mensaje": mensaje_cumplimiento,
    }

    return jsonify({
        "mensajes": cves_encontradas,
        "criterios": criterios_data,
        "descarga": f"/descargar-reporte/{nombre_archivo}"
    })

@app.route('/descargar-reporte/<filename>')
def descargar_reporte(filename):
    return send_from_directory("reportes", filename, as_attachment=True)

if __name__ == '__main__':
    with app.app_context():
        if not Usuario.query.filter_by(email="admin@example.es").first():
            admin = Usuario(
                nombre="Admin",
                apellidos="Ejemplo",
                email="admin@example.es",
                password="admin"  # Será hasheada automáticamente
            )
            admin.es_admin = True
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuario admin creado correctamente")
        else:
            print("ℹ️ El usuario admin ya existe")
            
    app.run(host='0.0.0.0', port=5000, debug=True)