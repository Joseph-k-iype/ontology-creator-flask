from models import Class, OntologyProperty, EquivalentClass, DisjointClass, Namespace, db
from rdflib import Graph as RDFGraph, URIRef, RDF, OWL, RDFS
from urllib.parse import quote

class OntologyService:
    def __init__(self, ontology_id, filename=None):
        self.graph = RDFGraph()
        self.ontology_id = ontology_id
        self.base_uri = f"http://example.org/ontology/{ontology_id}"

        # Load existing TTL file if provided
        if filename:
            self.graph.parse(filename, format='turtle')

        # Load existing data from the database
        self.load_existing_data()

    def load_existing_data(self):
        """Load existing classes, properties, etc., into the RDF graph."""
        classes = Class.query.filter_by(ontology_id=self.ontology_id).all()
        for cls in classes:
            class_uri = URIRef(f"{self.base_uri}#{quote(cls.name)}")
            self.graph.add((class_uri, RDF.type, OWL.Class))
            if cls.parent_id:
                parent_class = Class.query.get(cls.parent_id)
                parent_class_uri = URIRef(f"{self.base_uri}#{quote(parent_class.name)}")
                self.graph.add((class_uri, RDFS.subClassOf, parent_class_uri))

        properties = OntologyProperty.query.filter_by(ontology_id=self.ontology_id).all()
        for prop in properties:
            property_uri = URIRef(f"{self.base_uri}#{quote(prop.name)}")
            domain_class = Class.query.get(prop.domain_class_id)
            range_class = Class.query.get(prop.range_class_id)
            domain_uri = URIRef(f"{self.base_uri}#{quote(domain_class.name)}")
            range_uri = URIRef(f"{self.base_uri}#{quote(range_class.name)}")

            self.graph.add((property_uri, RDF.type, OWL.ObjectProperty))
            self.graph.add((property_uri, RDFS.domain, domain_uri))
            self.graph.add((property_uri, RDFS.range, range_uri))

    def add_class(self, class_name, parent_id=None, custom_namespace=None):
        new_class = Class(name=class_name, ontology_id=self.ontology_id, parent_id=parent_id)
        db.session.add(new_class)
        db.session.commit()

        class_uri = URIRef(f"{self.base_uri}#{quote(class_name)}")
        self.graph.add((class_uri, RDF.type, OWL.Class))

        if parent_id:
            parent_class = Class.query.get(parent_id)
            parent_class_uri = URIRef(f"{self.base_uri}#{quote(parent_class.name)}")
            self.graph.add((class_uri, RDFS.subClassOf, parent_class_uri))

        return {'id': new_class.id, 'name': new_class.name}

    def add_subclass(self, class_name, parent_class_id):
        return self.add_class(class_name, parent_class_id)

    def add_equivalent_class(self, class_id, equivalent_class_id):
        eq_class = EquivalentClass(class_id=class_id, equivalent_class_id=equivalent_class_id)
        db.session.add(eq_class)
        db.session.commit()

        class_obj = Class.query.get(class_id)
        eq_class_obj = Class.query.get(equivalent_class_id)
        class_uri = URIRef(f"{self.base_uri}#{quote(class_obj.name)}")
        eq_class_uri = URIRef(f"{self.base_uri}#{quote(eq_class_obj.name)}")
        self.graph.add((class_uri, OWL.equivalentClass, eq_class_uri))

        return {'id': eq_class.id, 'class_id': class_id, 'equivalent_class_id': equivalent_class_id}

    def add_disjoint_class(self, class_id, disjoint_class_id):
        disj_class = DisjointClass(class_id=class_id, disjoint_class_id=disjoint_class_id)
        db.session.add(disj_class)
        db.session.commit()

        class_obj = Class.query.get(class_id)
        disj_class_obj = Class.query.get(disjoint_class_id)
        class_uri = URIRef(f"{self.base_uri}#{quote(class_obj.name)}")
        disj_class_uri = URIRef(f"{self.base_uri}#{quote(disj_class_obj.name)}")
        self.graph.add((class_uri, OWL.disjointWith, disj_class_uri))

        return {'id': disj_class.id, 'class_id': class_id, 'disjoint_class_id': disjoint_class_id}

    def add_property(self, property_name, domain_class_id, range_class_id, parent_id=None, custom_namespace=None, data_type=None):
        new_property = OntologyProperty(
            name=property_name, ontology_id=self.ontology_id, 
            domain_class_id=domain_class_id, range_class_id=range_class_id, 
            parent_id=parent_id
        )
        db.session.add(new_property)
        db.session.commit()

        property_uri = URIRef(f"{self.base_uri}#{quote(property_name)}")
        domain_class = Class.query.get(domain_class_id)
        range_class = Class.query.get(range_class_id)
        domain_uri = URIRef(f"{self.base_uri}#{quote(domain_class.name)}")
        range_uri = URIRef(f"{self.base_uri}#{quote(range_class.name)}")

        self.graph.add((property_uri, RDF.type, OWL.ObjectProperty))
        self.graph.add((property_uri, RDFS.domain, domain_uri))
        self.graph.add((property_uri, RDFS.range, range_uri))

        return {'id': new_property.id, 'name': new_property.name}

    def add_namespace(self, namespace_name, namespace_uri):
        new_namespace = Namespace(name=namespace_name, uri=namespace_uri, ontology_id=self.ontology_id)
        db.session.add(new_namespace)
        db.session.commit()

        self.graph.bind(namespace_name, URIRef(namespace_uri))

        return {'id': new_namespace.id, 'name': new_namespace.name, 'uri': new_namespace.uri}

    def serialize_ontology(self, format="ttl"):
        return self.graph.serialize(format=format)

    def get_cytoscape_elements(self):
        elements = []

        classes = Class.query.filter_by(ontology_id=self.ontology_id).all()
        for cls in classes:
            elements.append({'data': {'id': cls.id, 'label': cls.name}})
            if cls.parent_id:
                elements.append({'data': {'source': cls.parent_id, 'target': cls.id}})

        properties = OntologyProperty.query.filter_by(ontology_id=self.ontology_id).all()
        for prop in properties:
            elements.append({'data': {'id': prop.id, 'label': prop.name}})
            elements.append({'data': {'source': prop.domain_class_id, 'target': prop.range_class_id, 'label': prop.name}})

        return elements
