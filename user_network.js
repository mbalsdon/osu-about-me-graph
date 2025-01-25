let cy;

const RANK_RANGE_SIZE = 100;

/**
 * Nonstatic files will not be used if the flag is set to true, and vice-versa.
 * You have to populate these yourself using the python tool.
 * Make sure to place them in the same directory as this file.
 * You don't have to add them all, but if you don't, make sure to append the mode param.
 * For example, if you only have graph_data_taiko.json, you will need to open .../user_network.html?mode=taiko in your browser.
 *
 * See README.md for more information.
 */
const USE_STATIC_GRAPH_DATA = true;
const GRAPH_DATA_FILENAMES = {
    nonstatic_osu   : "graph_data_osu.json",
    nonstatic_taiko : "graph_data_taiko.json",
    nonstatic_mania : "graph_data_mania.json",
    nonstatic_fruits : "graph_data_fruits.json",

    static_osu   : "static_graph_data_osu.json",
    static_taiko : "static_graph_data_taiko.json",
    static_mania : "static_graph_data_mania.json",
    static_fruits : "static_graph_data_fruits.json",
};
const GAMEMODES = ['osu', 'taiko', 'mania', 'fruits'];

//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\
//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\

/**
 * Return graph data filename associated with gamemode.
 */
function getJsonFilename(gamemode) {
    const filenameKey = (USE_STATIC_GRAPH_DATA ? `static_${gamemode}` : `nonstatic_${gamemode}`);
    return GRAPH_DATA_FILENAMES[filenameKey];
}

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
* Open info panel for given node.
*/
function openInfoPanel(nodeData) {
    const node = cy.$(`node[id = "${nodeData.id}"]`);
    const incomingNodes = node.incomers().nodes().map(n =>
        `- <a href="#" onclick="handleNodeClick('${n.id()}'); return false;" style="color: #00aaff; text-decoration: none;">
            ${n.data('label')}
        </a> (#${n.data('rank')})`
    ).join('<br>');

    const outgoingNodes = node.outgoers().nodes().map(n =>
        `- <a href="#" onclick="handleNodeClick('${n.id()}'); return false;" style="color: #00aaff; text-decoration: none;">
            ${n.data('label')}
        </a> (#${n.data('rank')})`
    ).join('<br>');

    document.getElementById('infoTitle').innerHTML = `
        <a href="https://osu.ppy.sh/users/${nodeData.label}" target="_blank" style="color: #00aaff; text-decoration: none;">
            ${nodeData.label}
        </a> (#${nodeData.rank})
        <hr></hr>
    `.trim();

    document.getElementById('infoContent').innerHTML = `
        <strong>Mentions:</strong><br>
        ${outgoingNodes || 'None'}<br>
        <br>
        <strong>Mentioned by:</strong><br>
        ${incomingNodes || 'None'}
    `.trim();

    document.getElementById('legend').classList.remove('open');
    document.getElementById('toggle-button').textContent = '←';
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
 * Node click event handler.
 */
function handleNodeClick(nodeId) {
    const node = cy.$(`node[id = "${nodeId}"]`);
    const nodeData = node.data();

    // Reset previous highlighting
    cy.elements().removeClass('highlighted dimmed');

    // Highlight new selection
    cy.elements().addClass('dimmed');
    node.removeClass('dimmed');
    node.connectedEdges().removeClass('dimmed').addClass('highlighted');
    node.connectedEdges().connectedNodes().removeClass('dimmed');

    // Update info panel
    openInfoPanel(nodeData);
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
* Generate legend, rows contain color patch and associated rank range.
*/
function createLegend(maxRank) {
    const legendContent = document.getElementById('legend-content');
    const numRanges = Math.ceil(maxRank / RANK_RANGE_SIZE);

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
        legendContent.appendChild(legendItem);
    }
}

//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\
//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\

/**
* Load graph data and put into page.
*/
async function loadAndDisplayGraph(gamemode) {
    try {
        const start = performance.now();

        // Retrieve graph data
        const response = await fetch(getJsonFilename(gamemode), {cache: 'no-store'});
        const graphData = await response.json();

        // Create legend
        const toggleButton = document.getElementById('toggle-button');
        const legend = document.getElementById('legend');

        toggleButton.addEventListener('click', () => {
            legend.classList.toggle('open');
            toggleButton.textContent = legend.classList.contains('open') ? '→' : '←';

            closeInfoPanel();
        });

        const maxRank = Math.max(...graphData.nodes.map(node => node.data.rank));
        createLegend(maxRank);

        // Generate graph
        const numUsers = graphData['nodes'].length;

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
                        'background-color': (ele) => rankToColor(ele.data('rank'), numUsers),
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
                            return rankToColor(targetNode.data('rank'), numUsers);
                        },
                        'target-arrow-color': (ele) => {
                            const targetNode = ele.target();
                            return rankToColor(targetNode.data('rank'), numUsers);
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
            layout: USE_STATIC_GRAPH_DATA ? { name: 'preset' } : {
                name: 'cose',
                animate: false,
                nodeRepulsion: 400 * numUsers,
                nodeOverlap: 100 * numUsers,
                idealEdgeLength: 0.001 * numUsers,
                gravity: 200 * numUsers,
                numIter: 500,
            }
        });

        // Nodes with no connections
        const isolatedNodes = cy.nodes().filter(node => node.degree() === 0);
        const radius = isolatedNodes.length * 5;
        isolatedNodes.forEach(node => {
            const angle = Math.random() * 2 * Math.PI;
            const r = Math.sqrt(Math.random()) * radius;
            node.position({
                x: r * Math.cos(angle) - (cy.width() * (numUsers / 1000)),
                y: r * Math.sin(angle) - (cy.height() * (numUsers / 1000))
            });
        });

        // Node click handler
        cy.on('tap', 'node', function(evt) {
            const node = evt.target;
            handleNodeClick(node.data().id);
        });

        // Click on background handler
        cy.on('tap', function(evt) {
            if (evt.target === cy) {
                closeInfoPanel();
            }
        });

        // Hide loading screen
        document.getElementById('loadingScreen').style.display = 'none';

        const end = performance.now();
        console.log(`Graph load took ${(end - start) / 1000} seconds.`);

    } catch (error) {
        console.error('Error loading or displaying graph: ', error);
        document.getElementById('cy').style.color = 'white';
        document.getElementById('cy').innerHTML = 'Error loading graph data. Check console for details.';
        document.getElementById('loadingScreen').style.display = 'none';
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
 * Setup dropdown for selecting gamemodes.
 */
async function setupGamemodeDropdown() {
    const gamemodeDropdown = document.querySelector('.dropdown-select');

    // Check if data exists for each gamemode
    for (const gamemode of GAMEMODES) {
        const option = gamemodeDropdown.querySelector(`option[value="${gamemode}"]`);
        const filenameKey = (USE_STATIC_GRAPH_DATA ? `static_${gamemode}` : `nonstatic_${gamemode}`);
        const filename = GRAPH_DATA_FILENAMES[filenameKey];
        const response = await fetch(filename);

        if (!response.ok) {
            option.disabled = true;
        }
    }

    // Setup dropdown handler
    gamemodeDropdown.addEventListener('change', (event) => {
        const selectedMode = event.target.value;
        window.location.href = window.location.pathname + '?mode=' + selectedMode;
    });

    // Select initial option
    const urlParams = new URLSearchParams(window.location.search);
    const gamemode = urlParams.get('mode') || 'osu';
    gamemodeDropdown.value = gamemode;
}

/**
 * Setup source code button.
 */
function setupSourceButton() {
    const sourceButton = document.getElementById('sourceButton');
    sourceButton.addEventListener('mouseover', () => {
        sourceButton.style.backgroundColor = '#333';
    });

    sourceButton.addEventListener('mouseout', () => {
        sourceButton.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    });

    sourceButton.addEventListener('click', () => {
        window.open('https://github.com/mbalsdon/osu-about-me-graph/', '_blank');
    });
}

/**
 * Setup download button.
 */
function setupDownloadButton(gamemode) {
    const downloadButton = document.getElementById('downloadButton');
    downloadButton.addEventListener('mouseover', () => {
        downloadButton.style.backgroundColor = '#333';
    });

    downloadButton.addEventListener('mouseout', () => {
        downloadButton.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    });

    downloadButton.addEventListener('click', () => {
        const staticGraphData = {
            nodes: cy.nodes().map(node => ({
                data: node.data(),
                position: node.position()
            })),
            edges: cy.edges().map(edge => ({
                data: edge.data()
            }))
        };
        const dataStr = JSON.stringify(staticGraphData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `static_graph_data_${gamemode}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    });
}

//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\
//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\

/**
 * Entrypoint (basically)
 */
document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const gamemode = urlParams.get('mode') || 'osu';

    loadAndDisplayGraph(gamemode);
    setupSearch();
    setupGamemodeDropdown();
    setupSourceButton();
    setupDownloadButton(gamemode);
});
