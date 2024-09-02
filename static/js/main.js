const socket = io();

// Initialize Cytoscape
const cy = cytoscape({
    container: document.getElementById('cy'),
    style: [
        {
            selector: 'node',
            style: {
                'label': 'data(label)',
                'background-color': '#666',
                'text-valign': 'center',
                'color': '#fff',
                'text-outline-width': 2,
                'text-outline-color': '#666'
            }
        },
        {
            selector: 'edge',
            style: {
                'width': 3,
                'line-color': '#ccc',
                'target-arrow-color': '#ccc',
                'target-arrow-shape': 'triangle'
            }
        }
    ],
    elements: [],
    layout: {
        name: 'cose',
        fit: true,
        padding: 10,
        animate: true
    }
});

// Function to load the ontology graph from the server
function loadOntologyGraph() {
    const ontologyId = document.querySelector('input[name="ontology_id"]').value;
    $.getJSON(`/ontology/${ontologyId}/graph`, function(data) {
        cy.json({ elements: data });
        cy.layout({ name: 'cose' }).run();
    });
}

// Update the graph after adding a new class, property, etc.
function updateOntologyGraph() {
    cy.elements().remove();
    loadOntologyGraph();
}

// Handle adding namespaces
document.getElementById('addNamespaceForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const namespaceUri = document.getElementById('namespaceUri').value;
    const ontologyId = document.querySelector('input[name="ontology_id"]').value;

    const data = {
        namespace_uri: namespaceUri,
        ontology_id: ontologyId
    };

    fetch('/add_namespace', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Namespace Added:', data);
        updateOntologyGraph();
        location.reload();
    })
    .catch(error => console.error('Error:', error));
});

// Handle adding classes
document.getElementById('addClassForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const className = document.getElementById('className').value;
    const parentClass = document.getElementById('parentClass').value;
    const namespaceId = document.getElementById('namespaceSelect').value;
    const ontologyId = document.querySelector('input[name="ontology_id"]').value;

    const data = {
        class_name: className,
        ontology_id: ontologyId,
        parent_id: parentClass || null,
        namespace_id: namespaceId
    };

    fetch('/add_class', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Class Added:', data);
        socket.emit('class_added', data);
        updateOntologyGraph();
    })
    .catch(error => console.error('Error:', error));
});

// Handle adding subclasses
document.getElementById('addSubclassForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const subclassName = document.getElementById('subclassName').value;
    const parentClassId = document.getElementById('parentClassSubclass').value;
    const namespaceId = document.getElementById('namespaceSelectSubclass').value;
    const ontologyId = document.querySelector('input[name="ontology_id"]').value;

    const data = {
        class_name: subclassName,
        ontology_id: ontologyId,
        parent_class_id: parentClassId,
        namespace_id: namespaceId
    };

    fetch('/add_subclass', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Subclass Added:', data);
        socket.emit('subclass_added', data);
        updateOntologyGraph();
    })
    .catch(error => console.error('Error:', error));
});

// Handle adding properties
document.getElementById('addPropertyForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const propertyName = document.getElementById('propertyName').value;
    const domainClass = document.getElementById('domainClass').value;
    const rangeClass = document.getElementById('rangeClass').value;
    const dataType = document.getElementById('dataType').value;
    const namespaceId = document.getElementById('namespaceSelectProperty').value;
    const ontologyId = document.querySelector('input[name="ontology_id"]').value;

    const data = {
        property_name: propertyName,
        ontology_id: ontologyId,
        domain_class_id: domainClass,
        range_class_id: rangeClass,
        data_type: dataType || null,
        namespace_id: namespaceId
    };

    fetch('/add_property', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Property Added:', data);
        socket.emit('property_added', data);
        updateOntologyGraph();
    })
    .catch(error => console.error('Error:', error));
});

// Handle adding equivalent classes
document.getElementById('addEquivalentClassForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const classId = document.getElementById('classIdEq').value;
    const equivalentClassId = document.getElementById('equivalentClassId').value;
    const ontologyId = document.querySelector('input[name="ontology_id"]').value;

    const data = {
        class_id: classId,
        equivalent_class_id: equivalentClassId,
        ontology_id: ontologyId
    };

    fetch('/add_equivalent_class', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Equivalent Class Added:', data);
        socket.emit('equivalent_class_added', data);
        updateOntologyGraph();
    })
    .catch(error => console.error('Error:', error));
});

// Handle adding disjoint classes
document.getElementById('addDisjointClassForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const classId = document.getElementById('classIdDisj').value;
    const disjointClassId = document.getElementById('disjointClassId').value;
    const ontologyId = document.querySelector('input[name="ontology_id"]').value;

    const data = {
        class_id: classId,
        disjoint_class_id: disjointClassId,
        ontology_id: ontologyId
    };

    fetch('/add_disjoint_class', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Disjoint Class Added:', data);
        socket.emit('disjoint_class_added', data);
        updateOntologyGraph();
    })
    .catch(error => console.error('Error:', error));
});

// Real-time updates via Socket.IO
socket.on('class_added', function(data) {
    cy.add({
        data: { id: data.class.id, label: data.class.name }
    });
    cy.layout({ name: 'cose' }).run();
});

socket.on('subclass_added', function(data) {
    cy.add([
        { data: { id: data.subclass.id, label: data.subclass.name }},
        { data: { source: data.subclass.parent_class_id, target: data.subclass.id }}
    ]);
    cy.layout({ name: 'cose' }).run();
});

socket.on('property_added', function(data) {
    cy.add([
        { data: { id: data.property.id, label: data.property.name }},
        { data: { source: data.property.domain_class_id, target: data.property.range_class_id, label: data.property.name }}
    ]);
    cy.layout({ name: 'cose' }).run();
});

socket.on('equivalent_class_added', function(data) {
    cy.add([
        { data: { source: data.equivalent_class.class_id, target: data.equivalent_class.equivalent_class_id }}
    ]);
    cy.layout({ name: 'cose' }).run();
});

socket.on('disjoint_class_added', function(data) {
    cy.add([
        { data: { source: data.disjoint_class.class_id, target: data.disjoint_class.disjoint_class_id }}
    ]);
    cy.layout({ name: 'cose' }).run();
});

// Initial load of the ontology graph
loadOntologyGraph();
