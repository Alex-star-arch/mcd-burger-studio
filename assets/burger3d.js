/* =========================================================================
 *  麦当劳「真」随心配 · 3D 引擎  (Burger3D)  v3.0  —— 官方素材唯一来源版
 *  合规要求：汉堡本体及其内部所有食材(牛肉/芝士/蔬菜/水果等)
 *            一律使用麦当劳官方提供的产品图(assets/mcd_photos/*.png)呈现，
 *            【不使用任何自定义或占位几何/贴图】。
 *  实现：每个被选中的麦当劳产品 = 一张官方透明 PNG，作为 3D 布告板(billboard)
 *        在轨道可控的 3D 场景中按官方规范顺序排列(单一堡直接呈现官方整图，
 *        其内部的牛肉/芝士/蔬菜/水果顺序由官方产品图本身保证)。
 *  排序规范：official_composition.json 的 priority(分类)+ compositions(组成顺序)。
 *  依赖：three.min.js (r128) + OrbitControls.js（已本地化到 assets/vendor）
 * ========================================================================= */
(function (global) {
  "use strict";
  const THREE = global.THREE;

  /* ----------------- 分类（仅用于"官方规范排序"的优先级） ----------------- */
  function classify(mat) {
    const n = mat.name || "";
    const role = mat.role || "";
    if (/帽|徽章|贴|捶|按摩|棒球|周边|玩具|公仔|盲盒|支撑|手办|八音盒|拼图/.test(n)) return { kind: "merch", label: "周边" };
    if (role === "drink" || /可乐|雪碧|果汁|咖啡|红茶|奶茶|奶|橙|水|阿芙佳朵|奶铁|美式|汽水|柠檬|苹果汁|燕麦|苏打/.test(n)) return { kind: "drink", label: "饮品" };
    if (role === "dessert" || /新地|麦旋风|圆筒|冰淇淋|派|黑巧|圣代|冰炫风/.test(n)) return { kind: "dessert", label: "甜品" };
    if (/薯条|薯饼|扭扭薯|薯/.test(n)) return { kind: "fries", label: "小食" };
    if (role === "side" && /四宫格|小食盘|分享盒|桶/.test(n)) return { kind: "snack", label: "小食" };
    if (role === "sauce" || /酱/.test(n)) return { kind: "sauce", label: "酱料" };
    if (role === "cheese" || /芝士|吉士|高达|马苏里拉|芝|干酪/.test(n)) return { kind: "cheese", label: "芝士" };
    if (role === "veg" || /玉米|苹果片|蔬菜|沙拉|蔬果|黄瓜|洋葱|生菜|番茄|酸/.test(n)) return { kind: "veg", label: "蔬果" };
    if (role === "fish" || /鱼|虾|三文鱼|鳕鱼|海鲜|虾排/.test(n)) return { kind: "fish", label: "鱼排" };
    if (role === "chicken" || /鸡|翅|鸡块|鸡排|鸡腿|鸡柳/.test(n)) return { kind: "chicken", label: "鸡排" };
    if (/培根/.test(n)) return { kind: "bacon", label: "培根" };
    if (role === "beef" || /牛|安格斯|板烧|牛肉|牛堡/.test(n)) return { kind: "beef", label: "牛肉" };
    if (role === "burger" || /堡|汉堡|麦满分|月堡|Mac/.test(n)) return { kind: "burger", label: "汉堡" };
    if (/蛋|蛋堡|蛋卷/.test(n)) return { kind: "egg", label: "蛋" };
    return { kind: "generic", label: "其他" };
  }

  // 官方规范排序优先级（来自 official_composition.json）
  const PRIORITY = {
    burger: 0, beef: 1, chicken: 2, fish: 3, cheese: 4, bacon: 5,
    veg: 6, egg: 7, sauce: 8, drink: 20, dessert: 21, fries: 22, snack: 23, merch: 24, generic: 30,
  };
  function rolePriority(kind) { return PRIORITY[kind] != null ? PRIORITY[kind] : 30; }

  function isWholeBurger(mat) {
    const n = mat.name || "";
    return /堡|汉堡|麦满分|月堡|Mac|三明治|卷/.test(n);
  }

  /* ----------------- 官方产品图（照片级，唯一食材来源） ----------------- */
  let _photoLoader = null; // fn(code) -> THREE.Texture | null
  function setPhotoLoader(fn) { _photoLoader = fn; }
  function getPhoto(code) { return _photoLoader ? _photoLoader(code) : null; }

  // 中性柔和接触阴影（非食物影像，仅用于 3D 纵深表现）
  const _texCache = {};
  function shadowTexture() {
    if (_texCache.shadow) return _texCache.shadow;
    const c = document.createElement("canvas"); c.width = c.height = 256;
    const x = c.getContext("2d");
    const g = x.createRadialGradient(128, 128, 10, 128, 128, 128);
    g.addColorStop(0, "rgba(40,28,12,0.32)"); g.addColorStop(0.6, "rgba(40,28,12,0.14)"); g.addColorStop(1, "rgba(40,28,12,0)");
    x.fillStyle = g; x.fillRect(0, 0, 256, 256);
    const t = new THREE.CanvasTexture(c); t.encoding = THREE.sRGBEncoding;
    return (_texCache.shadow = t);
  }

  // 单个产品 = 官方透明 PNG 布告板（始终正对相机，呈现真实商品外观）
  function buildBillboard(mat, opts) {
    opts = opts || {};
    const tex = getPhoto(mat.code);
    const g = new THREE.Group();
    let w = 1.6, h = 1.6;
    if (tex && tex.image && tex.image.width && tex.image.height) {
      const aspect = tex.image.width / tex.image.height;
      const TARGET = 2.2; // 统一高度基准
      if (aspect >= 1) { h = TARGET; w = TARGET * aspect; }
      else { w = TARGET * 0.92; h = w / aspect; }
    }
    const geo = new THREE.PlaneGeometry(w, h);
    const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({
      map: tex || null, transparent: true, alphaTest: 0.42, side: THREE.DoubleSide, depthWrite: true,
    }));
    m.userData.billboard = true;
    g.add(m);
    // 接触阴影（仅纵深，非食物）
    const sh = new THREE.Mesh(new THREE.PlaneGeometry(w * 1.05, w * 0.5),
      new THREE.MeshBasicMaterial({ map: shadowTexture(), transparent: true, depthWrite: false }));
    sh.rotation.x = -Math.PI / 2; sh.position.y = 0.01; sh.position.z = 0.15;
    g.add(sh);
    return { obj: g, height: h, width: w, fromPhoto: !!tex };
  }

  /* ----------------- 装配：按官方规范顺序堆垛官方图 ----------------- */
  function buildBurger(codes, byCode, opts) {
    opts = opts || {};
    const group = new THREE.Group();
    const items = [];
    for (const c of codes) {
      const mat = byCode[c]; if (!mat) continue;
      // 无官方图则跳过（不使用任何占位/自定义几何）
      if (!getPhoto(mat.code)) continue;
      items.push(mat);
    }
    // 排序：官方规范顺序（分类优先级），同级保持用户原序
    let ordered = items.slice();
    if (opts.order === "official") {
      ordered.sort((a, b) => rolePriority(classify(a).kind) - rolePriority(classify(b).kind));
    }
    const tower = new THREE.Group();
    let y = 0;
    const GAP = 0.18;
    for (const mat of ordered) {
      const o = buildBillboard(mat, opts);
      o.obj.position.y = y + o.height / 2;
      tower.add(o.obj);
      y += o.height + GAP;
    }
    // 整体居中
    tower.position.y = -y / 2;
    group.add(tower);
    return { group, totalHeight: Math.max(y, 1.6), stackCount: ordered.length, ordered: ordered.map((m) => m.code) };
  }

  /* ----------------- 实时预览（带 OrbitControls） ----------------- */
  function makeBgTexture() {
    const c = document.createElement("canvas"); c.width = c.height = 512;
    const x = c.getContext("2d");
    const g = x.createLinearGradient(0, 0, 0, 512);
    g.addColorStop(0, "#fff3df"); g.addColorStop(0.55, "#ffe7c4"); g.addColorStop(1, "#f6c98a");
    x.fillStyle = g; x.fillRect(0, 0, 512, 512);
    const t = new THREE.CanvasTexture(c); t.encoding = THREE.sRGBEncoding; return t;
  }

  function createStudioPreview(container) {
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(global.devicePixelRatio || 1, 2));
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
    container.appendChild(renderer.domElement);
    renderer.domElement.style.width = "100%"; renderer.domElement.style.height = "100%";
    renderer.domElement.style.display = "block";

    const scene = new THREE.Scene();
    scene.background = makeBgTexture();
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 200);
    camera.position.set(0, 1, 9);

    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true; controls.dampingFactor = 0.08;
    controls.minDistance = 4; controls.maxDistance = 30;
    controls.maxPolarAngle = Math.PI * 0.95;
    controls.target.set(0, 0, 0);

    // 官方图为 MeshBasic(不受光)，灯光仅用于整体氛围/阴影承接
    scene.add(new THREE.HemisphereLight(0xffffff, 0x886644, 1.0));
    const key = new THREE.DirectionalLight(0xffffff, 0.7);
    key.position.set(5, 10, 7); scene.add(key);

    let current = null;
    function setLayers(codes, byCode, o) {
      if (current) { scene.remove(current.group); disposeGroup(current.group); }
      current = buildBurger(codes, byCode, o || {});
      scene.add(current.group);
      const h = current.totalHeight;
      controls.target.set(0, 0, 0);
      const need = h * 1.4 + 3.5;
      const cur = camera.position.length();
      if (cur > need * 1.7 || cur < need * 0.6) camera.position.set(0, h * 0.1, need);
    }
    function resetView() {
      const h = current ? current.totalHeight : 3;
      controls.target.set(0, 0, 0);
      camera.position.set(0, h * 0.1, h * 1.4 + 3.5);
    }
    function toggleRotate(on) { controls.autoRotate = on; controls.autoRotateSpeed = 1.4; }
    function updateBillboards() {
      if (!current) return;
      current.group.traverse((o) => {
        if (o.userData && o.userData.billboard) o.quaternion.copy(camera.quaternion);
      });
    }
    function onResize() {
      const w = container.clientWidth, hgt = container.clientHeight;
      if (w === 0 || hgt === 0) return;
      renderer.setSize(w, hgt, false);
      camera.aspect = w / hgt; camera.updateProjectionMatrix();
    }
    global.addEventListener("resize", onResize);
    setTimeout(onResize, 50);
    (function loop() {
      requestAnimationFrame(loop);
      controls.update();
      updateBillboards();
      renderer.render(scene, camera);
    })();
    return { renderer, scene, camera, controls, setLayers, resetView, toggleRotate, onResize, getState: () => current };
  }

  function disposeGroup(g) {
    g.traverse((o) => {
      if (o.geometry) o.geometry.dispose();
      if (o.material) {
        const ms = Array.isArray(o.material) ? o.material : [o.material];
        ms.forEach((m) => { if (m.map && m.map.__isCache) return; m.dispose(); });
      }
    });
  }

  global.Burger3D = {
    classify, buildBurger, createStudioPreview, setPhotoLoader, getPhoto,
    isWholeBurger, disposeGroup, rolePriority, PRIORITY,
  };
})(window);
