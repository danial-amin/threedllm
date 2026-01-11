// Three.js 3D Viewer for ThreeDLLM

class ThreeDViewer {
    constructor(containerId, canvasId) {
        this.container = document.getElementById(containerId);
        this.canvas = document.getElementById(canvasId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.currentMesh = null;
        this.animationId = null;
        
        this.init();
    }
    
    init() {
        // Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x1a1a1a);
        
        // Camera
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        this.camera.position.set(0, 0, 5);
        
        // Renderer
        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: true
        });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        
        // Controls - wait for OrbitControls to be available
        this.setupControls();
        
        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);
        
        const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight1.position.set(5, 5, 5);
        this.scene.add(directionalLight1);
        
        const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.4);
        directionalLight2.position.set(-5, -5, -5);
        this.scene.add(directionalLight2);
        
        // Grid helper
        const gridHelper = new THREE.GridHelper(10, 10, 0x444444, 0x222222);
        this.scene.add(gridHelper);
        
        // Axes helper
        const axesHelper = new THREE.AxesHelper(2);
        this.scene.add(axesHelper);
        
        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize());
        
        // Start animation loop
        this.animate();
    }
    
    setupControls() {
        // Wait for OrbitControls to be available
        const checkControls = () => {
            if (window.THREE_OrbitControls) {
                this.controls = new window.THREE_OrbitControls(this.camera, this.renderer.domElement);
                this.controls.enableDamping = true;
                this.controls.dampingFactor = 0.05;
                this.controls.minDistance = 1;
                this.controls.maxDistance = 20;
            } else {
                // Retry after a short delay (max 5 seconds)
                if (this.controlRetries === undefined) {
                    this.controlRetries = 0;
                }
                if (this.controlRetries < 50) {
                    this.controlRetries++;
                    setTimeout(checkControls, 100);
                } else {
                    console.warn('OrbitControls not available - viewer will work but without controls');
                }
            }
        };
        checkControls();
    }
    
    onWindowResize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }
    
    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());
        
        if (this.controls) {
            this.controls.update();
        }
        
        this.renderer.render(this.scene, this.camera);
    }
    
    loadMesh(url, format) {
        return new Promise((resolve, reject) => {
            // Remove existing mesh
            if (this.currentMesh) {
                this.scene.remove(this.currentMesh);
                this.disposeMesh(this.currentMesh);
            }
            
            // Wait for modules to be ready if they're not yet
            const tryGetLoader = (retries = 0) => {
                const loader = this.getLoader(format);
                if (loader) {
                    this.loadWithLoader(loader, url, resolve, reject);
                } else if (retries < 100 && !window.threeModulesReady) {
                    // Wait for modules to load (max 10 seconds)
                    setTimeout(() => tryGetLoader(retries + 1), 100);
                } else {
                    const available = {
                        OBJ: !!window.THREE_OBJLoader,
                        PLY: !!window.THREE_PLYLoader,
                        STL: !!window.THREE_STLLoader,
                        Controls: !!window.THREE_OrbitControls,
                        ready: window.threeModulesReady
                    };
                    reject(new Error(`Failed to load loader for format: ${format}. Available loaders: ${JSON.stringify(available)}`));
                }
            };
            
            tryGetLoader();
        });
    }
    
    loadWithLoader(loader, url, resolve, reject) {
            
        loader.load(
            url,
            (object) => {
                // Handle different loader return types
                let mesh = this.processLoadedObject(object);
                
                // Center and scale the mesh
                this.centerAndScaleMesh(mesh);
                
                // Add to scene
                this.currentMesh = mesh;
                this.scene.add(mesh);
                
                // Update camera to fit mesh
                this.fitCameraToMesh(mesh);
                
                resolve(mesh);
            },
            (progress) => {
                // Loading progress
                if (progress.lengthComputable) {
                    const percent = (progress.loaded / progress.total) * 100;
                    console.log('Loading progress:', percent.toFixed(0) + '%');
                }
            },
            (error) => {
                console.error('Loader error:', error);
                reject(new Error('Failed to load 3D model: ' + error.message));
            }
        );
    }
    
    processLoadedObject(object) {
        // Handle different loader return types
        // Check if object is a geometry (STL loader returns geometry directly)
        if (object && (object.isBufferGeometry || object.isGeometry || 
            (object.attributes && (object.attributes.position || object.attributes.normal)))) {
            // Geometry only - create mesh
            const material = this.createDefaultMaterial();
            return new THREE.Mesh(object, material);
        }
        
        // Check if object is a Mesh
        if (object && object.isMesh) {
            // Ensure material exists
            if (!object.material) {
                object.material = this.createDefaultMaterial();
            }
            return object;
        }
        
        // Check if object is a Group
        if (object && object.isGroup) {
            // Group - return as is or wrap children
            if (object.children.length === 1) {
                return object.children[0];
            }
            return object;
        }
        
        // Check for children array (Scene, Group, etc.)
        if (object && object.children && object.children.length > 0) {
            // Scene or group with children
            if (object.children.length === 1) {
                return object.children[0];
            }
            const group = new THREE.Group();
            object.children.forEach(child => group.add(child));
            return group;
        }
        
        // Fallback - try to create mesh from object
        if (object) {
            const material = this.createDefaultMaterial();
            return new THREE.Mesh(object, material);
        }
        
        // Last resort - wrap in group
        const group = new THREE.Group();
        if (object) {
            group.add(object);
        }
        return group;
    }
    
    createDefaultMaterial() {
        return new THREE.MeshStandardMaterial({
            color: 0x6366f1,
            metalness: 0.3,
            roughness: 0.7,
            side: THREE.DoubleSide
        });
    }
    
    getLoader(format) {
        // Normalize format - trim whitespace and convert to lowercase
        const normalizedFormat = String(format || '').trim().toLowerCase();
        
        console.log('Getting loader for format:', normalizedFormat);
        console.log('Available loaders:', {
            OBJ: !!window.THREE_OBJLoader,
            PLY: !!window.THREE_PLYLoader,
            STL: !!window.THREE_STLLoader,
            modulesReady: window.threeModulesReady
        });
        
        switch (normalizedFormat) {
            case 'obj':
                if (window.THREE_OBJLoader) {
                    return new window.THREE_OBJLoader();
                }
                console.error('OBJLoader not available. Modules ready:', window.threeModulesReady);
                return null;
            case 'ply':
                if (window.THREE_PLYLoader) {
                    return new window.THREE_PLYLoader();
                }
                console.error('PLYLoader not available. Modules ready:', window.threeModulesReady);
                return null;
            case 'stl':
                if (window.THREE_STLLoader) {
                    return new window.THREE_STLLoader();
                }
                console.error('STLLoader not available. Modules ready:', window.threeModulesReady);
                return null;
            default:
                console.error(`Unsupported format: "${format}" (normalized: "${normalizedFormat}")`);
                return null;
        }
    }
    
    centerAndScaleMesh(mesh) {
        // Compute bounding box
        const box = new THREE.Box3().setFromObject(mesh);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        
        // Center the mesh
        mesh.position.sub(center);
        
        // Scale to fit in a reasonable size
        const maxDim = Math.max(size.x, size.y, size.z);
        if (maxDim > 0) {
            const scale = 2 / maxDim;
            mesh.scale.multiplyScalar(scale);
        }
    }
    
    fitCameraToMesh(mesh) {
        const box = new THREE.Box3().setFromObject(mesh);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        
        const maxDim = Math.max(size.x, size.y, size.z);
        const distance = maxDim * 2.5;
        
        this.camera.position.set(distance, distance, distance);
        this.camera.lookAt(center);
        if (this.controls) {
            this.controls.target.copy(center);
            this.controls.update();
        }
    }
    
    resetView() {
        if (this.currentMesh) {
            this.fitCameraToMesh(this.currentMesh);
        } else {
            this.camera.position.set(0, 0, 5);
            if (this.controls) {
                this.controls.target.set(0, 0, 0);
                this.controls.update();
            }
        }
    }
    
    disposeMesh(mesh) {
        if (mesh.geometry) {
            mesh.geometry.dispose();
        }
        if (mesh.material) {
            if (Array.isArray(mesh.material)) {
                mesh.material.forEach(mat => mat.dispose());
            } else {
                mesh.material.dispose();
            }
        }
        if (mesh.children) {
            mesh.children.forEach(child => this.disposeMesh(child));
        }
    }
    
    dispose() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        if (this.currentMesh) {
            this.scene.remove(this.currentMesh);
            this.disposeMesh(this.currentMesh);
        }
        
        if (this.renderer) {
            this.renderer.dispose();
        }
    }
}

// Global viewer instance
let viewer = null;

// Initialize viewer when page loads
function initViewer() {
    if (document.getElementById('viewerContainer') && document.getElementById('threejsCanvas')) {
        if (!viewer) {
            viewer = new ThreeDViewer('viewerContainer', 'threejsCanvas');
        }
        return viewer;
    }
    return null;
}

// Load mesh from URL
async function loadMeshInViewer(url, format = 'obj') {
    if (!viewer) {
        const v = initViewer();
        if (!v) {
            console.error('Viewer initialization failed');
            return;
        }
    }
    
    try {
        await viewer.loadMesh(url, format);
        console.log('Mesh loaded successfully');
    } catch (error) {
        console.error('Error loading mesh:', error);
        alert('Failed to load 3D model: ' + error.message);
    }
}

// Reset viewer
function resetViewerView() {
    if (viewer) {
        viewer.resetView();
    }
}
