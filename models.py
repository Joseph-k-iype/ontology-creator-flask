from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint, ForeignKeyConstraint

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Ontology(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    classes = db.relationship('Class', backref='ontology', lazy=True)
    properties = db.relationship('OntologyProperty', backref='ontology', lazy=True)
    namespaces = db.relationship('Namespace', backref='ontology', lazy=True)

    def __repr__(self):
        return f'<Ontology {self.name}>'

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ontology_id = db.Column(db.Integer, db.ForeignKey('ontology.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=True)
    subclasses = db.relationship('Class', backref=db.backref('parent', remote_side=[id]), lazy=True)
    
    equivalent_classes = db.relationship(
        'EquivalentClass',
        foreign_keys='EquivalentClass.class_id',
        backref='class',
        lazy=True
    )
    
    disjoint_classes = db.relationship(
        'DisjointClass',
        foreign_keys='DisjointClass.class_id',
        backref='class',
        lazy=True
    )

    __table_args__ = (
        UniqueConstraint('name', 'ontology_id', name='uq_class_name_ontology_id'),
    )

    def __repr__(self):
        return f'<Class {self.name}>'

class OntologyProperty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ontology_id = db.Column(db.Integer, db.ForeignKey('ontology.id'), nullable=False)
    domain_class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    range_class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('ontology_property.id'), nullable=True)
    subproperties = db.relationship('OntologyProperty', backref=db.backref('parent', remote_side=[id]), lazy=True)

    __table_args__ = (
        UniqueConstraint('name', 'ontology_id', name='uq_property_name_ontology_id'),
    )

    def __init__(self, name, ontology_id, domain_class_id, range_class_id, parent_id=None):
        self.name = name
        self.ontology_id = ontology_id
        self.domain_class_id = domain_class_id
        self.range_class_id = range_class_id
        self.parent_id = parent_id

    def __repr__(self):
        return f'<OntologyProperty {self.name}>'

class Namespace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    uri = db.Column(db.String(255), nullable=False)
    ontology_id = db.Column(db.Integer, db.ForeignKey('ontology.id'), nullable=False)

    __table_args__ = (
        UniqueConstraint('name', 'ontology_id', name='uq_namespace_name_ontology_id'),
    )

    def __repr__(self):
        return f'<Namespace {self.name}>'

class EquivalentClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    equivalent_class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)

    __table_args__ = (
        UniqueConstraint('class_id', 'equivalent_class_id', name='uq_equivalent_class'),
    )

class DisjointClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    disjoint_class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)

    __table_args__ = (
        UniqueConstraint('class_id', 'disjoint_class_id', name='uq_disjoint_class'),
    )
