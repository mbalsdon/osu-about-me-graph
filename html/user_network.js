/**
 * Nonstatic files will not be used if the flag is set to true, and vice-versa.
 * You have to populate these yourself using the python tool.
 * Make sure to place them in the same directory as this file.
 * You don't have to add them all, but if you don't, make sure to append the mode param.
 * For example, if you only have graph_data_taiko.json, you will need to open .../user_network.html?mode=taiko in your browser.
 *
 * See README.md for more information.
 */
const USE_STATIC_GRAPH_DATA = false;
const GRAPH_DATA_FILENAMES = {
    nonstatic_osu    : 'graph_data_osu.json',
    nonstatic_taiko  : 'graph_data_taiko.json',
    nonstatic_mania  : 'graph_data_mania.json',
    nonstatic_fruits : 'graph_data_fruits.json',

    static_osu    : 'static_graph_data_osu.json',
    static_taiko  : 'static_graph_data_taiko.json',
    static_mania  : 'static_graph_data_mania.json',
    static_fruits : 'static_graph_data_fruits.json',
};
const GAMEMODES = ['osu', 'taiko', 'mania', 'fruits'];
const RANK_RANGE_SIZE = 100;

let cy;
let selectedUserOutgoingUsernames = [];
let profileDataOpen = false;
let ignoredStr = "";
let ignoredOpen = false;
let aboutOpen = false;
let isResizing = false;
let startY, startHeight;

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
    const incomingNodes = node.incomers().nodes();
    const incomingNodesHTML = incomingNodes.map(n =>
        `• <a href="#" onclick="handleNodeClick('${n.id()}'); return false;" class="href" onmouseover="this.style.color='#0088ff'" onmouseout="this.style.color='#00aaff'">
            ${n.data('label')}
        </a> (#${n.data('rank')})`
    ).join('<br>');

    const outgoingNodes = node.outgoers().nodes();
    const outgoingNodesHTML = outgoingNodes.map(n =>
        `• <a href="#" onclick="handleNodeClick('${n.id()}'); return false;" class="href" onmouseover="this.style.color='#0088ff'" onmouseout="this.style.color='#00aaff'">
            ${n.data('label')}
        </a> (#${n.data('rank')})`
    ).join('<br>');

    // Gstate to avoid quoting problems from passing into inlined fn yesssssssss this is bad whatever man 
    selectedUserOutgoingUsernames = [];
    for (const outgoer of node.outgoers().nodes()) {
        selectedUserOutgoingUsernames.push(outgoer.id());
        for (const prevUsername of outgoer.data('previous_usernames')) {
            if (prevUsername.startsWith('users/')) selectedUserOutgoingUsernames.push(prevUsername.substring(6));
            else selectedUserOutgoingUsernames.push(prevUsername);
        }
    }

    document.getElementById('infoTitle').innerHTML = `
        <a href="#" onclick="handleNodeClick('${nodeData.id}'); return false;" class="href" onmouseover="this.style.color='#0088ff'" onmouseout="this.style.color='#00aaff'">
            ${nodeData.label}
        </a> (#${nodeData.rank})
        <div onclick="openProfileData('${nodeData.id}', \`${encodeURIComponent(nodeData.about_me)}\`);" style="cursor: pointer; font-size: 10px; color: #0099ff; margin-top: 4px; font-weight: normal;" onmouseover="this.style.color='#0077ff'" onmouseout="this.style.color='#0099ff'">View raw profile data</div>
        <hr></hr>
    `.trim();

    document.getElementById('infoContent').innerHTML = `
        <strong>Mentions (${outgoingNodes.length} players):</strong><br>
        ${outgoingNodesHTML || 'None'}<br>
        <br>
        <strong>Mentioned by (${incomingNodes.length} players):</strong><br>
        ${incomingNodesHTML || 'None'}
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
 * Open raw profile data modal.
 */
function openProfileData(id, encodedAboutMe) {
    if (profileDataOpen) { return; }
    profileDataOpen = true;

    const aboutMe = decodeURIComponent(encodedAboutMe);

    const overlay = document.createElement('div');
    overlay.className = 'modal';

    const modal = document.createElement('div');
    modal.className = 'modalText';

    let highlighted = aboutMe.replace(
        new RegExp(selectedUserOutgoingUsernames.map(s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|'), 'gi'),
        match => `<span style="background-color: #cfb600; color: black;">${match}</span>`
    );

    modal.innerHTML = `
        <h2>${id}</h2>
        <div>${highlighted}</div>
        <button onclick="this.parentElement.parentElement.remove(); profileDataOpen = false;" style="position: absolute; top: 10px; right: 10px; background: none; border: none; color: white; font-size: 20px; cursor: pointer;">×</button>
    `;

    modal.addEventListener('scroll', (e) => e.stopPropagation());

    const style = document.createElement('style');
    style.textContent = `
        .modal::-webkit-scrollbar {
            display: none;
        }
    `;
    document.head.appendChild(style);
    modal.classList.add('modal');

    overlay.onclick = (e) => {
        if (e.target === overlay) {
            overlay.remove();
            profileDataOpen = false;
        }
    };

    overlay.appendChild(modal);
    document.body.appendChild(overlay);
}

/**
 * Format and store ignored usernames to global var
 */
function formatIgnoredUsernames(ignoredUsernames) {
    for (const ignoredUsername of ignoredUsernames) ignoredStr += `<div style="margin-bottom: 1px;">• ${ignoredUsername}</div>`;
}

/**
 * Open "ignored usernames" modal.
 */
function openIgnoredPanel() {
    if (ignoredOpen) { return; }
    ignoredOpen = true;

    const overlay = document.createElement('div');
    overlay.className = 'modal';

    const modal = document.createElement('div');
    modal.className = 'modalText';

    const style = document.createElement('style');
    document.head.appendChild(style);
    modal.classList.add('modal');

    modal.innerHTML = `
        <div style="white-space: pre-line">
            <strong style="font-size: 26px">List of Ignored Usernames</strong>\n
            ${ignoredStr}
        </div>
        <button onclick="this.parentElement.parentElement.remove(); ignoredOpen = false;" style="position: absolute; top: 10px; right: 10px; background: none; border: none; color: white; font-size: 20px; cursor: pointer;">×</button>
    `;

    overlay.onclick = (e) => {
        if (e.target === overlay) {
            overlay.remove();
            ignoredOpen = false;
        }
    };

    overlay.appendChild(modal);
    document.body.appendChild(overlay);
}

/**
 * Open "what is this" modal.
 */
function openAboutPanel(numUsers) {
    if (aboutOpen) { return; }
    aboutOpen = true;

    const overlay = document.createElement('div');
    overlay.className = 'modal';

    const modal = document.createElement('div');
    modal.className = 'modalText';

    const style = document.createElement('style');
    document.head.appendChild(style);
    modal.classList.add('modal');

    modal.innerHTML = `
        <div style="white-space: pre-line">
            <strong style="font-size: 26px">What Am I Looking At?</strong>\n
            <div style="margin-bottom: 1px;">• This is a graph network based on the "me!" pages of osu! players.</div>
            <div style="margin-bottom: 1px;">• If player "whitecat" mentions player "mrekk" in their page, an arrow is drawn between the two.</div>
            <div style="margin-bottom: 1px;">• Player nodes are larger if more people mention them in their pages. Node color is based on rank.</div>
        </div>
        <div style="white-space: pre-line">
            <strong style="font-size: 26px">A Few Notes</strong>\n
            <div style="margin-bottom: 1px;">• Some usernames have been filtered out because they trigger false-positives. For example, mentions may incorrectly be attributed to the player "wooting" if a player lists "wooting" in the keyboard specs on their page.</div>
            <div style="margin-bottom: 1px;">• Past usernames are taken into account. For example, if someone mentions "cookiezi" but their current username is "chocomint", the algorithm will correctly attribute 2 mentions to "chocomint".</div>
            <div style="margin-bottom: 1px;">• Rename conflicts are resolved to the best of the algorithm's ability. For example, if "shigetora" renames to "cookiezi", the name "shigetora" can be taken by somebody else. In this case, mentions are attributed to the player with more followers.</div>
            <div style="margin-bottom: 1px;">• Username reverts are unaccounted for. If "kurtis-" requests a username revert from osu! staff back to "Sour_Key", the name "kurtis-" gets erased from osu!'s side, and thus mentions to "kurtis-" won't be able to be considered.</div>
            <div style="margin-bottom: 1px;">• Typos are not be accounted for. For example, if someone mentions "kurtis" on their page but the username is "kurtis-", a mention will not be tallied.</div>
            <div style="margin-bottom: 1px;">• Mentions from users past rank #${numUsers} are not counted. That is, if a user "spreadnuts" ranked #${numUsers + 500} mentions a user "igibob" ranked #${numUsers - 25}, it will not be counted here.</div>
            <div style="margin-bottom: 1px;">• This data was collected on YYYY-MM-DD.</div>
        </div>
        <button onclick="this.parentElement.parentElement.remove(); aboutOpen = false;" style="position: absolute; top: 10px; right: 10px; background: none; border: none; color: white; font-size: 20px; cursor: pointer;">×</button>
    `;

    overlay.onclick = (e) => {
        if (e.target === overlay) {
            overlay.remove();
            aboutOpen = false;
        }
    };

    overlay.appendChild(modal);
    document.body.appendChild(overlay);
}

/**
 * Node click event handler.
 */
function handleNodeClick(nodeId) {
    const node = cy.$(`node[id = "${nodeId}"]`);
    const nodeData = node.data();

    // Move viewport to selected node
    cy.animate({
        center: { eles: node },
        duration: 500,
        easing: 'ease-in-out'
    });

    // Reset previous highlighting and highlight new selection after animation completes
    setTimeout(() => {
        cy.elements().removeClass('highlighted dimmed');
        cy.elements().addClass('dimmed');
        node.removeClass('dimmed');
        node.connectedEdges().removeClass('dimmed').addClass('highlighted');
        node.connectedEdges().connectedNodes().removeClass('dimmed');
    }, 500);

    // Update info panel
    openInfoPanel(nodeData);
}

/**
 * Mouse move handler for info panel resizing.
 */
function handleMouseMove(e) {
    if (!isResizing) return;
    const delta = startY - e.clientY;
    const newHeight = Math.min(Math.max(startHeight + delta, 100), window.innerHeight * 0.8);
    infoPanel.style.height = `${newHeight}px`;
}

/**
* Generate legend, rows contain color patch and associated rank range.
*/
function createLegend(maxRank) {
    const legendRanks = document.getElementById('legend-ranks');
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
        legendRanks.appendChild(legendItem);
    }
}

/**
 * Sort users by mentions and place them in the legend.
 */
function populateSidebarUsers() {
    const legendMentionsSorted = document.getElementById('legend-mentions-sorted');

    const sortedNodes = cy.nodes().sort((a, b) => {
        const incomersA = a.incomers().nodes().length;
        const incomersB = b.incomers().nodes().length;
        if (incomersB !== incomersA) { return incomersB - incomersA; }
        return a.id().localeCompare(b.id());
    });

    for (const [i, node] of Array.from(sortedNodes).entries()) {
        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';
        legendItem.style.fontSize = '14px';

        legendItem.innerHTML = `
            ${i+1}.&nbsp<a href="#" onclick="handleNodeClick('${node.id()}'); return false;" class="href" onmouseover="this.style.color='#0088ff'" onmouseout="this.style.color='#00aaff'">
                ${node.id()}
            </a>&nbsp(${node.incomers().nodes().length} mentions)
            <br>`;

        legendMentionsSorted.appendChild(legendItem);
    }
}

//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\
//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\

/**
* Load graph data and put into page.
*/
async function loadAndDisplayGraph(gamemode) {
    try {
        // Retrieve graph data
        let start = performance.now();
        const response = await fetch(getJsonFilename(gamemode), {cache: 'no-store'});
        const graphData = await response.json();
        formatIgnoredUsernames(graphData['ignored']);
        let end = performance.now();
        console.log(`Graph load took ${(end - start) / 1000} seconds.`);

        // Create legend
        start = performance.now();
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

        // Populate sidebar users once graph is done
        cy.ready(() => {
            populateSidebarUsers();
            setupAboutButton(numUsers);
        });

        // Hide loading screen
        document.getElementById('loadingScreen').style.display = 'none';

        end = performance.now();
        console.log(`Graph generation took ${(end - start) / 1000} seconds.`);

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
                    handleNodeClick(node.id());
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
 * Setup ignored usernames button.
 */
function setupIgnoredButton() {
    const ignoredButton = document.getElementById('ignoredButton');
    ignoredButton.addEventListener('mouseover', () => {
        ignoredButton.style.backgroundColor = '#333';
    });

    ignoredButton.addEventListener('mouseout', () => {
        ignoredButton.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    });

    ignoredButton.addEventListener('click', () => { openIgnoredPanel(); });
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

/**
 * Setup about button.
 */
function setupAboutButton(numUsers) {
    const aboutButton = document.getElementById('aboutButton');
    aboutButton.addEventListener('mouseover', () => {
        aboutButton.style.backgroundColor = '#333';
    });

    aboutButton.addEventListener('mouseout', () => {
        aboutButton.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    });

    aboutButton.addEventListener('click', () => { openAboutPanel(numUsers); });
}

/**
 * Setup info panel resize handle.
 */
function setupInfoPanelResizeHandle() {
    document.getElementById('infoPanelResizeHandle').addEventListener('mousedown', (e) => {
        isResizing = true;
        startY = e.clientY;
        startHeight = parseInt(getComputedStyle(infoPanel).height);
    
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', () => {
            isResizing = false;
            document.removeEventListener('mousemove', handleMouseMove);
        });
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
    setupIgnoredButton();
    setupDownloadButton(gamemode);
    setupInfoPanelResizeHandle();
});
