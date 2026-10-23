/* =========================================================================
 *  麦当劳「真」随心配 · 可分离汉堡组件 3D 模型库 (Components3D)  v3.0
 *  —— 高保真「食物几何」重建 + 程序化表面纹理（albedo + bump）：
 *     圆顶芝麻包胚（烘烤斑/面粉点）、带焦痕与交叉烤架纹的牛肉饼、
 *     裹粉鸡排/鱼排、融化芝士、褶皱生菜、带籽番茄、波浪培根、煎蛋……
 *     每个组件都是受光、有体积、带真实表面细节的实体 3D 模型。
 *
 *  依赖：three.min.js (r128)（global.THREE）
 * ========================================================================= */
(function (global) {
  "use strict";
  const THREE = global.THREE;

  // ---------- 程序化表面纹理（canvas：albedo + bump） ----------
  const Tex = (function () {
    const cache = {};
    function mk() { const c = document.createElement("canvas"); c.width = c.height = 256; return c; }
    function fill(ctx, col) { ctx.fillStyle = col; ctx.fillRect(0, 0, 256, 256); }
    function blots(ctx, s, col, n, r0, r1, a) {
      for (let i = 0; i < n; i++) {
        const x = Math.random() * s, y = Math.random() * s, r = r0 + Math.random() * (r1 - r0);
        const g = ctx.createRadialGradient(x, y, r * 0.15, x, y, r);
        g.addColorStop(0, col); g.addColorStop(1, "rgba(0,0,0,0)");
        ctx.fillStyle = g; ctx.globalAlpha = a; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
      }
      ctx.globalAlpha = 1;
    }
    function dots(ctx, s, col, n, r0, r1, a) {
      for (let i = 0; i < n; i++) {
        const x = Math.random() * s, y = Math.random() * s, r = r0 + Math.random() * (r1 - r0);
        ctx.fillStyle = col; ctx.globalAlpha = a; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
      }
      ctx.globalAlpha = 1;
    }
    function lines(ctx, s, col, w, n, wob) {
      ctx.strokeStyle = col; ctx.lineWidth = w; ctx.globalAlpha = 0.55;
      for (let i = 0; i < n; i++) {
        const y = Math.random() * s; ctx.beginPath(); ctx.moveTo(0, y);
        for (let x = 0; x <= s; x += 14) ctx.lineTo(x, y + Math.sin(x * 0.05 + i) * wob);
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
    }
    function make(kind) {
      if (cache[kind]) return cache[kind];
      const s = 256, mapC = mk(), bumpC = mk();
      const m = mapC.getContext("2d"), b = bumpC.getContext("2d");
      b.fillStyle = "#808080"; b.fillRect(0, 0, s, s);
      switch (kind) {
        case "bun":
          fill(m, "#f0bd74");
          blots(m, s, "rgba(176,116,54,0.28)", 22, 10, 30, 0.28);
          dots(m, s, "rgba(255,247,224,0.45)", 110, 0.8, 2, 0.45);
          blots(b, s, "rgba(95,95,95,0.3)", 22, 10, 30, 1);
          dots(b, s, "rgba(220,220,220,0.4)", 110, 0.8, 2, 1);
          break;
        case "beef":
          fill(m, "#6f3d24");
          blots(m, s, "rgba(42,20,9,0.38)", 24, 14, 38, 0.38);
          blots(m, s, "rgba(158,94,54,0.32)", 30, 8, 22, 0.32);
          lines(m, s, "rgba(32,15,7,0.4)", 3, 11, 4);
          blots(b, s, "rgba(60,60,60,0.35)", 24, 14, 38, 1);
          blots(b, s, "rgba(195,195,195,0.3)", 30, 8, 22, 1);
          lines(b, s, "rgba(55,55,55,0.5)", 3, 11, 4);
          break;
        case "chicken": case "fish": {
          const base = kind === "fish" ? "#d8c36a" : "#c8893b";
          fill(m, base);
          for (let i = 0; i < 720; i++) {
            const x = Math.random() * s, y = Math.random() * s, r = 1 + Math.random() * 2.6;
            m.fillStyle = Math.random() < 0.5 ? "rgba(120,70,20,0.5)" : "rgba(238,178,92,0.5)";
            m.beginPath(); m.arc(x, y, r, 0, Math.PI * 2); m.fill();
          }
          for (let i = 0; i < 720; i++) {
            const x = Math.random() * s, y = Math.random() * s, r = 1 + Math.random() * 2.6;
            const v = (90 + Math.random() * 120) | 0;
            b.fillStyle = "rgb(" + v + "," + v + "," + v + ")";
            b.beginPath(); b.arc(x, y, r, 0, Math.PI * 2); b.fill();
          }
          break;
        }
        case "cheese":
          fill(m, "#f6bb0a");
          blots(m, s, "rgba(228,172,0,0.32)", 18, 8, 18, 0.32);
          dots(m, s, "rgba(205,148,10,0.5)", 9, 3, 6, 0.5);
          blots(b, s, "rgba(125,125,125,0.3)", 16, 8, 16, 1);
          break;
        case "lettuce":
          fill(m, "#7cb342");
          for (let i = 0; i < 26; i++) {
            const a = (i / 26) * Math.PI * 2, cx = 128 + Math.cos(a) * 30, cy = 128 + Math.sin(a) * 30;
            b.strokeStyle = m.strokeStyle = i % 2 ? "rgba(60,110,30,0.4)" : "rgba(168,216,94,0.5)";
            b.lineWidth = m.lineWidth = 2.4;
            b.globalAlpha = m.globalAlpha = 0.5;
            b.beginPath(); b.moveTo(cx, cy);
            m.beginPath(); m.moveTo(cx, cy);
            for (let t = 0; t <= 1; t += 0.05) {
              const x = cx + Math.cos(a) * 110 * t, y = cy + Math.sin(a) * 110 * t;
              b.lineTo(x, y + Math.sin(t * 9 + i) * 6);
              m.lineTo(x, y + Math.sin(t * 9 + i) * 6);
            }
            b.stroke(); m.stroke();
            b.globalAlpha = m.globalAlpha = 1;
          }
          blots(m, s, "rgba(168,216,94,0.4)", 18, 8, 22, 0.4);
          break;
        case "tomato": {
          const g = m.createRadialGradient(128, 128, 8, 128, 128, 128);
          g.addColorStop(0, "#ec5a4b"); g.addColorStop(1, "#bf201b");
          m.fillStyle = g; m.fillRect(0, 0, s, s);
          dots(m, s, "rgba(255,210,200,0.25)", 60, 1, 2, 0.25);
          blots(b, s, "rgba(110,110,110,0.3)", 20, 10, 24, 1);
          break;
        }
        case "onion":
          fill(m, "#efe4d2");
          for (let i = 0; i < 5; i++) {
            m.strokeStyle = "rgba(190,170,140,0.5)"; m.lineWidth = 3;
            m.beginPath(); m.arc(128, 128, 20 + i * 22, 0, Math.PI * 2); m.stroke();
            b.strokeStyle = "rgba(150,150,150,0.5)"; b.lineWidth = 3;
            b.beginPath(); b.arc(128, 128, 20 + i * 22, 0, Math.PI * 2); b.stroke();
          }
          break;
        case "sauce":
          fill(m, "#e8c36b");
          blots(m, s, "rgba(212,171,74,0.5)", 26, 10, 26, 0.5);
          dots(m, s, "rgba(255,240,210,0.4)", 40, 1, 3, 0.4);
          blots(b, s, "rgba(120,120,120,0.3)", 20, 10, 22, 1);
          break;
        case "bacon":
          fill(m, "#9b4a2b");
          for (let k = 0; k < 4; k++) {
            const y = 40 + k * 60;
            m.fillStyle = "rgba(217,169,140,0.85)";
            m.beginPath();
            for (let x = 0; x <= s; x += 10) m.lineTo(x, y + Math.sin(x * 0.08 + k) * 10);
            m.lineTo(s, y + 18);
            for (let x = s; x >= 0; x -= 10) m.lineTo(x, y + 18 + Math.sin(x * 0.08 + k) * 10);
            m.closePath(); m.fill();
            b.fillStyle = "rgba(210,210,210,0.8)";
            b.beginPath();
            for (let x = 0; x <= s; x += 10) b.lineTo(x, y + Math.sin(x * 0.08 + k) * 10);
            b.lineTo(s, y + 18);
            for (let x = s; x >= 0; x -= 10) b.lineTo(x, y + 18 + Math.sin(x * 0.08 + k) * 10);
            b.closePath(); b.fill();
          }
          lines(m, s, "rgba(70,30,18,0.5)", 2, 6, 3);
          break;
        case "egg":
          fill(m, "#f7f2e7");
          blots(m, s, "rgba(233,221,198,0.5)", 30, 10, 26, 0.5);
          blots(b, s, "rgba(150,150,150,0.3)", 20, 10, 22, 1);
          break;
        case "grill":
          fill(m, "#c0814a");
          lines(m, s, "rgba(70,38,20,0.45)", 5, 9, 3);
          blots(m, s, "rgba(150,95,55,0.30)", 20, 8, 20, 0.30);
          blots(b, s, "rgba(110,110,110,0.30)", 16, 10, 22, 1);
          lines(b, s, "rgba(60,60,60,0.5)", 5, 9, 3);
          break;
        case "nugget":
          fill(m, "#d9a441");
          blots(m, s, "rgba(176,122,46,0.45)", 30, 6, 16, 0.45);
          blots(m, s, "rgba(232,192,106,0.40)", 26, 5, 13, 0.40);
          dots(m, s, "rgba(255,240,200,0.35)", 70, 0.6, 1.6, 0.35);
          blots(b, s, "rgba(120,120,120,0.30)", 30, 6, 16, 1);
          break;
        case "fries":
          fill(m, "#e3b35a");
          dots(m, s, "rgba(255,250,235,0.5)", 60, 0.6, 1.5, 0.5);
          blots(m, s, "rgba(200,150,70,0.4)", 24, 6, 14, 0.4);
          blots(b, s, "rgba(120,120,120,0.30)", 22, 6, 14, 1);
          break;
        case "pie":
          fill(m, "#d9a14a");
          blots(m, s, "rgba(198,150,70,0.4)", 22, 8, 18, 0.4);
          blots(m, s, "rgba(232,196,120,0.40)", 18, 6, 14, 0.40);
          blots(b, s, "rgba(120,120,120,0.30)", 20, 8, 18, 1);
          break;
        default:
          fill(m, "#cccccc");
      }
      const map = new THREE.CanvasTexture(mapC);
      if (THREE.sRGBEncoding) map.encoding = THREE.sRGBEncoding;
      map.wrapS = map.wrapT = THREE.RepeatWrapping;
      const bump = new THREE.CanvasTexture(bumpC);
      bump.wrapS = bump.wrapT = THREE.RepeatWrapping;
      cache[kind] = { map, bump };
      return cache[kind];
    }
    return { make };
  })();

  // 官方配色（取自 materials.json 颜色 + 真实形态调研）
  const C = {
    bunTop: 0xE3A857, bunBottom: 0xDFA24F, sesame: 0xF3E6C0,
    beef: 0x5E3320, beefSeared: 0x3A1E10, chicken: 0xC8893B, crumb: 0xB5782E,
    fish: 0xD8C36A, cheese: 0xF4B400, lettuce: 0x7CB342, lettuce2: 0x8BC34A,
    lettuce3: 0x689F38, tomato: 0xE53935, tomatoFlesh: 0xEF6B5A,
    onion: 0xEDE2D0, pickle: 0x6B8E23, pickleSkin: 0x4E6B18,
    sauce: 0xE8C36B, bacon: 0x9B4A2B, baconFat: 0xD9A98C,
    eggWhite: 0xF7F2E7, yolk: 0xF2B705,
    grilled: 0xC0814A, grillChar: 0x46261A, nugget: 0xD9A441, nuggetEdge: 0xB07A2E,
    cone: 0xC68A4A, vanilla: 0xFFF4E2, pie: 0xD9A14A, pieFilling: 0xE9C46A,
    shrimp: 0xF18C6B, shrimpStripe: 0xD9533C
  };

  function mat(color, opts) {
    opts = opts || {};
    // 使用纹理时基色设为白，让贴图呈现真实颜色；否则用 hex（sRGB→线性，避免"漂白"）
    const base = opts.map ? 0xffffff : color;
    const c = new THREE.Color(base).convertSRGBToLinear();
    return new THREE.MeshStandardMaterial({
      color: c, roughness: opts.rough != null ? opts.rough : 0.85,
      metalness: opts.metal != null ? opts.metal : 0.0,
      transparent: !!opts.transparent, opacity: opts.opacity != null ? opts.opacity : 1,
      side: THREE.DoubleSide, emissive: opts.emissive || 0x000000,
      emissiveIntensity: opts.emissiveIntensity || 0,
      map: opts.map || null,
      bumpMap: opts.bump || null,
      bumpScale: opts.bumpScale != null ? opts.bumpScale : 0.03
    });
  }

  // ---- 轻量噪声 ----
  function fbm(x, y) {
    return Math.sin(x * 1.7 + Math.cos(y * 1.3)) * 0.5
      + Math.sin(x * 3.1 + y * 2.7) * 0.25
      + Math.sin(y * 4.3 - x * 1.1) * 0.25;
  }
  function displace(geo, fn) {
    const p = geo.attributes.position, v = new THREE.Vector3();
    for (let i = 0; i < p.count; i++) {
      v.fromBufferAttribute(p, i);
      const d = fn(v.x, v.y, v.z);
      p.setXYZ(i, v.x + d[0], v.y + d[1], v.z + d[2]);
    }
    geo.computeVertexNormals();
    return geo;
  }

  const texOf = (k) => Tex.make(k);

  // ---- 各组件构造（高保真 + 表面纹理） ----
  const builders = {
    bunTop() {
      const g = new THREE.Group();
      const R = 1.05, h = 0.62;
      const domeG = new THREE.SphereGeometry(R, 72, 44, 0, Math.PI * 2, 0, Math.PI / 2);
      displace(domeG, (x, y, z) => {
        const n = fbm(x * 3.2, z * 3.2) * 0.03;
        return [0, n * (y / R), 0];
      });
      const t = texOf("bun");
      const dome = new THREE.Mesh(domeG, mat(0xffffff, { map: t.map, bump: t.bump, rough: 0.6, bumpScale: 0.025 }));
      dome.scale.set(1, h / R, 1);
      g.add(dome);
      // 收口脖颈
      const collar = new THREE.Mesh(
        new THREE.CylinderGeometry(R * 0.9, R * 0.82, 0.16, 48),
        mat(0xDEA052, { rough: 0.85 }));
      collar.position.y = -0.08; g.add(collar);
      // 芝麻（沿圆顶表面，朝外，略微随机朝向）
      const sm = mat(0xE8D9A8, { rough: 0.6 });
      const se = new THREE.SphereGeometry(0.03, 8, 6);
      let placed = 0;
      for (let i = 0; i < 340 && placed < 105; i++) {
        const th = Math.random() * Math.PI * 2;
        const ph = (0.12 + Math.random() * 0.84) * Math.PI / 2;
        const sx = Math.cos(th) * Math.sin(ph) * R;
        const sz = Math.sin(th) * Math.sin(ph) * R;
        const sy = Math.cos(ph) * h;
        if (sy < 0.05) continue;
        const s = new THREE.Mesh(se, sm);
        s.position.set(sx, sy, sz);
        s.scale.set(1.7, 0.6, 1.0);
        const nrm = new THREE.Vector3(sx, sy / h, sz).normalize();
        s.lookAt(s.position.clone().add(nrm));
        s.rotateZ(Math.random() * Math.PI);
        g.add(s); placed++;
      }
      return g;
    },
    bunBottom() {
      const g = new THREE.Group();
      const R = 1.0, h = 0.3;
      const geo = new THREE.CylinderGeometry(R, R * 0.95, h, 56, 2);
      displace(geo, (x, y, z) => {
        const r = Math.sqrt(x * x + z * z);
        if (y > 0) {
          const dip = -0.05 * Math.pow(Math.max(0, r / R), 2);
          return [0, dip + fbm(x * 3, z * 3) * 0.02, 0];
        }
        return [0, fbm(x * 4, y * 4) * 0.008, 0];
      });
      const t = texOf("bun");
      g.add(new THREE.Mesh(geo, mat(0xffffff, { map: t.map, bump: t.bump, rough: 0.82, bumpScale: 0.02 })));
      return g;
    },
    beef() {
      const g = new THREE.Group();
      const R = 1.0, h = 0.28;
      const geo = new THREE.CylinderGeometry(R, R, h, 72, 3);
      displace(geo, (x, y, z) => {
        const a = Math.atan2(z, x), r = Math.sqrt(x * x + z * z);
        const jag = (Math.sin(a * 9) * 0.02 + Math.sin(a * 23 + 1.7) * 0.011) * (r / R);
        if (y > 0) return [Math.cos(a) * jag, fbm(x * 5, z * 5) * 0.03, Math.sin(a) * jag];
        if (y < 0) return [Math.cos(a) * jag * 0.6, fbm(x * 4 + 9, z * 4) * 0.02, Math.sin(a) * jag * 0.6];
        return [Math.cos(a) * jag, 0, Math.sin(a) * jag];
      });
      const t = texOf("beef");
      g.add(new THREE.Mesh(geo, mat(0xffffff, { map: t.map, bump: t.bump, rough: 0.95, bumpScale: 0.04 })));
      return g;
    },
    chicken() {
      const g = new THREE.Group();
      const R = 1.0, h = 0.28;
      const geo = new THREE.CylinderGeometry(R, R, h, 56, 3);
      displace(geo, (x, y, z) => {
        const r = Math.sqrt(x * x + z * z);
        if (y > 0) return [0, fbm(x * 6, z * 6) * 0.025, 0];
        if (y < 0) return [0, fbm(x * 5 + 3, z * 5) * 0.02, 0];
        return [Math.sin(Math.atan2(z, x) * 16) * 0.015 * (r / R), 0, 0];
      });
      const t = texOf("chicken");
      g.add(new THREE.Mesh(geo, mat(0xffffff, { map: t.map, bump: t.bump, rough: 0.9, bumpScale: 0.05 })));
      return g;
    },
    fish() {
      const g = new THREE.Group();
      const w = 2.0, d = 1.3, h = 0.26;
      const geo = new THREE.BoxGeometry(w, h, d, 40, 2, 26);
      displace(geo, (x, y, z) => {
        const ex = Math.max(0, Math.abs(x) - (w / 2 - 0.12)) / 0.12;
        const ez = Math.max(0, Math.abs(z) - (d / 2 - 0.12)) / 0.12;
        const fall = 1 - Math.min(1, Math.max(ex, ez));
        if (y > 0) return [0, fbm(x * 5, z * 5) * 0.02 * fall, 0];
        return [0, 0, 0];
      });
      const t = texOf("fish");
      g.add(new THREE.Mesh(geo, mat(0xffffff, { map: t.map, bump: t.bump, rough: 0.9, bumpScale: 0.05 })));
      return g;
    },
    cheese() {
      const g = new THREE.Group();
      const s = 1.5, h = 0.05;
      const t = texOf("cheese");
      const slab = new THREE.Mesh(new THREE.BoxGeometry(s, h, s, 28, 1, 28),
        mat(0xffffff, { map: t.map, bump: t.bump, rough: 0.5, bumpScale: 0.02 }));
      slab.rotation.y = Math.PI / 4; slab.position.y = h / 2;
      displace(slab.geometry, (x, y, z) => { if (y > 0) return [0, fbm(x * 4 + z, z * 4) * 0.012, 0]; return [0, 0, 0]; });
      g.add(slab);
      // 四角 + 边中点下垂融化
      const drip = mat(C.cheese, { rough: 0.5 });
      const pts = [[s / 2, s / 2], [s / 2, -s / 2], [-s / 2, s / 2], [-s / 2, -s / 2],
        [s / 2, 0], [-s / 2, 0], [0, s / 2], [0, -s / 2]];
      pts.forEach(([x, z]) => {
        const dr = new THREE.Mesh(new THREE.ConeGeometry(0.1, 0.34, 10), drip);
        dr.position.set(x, -0.14, z); dr.rotation.x = Math.PI; g.add(dr);
      });
      return g;
    },
    // 真实生菜：水平铺展、边缘波浪褶皱、多层交叠的叶丛（非立着的环形）
    lettuce() {
      const g = new THREE.Group();
      const t = texOf("lettuce");
      // 单层褶皱叶盘：环形几何平躺于 XZ 面，外缘沿 Y 起伏形成荷叶边
      function ruffle(R, col, phase, amp, yRot) {
        const geo = new THREE.RingGeometry(R * 0.42, R, 120, 8);
        geo.rotateX(-Math.PI / 2);                 // 平躺（水平）
        const p = geo.attributes.position, v = new THREE.Vector3();
        for (let i = 0; i < p.count; i++) {
          v.fromBufferAttribute(p, i);
          const r = Math.sqrt(v.x * v.x + v.z * v.z);
          const ang = Math.atan2(v.z, v.x);
          const edge = Math.max(0, (r - R * 0.42) / (R * 0.58));   // 0 内 → 1 外缘
          const wave = Math.sin(ang * 20 + phase) * 0.07 + Math.sin(ang * 7 + phase * 2) * 0.045;
          const lift = wave * edge * amp + fbm(v.x * 5, v.z * 5) * 0.02 * edge;
          p.setY(i, lift);
        }
        geo.computeVertexNormals();
        const me = mat(col, { rough: 0.82, bump: t.bump, bumpScale: 0.05 });
        const m = new THREE.Mesh(geo, me);
        m.rotation.y = yRot;
        return m;
      }
      const layers = [
        { R: 1.28, col: C.lettuce3, phase: 0.0, amp: 1.0, y: 0.00, rot: 0.0 },
        { R: 1.14, col: C.lettuce, phase: 2.1, amp: 1.15, y: 0.05, rot: 0.4 },
        { R: 0.96, col: C.lettuce2, phase: 4.0, amp: 1.3, y: 0.10, rot: 1.1 }
      ];
      layers.forEach(L => {
        const d = ruffle(L.R, L.col, L.phase, L.amp, L.rot);
        d.position.y = L.y; g.add(d);
      });
      // 几片翘起的卷曲叶尖，增加体积与真实松散感
      const tipMat = mat(C.lettuce, { rough: 0.8, bump: t.bump, bumpScale: 0.04 });
      for (let i = 0; i < 6; i++) {
        const a = Math.random() * Math.PI * 2;
        const rr = 0.7 + Math.random() * 0.45;
        const tip = new THREE.Mesh(new THREE.SphereGeometry(0.22, 14, 10), tipMat);
        tip.scale.set(1.1, 0.45, 0.7);
        tip.position.set(Math.cos(a) * rr, 0.12 + Math.random() * 0.1, Math.sin(a) * rr);
        tip.lookAt(tip.position.clone().add(new THREE.Vector3(Math.cos(a), 0.6, Math.sin(a))));
        tip.rotateX(-0.5);
        g.add(tip);
      }
      return g;
    },
    tomato() {
      const g = new THREE.Group();
      const R = 0.95, h = 0.1;
      const t = texOf("tomato");
      const geo = new THREE.CylinderGeometry(R, R * 0.98, h, 48, 2);
      displace(geo, (x, y, z) => {
        const r = Math.sqrt(x * x + z * z);
        if (y > 0) return [0, fbm(x * 7, z * 7) * 0.015, 0];
        if (y < 0) return [0, fbm(x * 6 + 2, z * 6) * 0.01, 0];
        return [Math.sin(Math.atan2(z, x) * 18) * 0.01 * (r / R), 0, 0];
      });
      g.add(new THREE.Mesh(geo, mat(0xffffff, { map: t.map, bump: t.bump, rough: 0.5, bumpScale: 0.02 })));
      const flesh = new THREE.Mesh(new THREE.CircleGeometry(R * 0.72, 40), mat(C.tomatoFlesh, { rough: 0.35 }));
      flesh.rotation.x = -Math.PI / 2; flesh.position.y = h / 2 + 0.002; g.add(flesh);
      const seedMat = mat(0xF0E68C, { rough: 0.4 });
      for (let i = 0; i < 16; i++) {
        const a = i / 16 * Math.PI * 2 + Math.random() * 0.2;
        const rr = R * (0.34 + Math.random() * 0.18);
        const sd = new THREE.Mesh(new THREE.SphereGeometry(0.026, 6, 5), seedMat);
        sd.scale.set(1, 0.45, 1.7);
        sd.position.set(Math.cos(a) * rr, h / 2 + 0.012, Math.sin(a) * rr);
        sd.rotation.y = a; g.add(sd);
      }
      return g;
    },
    onion() {
      const g = new THREE.Group();
      const t = texOf("onion");
      const m = mat(0xffffff, { map: t.map, bump: t.bump, rough: 0.8, transparent: true, opacity: 0.92, bumpScale: 0.02 });
      [0.8, 0.62].forEach((R, i) => {
        const t2 = new THREE.Mesh(new THREE.TorusGeometry(R, 0.1, 14, 48), m);
        t2.rotation.x = Math.PI / 2; t2.position.y = 0.1 - i * 0.02; g.add(t2);
      });
      return g;
    },
    pickle() {
      const g = new THREE.Group();
      const R = 0.24, h = 0.05;
      const body = mat(C.pickle, { rough: 0.8 });
      const skin = mat(C.pickleSkin, { rough: 0.85 });
      for (let i = 0; i < 5; i++) {
        const b = new THREE.Mesh(new THREE.CylinderGeometry(R, R, h, 20), body);
        b.position.set((Math.random() - 0.5) * 1.3, h / 2, (Math.random() - 0.5) * 1.3);
        g.add(b);
        const sk = new THREE.Mesh(new THREE.CylinderGeometry(R * 1.02, R * 1.02, h * 1.02, 20), skin);
        sk.position.copy(b.position); sk.scale.set(1.04, 1.0, 1.04); g.add(sk);
      }
      return g;
    },
    sauce() {
      const g = new THREE.Group();
      const R = 1.0, h = 0.05;
      const t = texOf("sauce");
      const geo = new THREE.CylinderGeometry(R, R, h, 48, 2);
      displace(geo, (x, y, z) => {
        const r = Math.sqrt(x * x + z * z);
        if (y > 0) return [0, fbm(x * 9, z * 9) * 0.02, 0];
        return [Math.sin(Math.atan2(z, x) * 10) * 0.02 * (r / R), 0, 0];
      });
      g.add(new THREE.Mesh(geo, mat(0xffffff, { map: t.map, bump: t.bump, rough: 0.28, transparent: true, opacity: 0.92, bumpScale: 0.02 })));
      return g;
    },
    bacon() {
      const g = new THREE.Group();
      const w = 1.8, d = 0.55, h = 0.06;
      const geo = new THREE.BoxGeometry(w, h, d, 48, 1, 10);
      displace(geo, (x) => [0, Math.sin(x * 3.4) * 0.11, 0]);
      const t = texOf("bacon");
      g.add(new THREE.Mesh(geo, mat(0xffffff, { map: t.map, bump: t.bump, rough: 0.8, bumpScale: 0.05 })));
      return g;
    },
    egg() {
      const g = new THREE.Group();
      const R = 0.95, h = 0.08;
      const t = texOf("egg");
      const geo = new THREE.CylinderGeometry(R, R * 0.96, h, 48, 2);
      displace(geo, (x, y, z) => {
        const r = Math.sqrt(x * x + z * z);
        const wob = Math.sin(Math.atan2(z, x) * 7) * 0.06 + fbm(x * 5, z * 5) * 0.03;
        if (r > R - 0.18) return [Math.cos(Math.atan2(z, x)) * wob, 0, Math.sin(Math.atan2(z, x)) * wob];
        if (y > 0) return [0, fbm(x * 6, z * 6) * 0.012, 0];
        return [0, 0, 0];
      });
      g.add(new THREE.Mesh(geo, mat(0xffffff, { map: t.map, bump: t.bump, rough: 0.7, bumpScale: 0.02 })));
      const yolk = new THREE.Mesh(new THREE.SphereGeometry(0.32, 28, 20, 0, Math.PI * 2, 0, Math.PI / 2),
        mat(C.yolk, { rough: 0.4, metal: 0.05 }));
      yolk.position.y = h / 2; g.add(yolk);
      return g;
    },
    // 板烧鸡腿排：椭圆、轻烤褐色、带焦痕条纹（区别于炸鸡/牛肉）
    grilled() {
      const g = new THREE.Group();
      const R = 1.05, h = 0.24;
      const geo = new THREE.CylinderGeometry(R, R * 0.9, h, 64, 3);
      displace(geo, (x, y, z) => {
        const a = Math.atan2(z, x), r = Math.sqrt(x * x + z * z);
        const jag = (Math.sin(a * 7) * 0.018 + Math.sin(a * 19 + 0.6) * 0.01) * (r / R);
        if (y > 0) return [Math.cos(a) * jag, fbm(x * 5, z * 5) * 0.025, Math.sin(a) * jag];
        if (y < 0) return [Math.cos(a) * jag * 0.6, fbm(x * 4 + 9, z * 4) * 0.018, Math.sin(a) * jag * 0.6];
        return [Math.cos(a) * jag, 0, Math.sin(a) * jag];
      });
      const t = texOf("grill");
      const m = new THREE.Mesh(geo, mat(0xffffff, { map: t.map, bump: t.bump, rough: 0.85, bumpScale: 0.035 }));
      m.scale.x = 1.18;                       // 椭圆（鸡腿排）
      g.add(m);
      return g;
    },
    // 麦乐鸡：多颗裹粉金黄鸡块簇拥
    nuggets() {
      const g = new THREE.Group();
      const t = texOf("nugget");
      const spots = [
        [0, 0, 0, 1], [-0.34, 0.06, 0.22, 0.82], [0.32, 0.03, -0.16, 0.86],
        [0.12, 0.13, 0.30, 0.7], [-0.22, 0.11, -0.26, 0.76], [0.06, 0.05, 0.02, 0.92],
        [0.0, -0.04, 0.18, 0.7]
      ];
      spots.forEach(([x, y, z, sc]) => {
        const geo = new THREE.SphereGeometry(0.3, 22, 16);
        const p = geo.attributes.position, vv = new THREE.Vector3();
        for (let i = 0; i < p.count; i++) {
          vv.fromBufferAttribute(p, i);
          const r = vv.length();
          const bump = fbm(vv.x * 11 + 3, vv.y * 11) * 0.05 + Math.sin(vv.x * 16) * 0.012;
          p.setXYZ(i, vv.x + vv.x / r * bump, vv.y + vv.y / r * bump, vv.z + vv.z / r * bump);
        }
        geo.computeVertexNormals();
        const msh = new THREE.Mesh(geo, mat(0xffffff, { map: t.map, bump: t.bump, rough: 0.78, bumpScale: 0.05 }));
        msh.position.set(x, y, z);
        msh.scale.setScalar(sc);
        msh.rotation.set(Math.random() * 6, Math.random() * 6, Math.random() * 6);
        g.add(msh);
      });
      return g;
    },
    // 薯条：无包装，数根金黄薯条平放于台面（自然散落、轻微交叠与随机朝向）
    fries() {
      const g = new THREE.Group();
      const t = texOf("fries");
      const fryMat = mat(0xffffff, { map: t.map, bump: t.bump, rough: 0.7, bumpScale: 0.03 });
      const endMat = mat(0xC99044, { rough: 0.75 });          // 切口端面略深
      for (let i = 0; i < 8; i++) {
        const L = 0.85 + Math.random() * 0.4;                  // 单根长度
        const fr = new THREE.Mesh(new THREE.BoxGeometry(L, 0.075, 0.075), fryMat);
        // 端部做轻微收口，避免纯长方体的生硬感
        displace(fr.geometry, (x, y, z) => {
          const k = Math.abs(x) / (L / 2);
          if (k > 0.82) return [0, y * 0.85, z * 0.85];
          return [0, 0, 0];
        });
        const a = Math.random() * Math.PI * 2;
        const rr = Math.random() * 0.42;
        fr.position.set(Math.cos(a) * rr, 0.038, Math.sin(a) * rr);
        fr.rotation.y = a + (Math.random() - 0.5) * 1.3;
        fr.rotation.z = (Math.random() - 0.5) * 0.1;
        fr.rotation.x = (Math.random() - 0.5) * 0.1;
        g.add(fr);
        // 两小段"断薯条"碎块，增加散落真实感
        if (i % 3 === 0) {
          const bit = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.07, 0.07), endMat);
          bit.position.set(Math.cos(a + 1.1) * (rr + 0.35), 0.035, Math.sin(a + 1.1) * (rr + 0.35));
          bit.rotation.y = Math.random() * Math.PI;
          g.add(bit);
        }
      }
      return g;
    },
    // 圆筒冰淇淋：蛋筒 + 香草冰淇淋球漩涡
    icecream() {
      const g = new THREE.Group();
      const cone = new THREE.Mesh(new THREE.ConeGeometry(0.42, 0.8, 24, 1, true), mat(C.cone, { rough: 0.85 }));
      cone.rotation.x = Math.PI; cone.position.y = 0.4;          // 尖朝下，底在 0.8
      const vMat = mat(C.vanilla, { rough: 0.5 });
      const s1 = new THREE.Mesh(new THREE.SphereGeometry(0.38, 24, 18), vMat); s1.position.y = 0.86; s1.scale.set(1, 0.95, 1);
      const s2 = new THREE.Mesh(new THREE.SphereGeometry(0.30, 22, 16), vMat); s2.position.set(0, 1.08, 0); s2.scale.set(1, 1.05, 1);
      const s3 = new THREE.Mesh(new THREE.SphereGeometry(0.19, 18, 14), vMat); s3.position.set(0.05, 1.26, 0.02);
      g.add(cone, s1, s2, s3);
      return g;
    },
    // 派：酥皮金黄体 + 扇贝花边 + 馅料弧
    pie() {
      const g = new THREE.Group();
      const t = texOf("pie");
      const base = new THREE.Mesh(new THREE.CylinderGeometry(0.78, 0.78, 0.26, 36, 1),
        mat(0xffffff, { map: t.map, bump: t.bump, rough: 0.7, bumpScale: 0.04 }));
      base.position.y = 0.13; g.add(base);
      const edge = mat(C.pie, { rough: 0.7 });
      for (let i = 0; i < 22; i++) {
        const a = i / 22 * Math.PI * 2;
        const b = new THREE.Mesh(new THREE.SphereGeometry(0.07, 10, 8), edge);
        b.position.set(Math.cos(a) * 0.78, 0.26, Math.sin(a) * 0.78);
        g.add(b);
      }
      const fillMesh = new THREE.Mesh(new THREE.TorusGeometry(0.3, 0.06, 8, 24, Math.PI),
        mat(C.pieFilling, { rough: 0.6, transparent: true, opacity: 0.85 }));
      fillMesh.rotation.x = Math.PI / 2; fillMesh.position.y = 0.27; g.add(fillMesh);
      return g;
    },
    // 虾仁：粉橙色卷曲虾身 + 虾尾 + 熟虾红纹（三文鱼双虾堡用）
    shrimp() {
      const g = new THREE.Group();
      const body = mat(C.shrimp, { rough: 0.55 });
      const stripe = mat(C.shrimpStripe, { rough: 0.5 });
      const n = 4;
      for (let i = 0; i < n; i++) {
        const a = i / n * Math.PI * 2 + 0.4;
        const R = 0.38 + Math.random() * 0.06;
        const sh = new THREE.Group();
        // 卷曲虾身：3/4 圆弧环平躺
        const tor = new THREE.Mesh(new THREE.TorusGeometry(0.2, 0.08, 12, 24, Math.PI * 1.5), body);
        tor.rotation.x = Math.PI / 2;
        sh.add(tor);
        // 虾尾：小圆锥向外翘起
        const tail = new THREE.Mesh(new THREE.ConeGeometry(0.07, 0.16, 10), body);
        tail.position.set(0.22, 0.02, 0);
        tail.rotation.z = -Math.PI / 2.4;
        sh.add(tail);
        // 熟虾红纹
        const st = new THREE.Mesh(new THREE.TorusGeometry(0.2, 0.028, 8, 20, Math.PI * 1.4), stripe);
        st.rotation.x = Math.PI / 2; st.position.y = 0.04;
        sh.add(st);
        sh.position.set(Math.cos(a) * R, 0.085, Math.sin(a) * R);
        sh.rotation.y = a + (Math.random() - 0.5) * 0.5;
        g.add(sh);
      }
      return g;
    }
  };

  // 组件目录（供 UI 货架使用）
  const CATALOG = [
    { kind: "bunTop", label: "面包胚(上·带芝麻)", height: 0.78 },
    { kind: "bunBottom", label: "面包胚(下)", height: 0.3 },
    { kind: "beef", label: "牛肉饼", height: 0.3 },
    { kind: "chicken", label: "鸡排", height: 0.3 },
    { kind: "fish", label: "鱼排", height: 0.26 },
    { kind: "cheese", label: "芝士片", height: 0.22 },
    { kind: "lettuce", label: "生菜", height: 0.3 },
    { kind: "tomato", label: "番茄片", height: 0.16 },
    { kind: "onion", label: "洋葱圈", height: 0.14 },
    { kind: "pickle", label: "酸黄瓜", height: 0.08 },
    { kind: "sauce", label: "酱料", height: 0.06 },
    { kind: "bacon", label: "培根", height: 0.2 },
    { kind: "egg", label: "煎蛋", height: 0.34 },
    { kind: "grilled", label: "板烧鸡腿排", height: 0.26 },
    { kind: "nuggets", label: "麦乐鸡", height: 0.5 },
    { kind: "fries", label: "薯条(平放)", height: 0.12 },
    { kind: "icecream", label: "圆筒冰淇淋", height: 1.3 },
    { kind: "pie", label: "派", height: 0.34 },
    { kind: "shrimp", label: "虾仁", height: 0.22 }
  ];

  // 每层组件的营养/价格参考值（估自真实食材分量，用于"预计"展示）
  const NUTRITION = {
    bunTop: { price: 1.5, energyKcal: 120, protein: 4, fat: 2, carbohydrate: 22 },
    bunBottom: { price: 1.2, energyKcal: 110, protein: 4, fat: 2, carbohydrate: 20 },
    beef: { price: 3.6, energyKcal: 130, protein: 11, fat: 11, carbohydrate: 1 },
    chicken: { price: 3.6, energyKcal: 220, protein: 17, fat: 13, carbohydrate: 11 },
    fish: { price: 4.0, energyKcal: 180, protein: 12, fat: 9, carbohydrate: 14 },
    cheese: { price: 1.0, energyKcal: 50, protein: 3, fat: 4, carbohydrate: 1 },
    lettuce: { price: 0.3, energyKcal: 5, protein: 0.3, fat: 0, carbohydrate: 1 },
    tomato: { price: 0.3, energyKcal: 8, protein: 0.4, fat: 0, carbohydrate: 2 },
    onion: { price: 0.2, energyKcal: 6, protein: 0.2, fat: 0, carbohydrate: 1.5 },
    pickle: { price: 0.2, energyKcal: 3, protein: 0, fat: 0, carbohydrate: 1 },
    sauce: { price: 0.2, energyKcal: 40, protein: 0, fat: 4, carbohydrate: 2 },
    bacon: { price: 1.5, energyKcal: 90, protein: 7, fat: 7, carbohydrate: 0 },
    egg: { price: 1.0, energyKcal: 90, protein: 7, fat: 7, carbohydrate: 1 },
    grilled: { price: 5.0, energyKcal: 180, protein: 18, fat: 9, carbohydrate: 4 },
    nuggets: { price: 14.0, energyKcal: 190, protein: 11, fat: 10, carbohydrate: 11 },
    fries: { price: 13.5, energyKcal: 320, protein: 4, fat: 15, carbohydrate: 41 },
    icecream: { price: 5.0, energyKcal: 150, protein: 3, fat: 4, carbohydrate: 25 },
    pie: { price: 8.5, energyKcal: 260, protein: 3, fat: 11, carbohydrate: 39 },
    shrimp: { price: 3.0, energyKcal: 55, protein: 10, fat: 0.6, carbohydrate: 0.5 }
  };

  // 官方规范排序优先级（与 official_composition.json 对齐）
  const PRIORITY = {
    bunBottom: 1, beef: 2, chicken: 2, fish: 2, cheese: 3, bacon: 4,
    egg: 5, lettuce: 6, tomato: 6, onion: 6,     pickle: 6, sauce: 7, bunTop: 8, grilled: 2, nuggets: 4, fries: 5, pie: 6, icecream: 8, shrimp: 2
  };

  function buildComponent(kind, opts) {
    const b = builders[kind];
    if (!b) throw new Error("未知组件:" + kind);
    const g = b(opts);
    const meta = CATALOG.find(c => c.kind === kind) || { height: 0.2 };
    g.userData = { isComponent: true, kind, label: meta.label, height: meta.height };
    return g;
  }

  function stackComponents(items, opts) {
    opts = opts || {};
    const gap = opts.gap != null ? opts.gap : 0.015;
    const ordered = opts.officialOrder !== false
      ? items.slice().sort((a, b) => (PRIORITY[a.kind] || 9) - (PRIORITY[b.kind] || 9))
      : items;
    const root = new THREE.Group();
    let y = 0;
    ordered.forEach(it => {
      const c = buildComponent(it.kind, it.opts);
      c.position.y = y;
      root.add(c);
      y += (c.userData.height || 0.2) + gap;
    });
    root.userData = { isComponentStack: true, count: ordered.length, height: y };
    return root;
  }

  global.Components3D = { buildComponent, stackComponents, CATALOG, PRIORITY, NUTRITION, builders, COLORS: C, Tex };
  if (typeof module !== "undefined" && module.exports) module.exports = global.Components3D;
})(typeof window !== "undefined" ? window : globalThis);
