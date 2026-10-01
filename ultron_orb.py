"""
Real GPU-rendered (Three.js/WebGL) holographic AI core, replacing the
earlier Canvas2D wireframe sphere. Same render_orb(state=...) API as
before, so app.py doesn't need to change how it's called.

States: "idle", "listening", "thinking", "executing", "speaking",
        "success", "error"
("executing" currently shares thinking's visual intensity — see the
 architecture notes on why in the accompanying explanation.)
"""

_TEMPLATE = """
<div style="width:100%; display:flex; justify-content:center; background:#000;">
<div id="ultron-wrap" style="position:relative; width:100%; max-width:900px; height:__HEIGHT__px;">
  <canvas id="ultron-canvas" style="width:100%; height:100%; display:block;"></canvas>
  <div id="ultron-label" style="position:absolute; top:14px; left:50%; transform:translateX(-50%);
       color:#ffb15c; font-family:'Share Tech Mono', monospace; letter-spacing:4px;
       font-size:13px; text-shadow:0 0 8px rgba(255,140,30,0.8); pointer-events:none;">__LABEL__</div>
</div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function() {
  const wrap = document.getElementById('ultron-wrap');
  const canvas = document.getElementById('ultron-canvas');
  const W = wrap.clientWidth || 900;
  const H = __HEIGHT__;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, W / H, 0.1, 100);
  camera.position.z = 6.2;

  const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
  renderer.setSize(W, H);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  // ---- Dense particle sphere ----
  const particleCount = 4200;
  const positions = new Float32Array(particleCount * 3);
  for (let i = 0; i < particleCount; i++) {
    const r = 1.55 + Math.random() * 0.18;
    const theta = Math.acos(2 * Math.random() - 1);
    const phi = Math.random() * Math.PI * 2;
    positions[i * 3] = r * Math.sin(theta) * Math.cos(phi);
    positions[i * 3 + 1] = r * Math.sin(theta) * Math.sin(phi);
    positions[i * 3 + 2] = r * Math.cos(theta);
  }
  const pGeo = new THREE.BufferGeometry();
  pGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const pMat = new THREE.PointsMaterial({
    color: 0xffb15c, size: __PSIZE__, transparent: true, opacity: 0.85,
    blending: THREE.AdditiveBlending, depthWrite: false,
  });
  const particles = new THREE.Points(pGeo, pMat);
  scene.add(particles);

  // ---- Floating particles OUTSIDE the sphere ----
  const outerCount = 700;
  const outerPos = new Float32Array(outerCount * 3);
  for (let i = 0; i < outerCount; i++) {
    const r = 2.3 + Math.random() * 1.6;
    const theta = Math.acos(2 * Math.random() - 1);
    const phi = Math.random() * Math.PI * 2;
    outerPos[i * 3] = r * Math.sin(theta) * Math.cos(phi);
    outerPos[i * 3 + 1] = r * Math.sin(theta) * Math.sin(phi);
    outerPos[i * 3 + 2] = r * Math.cos(theta);
  }
  const oGeo = new THREE.BufferGeometry();
  oGeo.setAttribute('position', new THREE.BufferAttribute(outerPos, 3));
  const oMat = new THREE.PointsMaterial({
    color: 0xffe4bd, size: 0.014, transparent: true, opacity: 0.5,
    blending: THREE.AdditiveBlending, depthWrite: false,
  });
  const outerParticles = new THREE.Points(oGeo, oMat);
  scene.add(outerParticles);

  // ---- Wireframe geometry layer ----
  const wireGeo = new THREE.IcosahedronGeometry(1.75, 2);
  const wireMat = new THREE.MeshBasicMaterial({ color: 0xff9d4d, wireframe: true, transparent: true, opacity: 0.22 });
  const wireSphere = new THREE.Mesh(wireGeo, wireMat);
  scene.add(wireSphere);

  // ---- Rotating orbital rings ----
  const rings = [];
  for (let i = 0; i < 3; i++) {
    const ringGeo = new THREE.TorusGeometry(2.05 + i * 0.12, 0.008, 8, 120);
    const ringMat = new THREE.MeshBasicMaterial({ color: 0xffcf8a, transparent: true, opacity: 0.55 });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = Math.random() * Math.PI;
    ring.rotation.y = Math.random() * Math.PI;
    scene.add(ring);
    rings.push({ mesh: ring, dir: i % 2 === 0 ? 1 : -1, speed: 0.4 + i * 0.15 });
  }

  // ---- Central energy core + glow ----
  const coreGeo = new THREE.SphereGeometry(0.32, 32, 32);
  const coreMat = new THREE.MeshBasicMaterial({ color: 0xfff2dd, transparent: true, opacity: 0.95 });
  const core = new THREE.Mesh(coreGeo, coreMat);
  scene.add(core);

  const glowGeo = new THREE.SphereGeometry(0.55, 32, 32);
  const glowMat = new THREE.MeshBasicMaterial({ color: 0xff8c1e, transparent: true, opacity: 0.28, blending: THREE.AdditiveBlending });
  const glow = new THREE.Mesh(glowGeo, glowMat);
  scene.add(glow);

  const light = new THREE.PointLight(0xffb15c, 1.2, 10);
  light.position.set(0, 0, 3);
  scene.add(light);

  // ---- State-driven parameters ----
  const STATE = "__STATE__";
  const P = {
    idle:      { rot: 0.5,  pulse: 0.03, coreColor: 0xfff2dd, glowColor: 0xff8c1e },
    listening: { rot: 1.0,  pulse: 0.08, coreColor: 0xfff2dd, glowColor: 0xffb15c },
    thinking:  { rot: 2.4,  pulse: 0.05, coreColor: 0xfff2dd, glowColor: 0xff8c1e },
    executing: { rot: 2.8,  pulse: 0.06, coreColor: 0xfff2dd, glowColor: 0xff8c1e },
    speaking:  { rot: 1.5,  pulse: 0.14, coreColor: 0xfff2dd, glowColor: 0xffcf8a },
    success:   { rot: 1.2,  pulse: 0.20, coreColor: 0xd8ffb1, glowColor: 0xb1ff8c },
    error:     { rot: 1.2,  pulse: 0.20, coreColor: 0xffb1b1, glowColor: 0xff3b30 },
  }[STATE] || { rot: 0.5, pulse: 0.03, coreColor: 0xfff2dd, glowColor: 0xff8c1e };

  coreMat.color.setHex(P.coreColor);
  glowMat.color.setHex(P.glowColor);
  const GESTURE_SPEED_MULT = __SPEEDMULT__;

  let mouseX = 0, mouseY = 0;
  wrap.addEventListener('mousemove', (e) => {
    const rect = wrap.getBoundingClientRect();
    mouseX = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
    mouseY = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
  });

  let t = 0;
  function animate() {
    t += 0.016;

    particles.rotation.y += 0.0025 * P.rot * GESTURE_SPEED_MULT;
    particles.rotation.x += 0.0008 * P.rot * GESTURE_SPEED_MULT;
    outerParticles.rotation.y -= 0.0012 * P.rot * GESTURE_SPEED_MULT;
    wireSphere.rotation.y -= 0.0018 * P.rot * GESTURE_SPEED_MULT;
    wireSphere.rotation.x += 0.0011 * P.rot * GESTURE_SPEED_MULT;

    rings.forEach((r) => {
      r.mesh.rotation.z += 0.003 * P.rot * GESTURE_SPEED_MULT * r.dir * r.speed;
    });

    const pulse = 1 + P.pulse * Math.sin(t * 3.5);
    core.scale.set(pulse, pulse, pulse);
    glow.scale.set(pulse * 1.15, pulse * 1.15, pulse * 1.15);

    camera.position.x += (mouseX * 0.4 - camera.position.x) * 0.03;
    camera.position.y += (-mouseY * 0.3 - camera.position.y) * 0.03;
    camera.lookAt(0, 0, 0);

    renderer.render(scene, camera);
    requestAnimationFrame(animate);
  }
  animate();

  window.addEventListener('resize', () => {
    const w = wrap.clientWidth || 900;
    renderer.setSize(w, H);
    camera.aspect = w / H;
    camera.updateProjectionMatrix();
  });
})();
</script>
"""

_LABELS = {
    "idle": "ONLINE",
    "listening": "LISTENING...",
    "thinking": "THINKING...",
    "executing": "EXECUTING...",
    "speaking": "ULTRON",
    "success": "COMPLETE",
    "error": "ERROR",
}

_PARTICLE_SIZE = {
    "idle": "0.020", "listening": "0.023", "thinking": "0.024",
    "executing": "0.025", "speaking": "0.026", "success": "0.028", "error": "0.028",
}


def render_orb(state: str = "idle", size: int = 520, speed_mult: float = 1.0) -> str:
    label = _LABELS.get(state, "ONLINE")
    psize = _PARTICLE_SIZE.get(state, "0.020")
    html = _TEMPLATE.replace("__HEIGHT__", str(size))
    html = html.replace("__STATE__", state)
    html = html.replace("__LABEL__", label)
    html = html.replace("__PSIZE__", psize)
    html = html.replace("__SPEEDMULT__", str(speed_mult))
    return html
