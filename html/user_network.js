let cy;

const RANK_RANGE_SIZE = 100;

//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\
//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\

/**
* Map rank to RGB color according to gradient scheme.
*/
function rankToColor(rank, numUsers) {
    numColorGroups = Math.floor((numUsers + RANK_RANGE_SIZE - 1) / RANK_RANGE_SIZE);
    colorStep = Math.max(1, Math.floor(100 / numColorGroups));
    colorGroup = Math.floor((rank - 1) / RANK_RANGE_SIZE);
    colorIdx = (colorGroup * colorStep) % 100;

    let r, g, b;
    if (colorIdx < 25) {
        r = 180;
        g = 60 + (colorIdx * 3.6);
        b = 60;
    } else if (colorIdx < 50) {
        r = 180 - (colorIdx - 25) * 4.8;
        g = 150 + (colorIdx - 25) * 1.2;
        b = 60;
    } else if (colorIdx < 75) {
        r = 60;
        g = 180;
        b = 60 + (colorIdx - 50) * 4.8;
    } else {
        r = 60;
        g = 180 - (colorIdx - 75) * 4.8;
        b = 180;
    }

    return `rgb(${r},${g},${b})`;
}

/**
* Generate legend, rows contain color patch and associated rank range.
*/
function createLegend(maxRank) {
    const legendDiv = document.getElementById('legend');
    const numRanges = Math.ceil(maxRank / RANK_RANGE_SIZE);

    legendDiv.innerHTML = '<div style="margin-bottom: 10px; font-weight: bold;">Ranks</div>';

    for (let i = 0; i < numRanges; i++) {
        const startRank = i * RANK_RANGE_SIZE + 1;
        const endRank = Math.min((i + 1) * RANK_RANGE_SIZE, maxRank);

        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';

        const colorPatch = document.createElement('div');
        colorPatch.className = 'color-patch';
        colorPatch.style.backgroundColor = rankToColor(startRank, maxRank);

        const label = document.createElement('span');
        label.textContent = `#${startRank} - #${endRank}`;

        legendItem.appendChild(colorPatch);
        legendItem.appendChild(label);
        legendDiv.appendChild(legendItem);
    }
}

/**
* Open info panel for given node.
*/
function openInfoPanel(nodeData) {
    const node = cy.$(`node[id = "${nodeData.id}"]`);
    const incomingNodes = node.incomers().nodes().map(n => `- <a href="https://osu.ppy.sh/users/${n.data('label')}" target="_blank" style="color: #00aaff; text-decoration: none;">${n.data('label')}</a> (#${n.data('rank')})`).join('<br>');
    const outgoingNodes = node.outgoers().nodes().map(n => `- <a href="https://osu.ppy.sh/users/${n.data('label')}" target="_blank" style="color: #00aaff; text-decoration: none;">${n.data('label')}</a> (#${n.data('rank')})`).join('<br>');

    document.getElementById('infoTitle').innerHTML = `
        <a href="https://osu.ppy.sh/users/${nodeData.label}" target="_blank" style="color: #00aaff; text-decoration: none;">${nodeData.label}</a> (#${nodeData.rank})
        <hr></hr>
    `.trim();

    document.getElementById('infoContent').innerHTML = `
        <strong>Mentions:</strong><br>
        ${outgoingNodes || 'None'}<br>
        <br>
        <strong>Mentioned by:</strong><br>
        ${incomingNodes || 'None'}
    `.trim();

    document.getElementById('infoPanel').classList.add('visible');
}

/**
* Close info panel.
*/
function closeInfoPanel() {
    document.getElementById('infoPanel').classList.remove('visible');
    cy.elements().removeClass('highlighted dimmed');
}

/**
* Highlight given node and open info panel.
*/
function selectNode(nodeId) {
    const node = cy.$(`node[id = "${nodeId}"]`);
    if (node.length) {
        // Highlight the node and its connections
        cy.elements().addClass('dimmed');
        node.removeClass('dimmed');
        const connectedEdges = node.connectedEdges();
        const connectedNodes = connectedEdges.connectedNodes();
        connectedEdges.removeClass('dimmed').addClass('highlighted');
        connectedNodes.removeClass('dimmed');

        // Open info panel
        openInfoPanel(node.data());
    }
}

/**
* Setup search bar and query results.
*/
function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');

    // Search results
    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        if (searchTerm.length < 1) {
            searchResults.style.display = 'none';
            return;
        }

        const matchingNodes = cy.nodes().filter(node => 
            node.data('label').toLowerCase().includes(searchTerm)
        );

        if (matchingNodes.length > 0) {
            searchResults.innerHTML = '';
            searchResults.style.display = 'block';

            matchingNodes.forEach(node => {
                const resultDiv = document.createElement('div');
                resultDiv.className = 'search-result';
                resultDiv.textContent = `${node.data('label')} (#${node.data('rank')})`;
                resultDiv.onclick = () => {
                    selectNode(node.id());
                    searchResults.style.display = 'none';
                    searchInput.value = '';
                };
                searchResults.appendChild(resultDiv);
            });
        } else {
            searchResults.style.display = 'none';
        }
    });

    // Close search results when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchResults.contains(e.target) && e.target !== searchInput) {
            searchResults.style.display = 'none';
        }
    });
}

/**
* Load graph data and put into page.
*/
async function loadAndDisplayGraph() {
    try {
        // Unpack graph data
        const response = await fetch('graph_data.json', {cache: 'no-store'});
        const graphData = await response.json();

        // Create legend
        const maxRank = Math.max(...graphData.nodes.map(node => node.data.rank));
        createLegend(maxRank);

        // Generate graph
        cy = cytoscape({
            container: document.getElementById('cy'),
            elements: graphData,
            userZoomingEnabled: true,
            userPanningEnabled: true,
            boxSelectionEnabled: false,
            autounselectify: true,
            autoungrabify: true,
            style: [
                {
                    selector: 'node',
                    style: {
                        'label': 'data(label)',
                        'background-color': (ele) => rankToColor(ele.data('rank'), maxRank),
                        'width': (ele) => {
                            const inDegree = ele.indegree();
                            return 20 + (inDegree * 20);
                        },
                        'height': (ele) => {
                            const inDegree = ele.indegree();
                            return 20 + (inDegree * 20);
                        },
                        'shape': 'ellipse',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'color': '#ffffff',
                        'text-outline-color': '#000000',
                        'text-outline-width': 2,
                        'font-size': (ele) => {
                            const inDegree = ele.indegree();
                            return Math.max(12, 12 + (inDegree * 2)) + 'px';
                        },
                        'border-width': 2,
                        'border-color': '#000000',
                        'border-opacity': 1,
                        'opacity': 0.9
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 2,
                        'line-color': (ele) => {
                            const targetNode = ele.target();
                            return rankToColor(targetNode.data('rank'), maxRank);
                        },
                        'target-arrow-color': (ele) => {
                            const targetNode = ele.target();
                            return rankToColor(targetNode.data('rank'), maxRank);
                        },
                        'target-arrow-shape': 'triangle',
                        'arrow-scale': 1.5,
                        'curve-style': 'unbundled-bezier',
                        'control-point-distances': [100],
                        'control-point-weights': [0.5],
                        'opacity': 0.5
                    }
                },
                {
                    selector: '.highlighted',
                    style: {
                        'opacity': 1,
                        'width': 4,
                        'z-index': 999
                    }
                },
                {
                    selector: '.dimmed',
                    style: {
                        'opacity': 0.2
                    }
                }
            ],
            layout: {
                name: 'cose',
                animate: false,
                nodeRepulsion: 400000,
                nodeOverlap: 100000,
                idealEdgeLength: 1,
                gravity: 250000,
                numIter: 400,
            }
        });

        // Nodes with no connections
        const isolatedNodes = cy.nodes().filter(node => node.degree() === 0);
        const radius = isolatedNodes.length * 10;
        isolatedNodes.forEach(node => {
            const angle = Math.random() * 2 * Math.PI;
            const r = Math.sqrt(Math.random()) * radius;
            node.position({
                x: r * Math.cos(angle) - cy.width(),
                y: r * Math.sin(angle) - cy.height()
            });
        });

        // Node click handler
        cy.on('tap', 'node', function(evt) {
            const node = evt.target;
            const connectedEdges = node.connectedEdges();
            const connectedNodes = connectedEdges.connectedNodes();

            // Highlight clicked node + connections to it
            cy.elements().addClass('dimmed');
            node.removeClass('dimmed');
            connectedEdges.removeClass('dimmed').addClass('highlighted');
            connectedNodes.removeClass('dimmed');

            // Open info panel with node data
            openInfoPanel(node.data());
        });

        // Click on background handler
        cy.on('tap', function(evt) {
            if (evt.target === cy) {
                closeInfoPanel();
            }
        });

        // Hide loading screen
        document.getElementById('loadingScreen').style.display = 'none';

    } catch (error) {
        console.error('Error loading or displaying graph: ', error);
        document.getElementById('cy').innerHTML = 'Error loading graph data. Check console for details.';
        document.getElementById('loadingScreen').style.display = 'none';
    }
}

//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\
//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\

document.addEventListener('DOMContentLoaded', () => {
    loadAndDisplayGraph();
    setupSearch();
});
