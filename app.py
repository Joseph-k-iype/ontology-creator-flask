from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, send_file
from flask_migrate import Migrate
from extensions import db, login_manager, socketio
from models import User, Ontology, Class, OntologyProperty, Namespace
from flask_login import login_user, login_required, logout_user, current_user
from ontology.ontology_service import OntologyService
import logging
import io

app = Flask(__name__)
app.config.from_object('config.Config')

db.init_app(app)
login_manager.init_app(app)
socketio.init_app(app)
migrate = Migrate(app, db)

# Setup logging
logging.basicConfig(level=logging.DEBUG)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    ontologies = Ontology.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', ontologies=ontologies)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.')
            return redirect(url_for('signup'))

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/create', methods=['POST'])
@login_required
def create_ontology():
    name = request.form['name']
    ontology = Ontology(name=name, user_id=current_user.id)
    db.session.add(ontology)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/ontology/<int:id>')
@login_required
def view_ontology(id):
    ontology = Ontology.query.get_or_404(id)
    if ontology.user_id != current_user.id:
        return redirect(url_for('index'))

    classes = Class.query.filter_by(ontology_id=id).all()
    properties = OntologyProperty.query.filter_by(ontology_id=id).all()
    namespaces = Namespace.query.filter_by(ontology_id=id).all()
    return render_template('ontology.html', ontology=ontology, classes=classes, properties=properties, namespaces=namespaces)

@app.route('/add_class', methods=['POST'])
@login_required
def add_class():
    logging.debug('Received request: %s', request.get_json())
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input'}), 400

    class_name = data.get('class_name')
    ontology_id = data.get('ontology_id')
    parent_id = data.get('parent_id')
    custom_namespace = data.get('custom_namespace')

    if not class_name or not ontology_id:
        return jsonify({'error': 'Missing class_name or ontology_id'}), 400

    ontology_service = OntologyService(ontology_id)
    new_class = ontology_service.add_class(class_name, parent_id, custom_namespace)

    logging.debug('Created class: %s', new_class)
    
    socketio.emit('class_added', new_class)
    return jsonify({'success': True, 'class': new_class})

@app.route('/add_subclass', methods=['POST'])
@login_required
def add_subclass():
    data = request.json
    ontology_id = data['ontology_id']
    class_name = data['class_name']
    parent_class_id = data['parent_class_id']

    ontology_service = OntologyService(ontology_id)
    new_subclass = ontology_service.add_subclass(class_name, parent_class_id)

    socketio.emit('subclass_added', {'subclass': new_subclass})
    return jsonify({'success': True, 'subclass': new_subclass})

@app.route('/add_equivalent_class', methods=['POST'])
@login_required
def add_equivalent_class():
    data = request.json
    ontology_id = data['ontology_id']
    class_id = data['class_id']
    equivalent_class_id = data['equivalent_class_id']

    ontology_service = OntologyService(ontology_id)
    equivalent_class = ontology_service.add_equivalent_class(class_id, equivalent_class_id)

    socketio.emit('equivalent_class_added', {'equivalent_class': equivalent_class})
    return jsonify({'success': True, 'equivalent_class': equivalent_class})

@app.route('/add_disjoint_class', methods=['POST'])
@login_required
def add_disjoint_class():
    data = request.json
    ontology_id = data['ontology_id']
    class_id = data['class_id']
    disjoint_class_id = data['disjoint_class_id']

    ontology_service = OntologyService(ontology_id)
    disjoint_class = ontology_service.add_disjoint_class(class_id, disjoint_class_id)

    socketio.emit('disjoint_class_added', {'disjoint_class': disjoint_class})
    return jsonify({'success': True, 'disjoint_class': disjoint_class})

@app.route('/add_property', methods=['POST'])
@login_required
def add_property():
    data = request.json
    ontology_id = data['ontology_id']
    property_name = data['property_name']
    domain_class_id = data['domain_class_id']
    range_class_id = data['range_class_id']
    parent_id = data.get('parent_id')
    custom_namespace = data.get('custom_namespace')
    data_type = data.get('data_type')

    ontology_service = OntologyService(ontology_id)
    new_property = ontology_service.add_property(property_name, domain_class_id, range_class_id, parent_id, custom_namespace, data_type)

    socketio.emit('property_added', {'property': new_property})
    return jsonify({'success': True, 'property': new_property})

@app.route('/add_namespace', methods=['POST'])
@login_required
def add_namespace():
    data = request.get_json()
    ontology_id = data.get('ontology_id')
    namespace_name = data.get('namespace_name')
    namespace_uri = data.get('namespace_uri')

    if not namespace_name or not namespace_uri:
        return jsonify({'error': 'Missing namespace_name or namespace_uri'}), 400

    new_namespace = Namespace(name=namespace_name, uri=namespace_uri, ontology_id=ontology_id)
    db.session.add(new_namespace)
    db.session.commit()

    socketio.emit('namespace_added', {'namespace': {'id': new_namespace.id, 'name': new_namespace.name, 'uri': new_namespace.uri}})
    return jsonify({'success': True, 'namespace': {'id': new_namespace.id, 'name': new_namespace.name, 'uri': new_namespace.uri}})

@app.route('/export/<int:id>/<format>', methods=['GET'])
@login_required
def export_ontology(id, format):
    ontology = Ontology.query.get_or_404(id)
    if ontology.user_id != current_user.id:
        return redirect(url_for('index'))

    ontology_service = OntologyService(ontology.id)
    serialized_ontology = ontology_service.serialize_ontology(format=format)

    if format == 'ttl':
        return send_file(
            io.BytesIO(serialized_ontology.encode('utf-8')),
            mimetype='text/turtle',
            as_attachment=True,
            download_name=f'ontology_{id}.ttl'
        )
    else:
        return serialized_ontology

@app.route('/ontology/<int:id>/graph')
@login_required
def get_ontology_graph(id):
    ontology = Ontology.query.get_or_404(id)
    if ontology.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    ontology_service = OntologyService(ontology.id)
    elements = ontology_service.get_cytoscape_elements()
    return jsonify(elements)

if __name__ == '__main__':
    socketio.run(app, debug=True)
