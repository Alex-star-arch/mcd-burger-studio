/* =========================================================================
 *  麦当劳「真」随心配 · 官方图片转 3D 模型 (Photo3D)  v1.0
 *
 *  设计目标
 *    「小吃/饮品不用手写程序化几何，而是直接把官方产品图转成 3D 模型」。
 *    官方图是透明底的产品抠图（assets/mcd_photos_clean/），本身就带有真实的
 *    品牌配色、印刷文字、冰块/气泡/杯盖等细节——用它做 3D 化，比任何自建
 *    几何都更贴近实物。
 *
 *  原理（纯几何图像重建，无需云端/模型权重）
 *    1. 取官方图 RGBA，按 alpha 轮廓栅格化为 GX×GY 网格（含 3x3 众数滤波去毛刺）；
 *    2. 用「到轮廓的距离场」生成高度场：内部恒定厚度 + 近边缘平滑倒角，
 *       天然形成水密闭合实体（顶面 + 底面 + 侧壁），不存在单层壳的镂空；
 *    3. 顶/底面 UV 直接沿用官方图坐标 → 正面即官方原图，文字方向正确；
 *       侧壁 UV 取样该格中心色 → 侧面颜色与轮廓边缘自然衔接，不会透明穿空；
 *    4. **弧面整形**：沿宽度方向按 sqrt(1-u²) 把正面向外鼓出，
 *       让平面切片呈现杯/罐的圆柱体积感（侧向轮廓仍严格等于官方图）；
 *    5. 统一旋转为「竖直站立、正面朝相机」，再由调用方落地对齐展示台。
 *
 *  依赖：three.min.js (r128)（global.THREE）
 * ========================================================================= */
(function (global) {
  "use strict";
  const THREE = global.THREE;

  // 每款单品的成像参数：
  //   bulge  弧面鼓出量（世界单位，长边=2.2 归一下）
  //   depth  恒定厚度（倒角最小厚度）
  //   bevel  边缘倒角宽度（格）
  //   grid   长边栅格分辨率
  //   rough/metal 材质
  // 成像参数：
  //   segments  圆周分段（越大越圆滑）
  //   rows      高度方向采样行数
  //   rough/metal 材质
  //   emissive/diffuse 贴图与受光配比（官方图自带烘焙光照，以自发光为主）
  const SPEC = {
    "3010":      { segments: 112, rows: 200, rough: 0.62, metal: 0.00 }, // 雪碧（玻璃杯）
    "515520":    { segments: 112, rows: 200, rough: 0.62, metal: 0.00 }, // 怡泉 +C（玻璃杯）
    "4437":      { segments: 120, rows: 200, rough: 0.66, metal: 0.00 }, // 玉米杯（透明杯）
    "515837":    { segments: 112, rows: 210, rough: 0.70, metal: 0.00 }, // 圆筒冰淇淋
    "9900008751":{ segments: 120, rows: 210, rough: 0.58, metal: 0.00 }, // 可乐（杯装）
    "520689":    { segments: 120, rows: 190, rough: 0.66, metal: 0.00 }  // 麦咖啡（纸杯）
  };

  const CODES = Object.keys(SPEC);

  // ---------- 3x3 众数滤波：剔除轮廓毛刺与孤立格 ----------
  function denoise(solid, GX, GY) {
    const out = new Uint8Array(solid);
    for (let y = 0; y < GY; y++) {
      for (let x = 0; x < GX; x++) {
        const i = y * GX + x;
        let n = 0;
        for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            const yy = y + dy, xx = x + dx;
            if (yy < 0 || xx < 0 || yy >= GY || xx >= GX) { n += solid[i] ? 1 : 0; continue; }
            n += solid[yy * GX + xx] ? 1 : 0;
          }
        }
        if (solid[i] && n <= 2) out[i] = 0;        // 孤立实心格 → 挖掉
        else if (!solid[i] && n >= 8) out[i] = 1;  // 被包围的空心格 → 补上
      }
    }
    return out;
  }

  // ---------- alpha 轮廓 → 栅格实心掩码 + 每格代表色 ----------
  function rasterize(data, W, H, GX, GY) {
    const solid = new Uint8Array(GX * GY);
    const colR = new Float32Array(GX * GY);
    const colG = new Float32Array(GX * GY);
    const colB = new Float32Array(GX * GY);
    const hit = new Float32Array(GX * GY);
    for (let y = 0; y < H; y++) {
      const gy = Math.min(GY - 1, (y / H * GY) | 0);
      for (let x = 0; x < W; x++) {
        const i = y * W + x;
        if (data[i * 4 + 3] < 96) continue;
        const gx = Math.min(GX - 1, (x / W * GX) | 0);
        const k = gy * GX + gx;
        if (solid[k] !== 1) { solid[k] = 1; }
        colR[k] += data[i * 4]; colG[k] += data[i * 4 + 1]; colB[k] += data[i * 4 + 2];
        hit[k] += 1;
      }
    }
    for (let k = 0; k < GX * GY; k++) {
      if (hit[k] > 0) { colR[k] /= hit[k]; colG[k] /= hit[k]; colB[k] /= hit[k]; }
    }
    const clean = denoise(solid, GX, GY);
    // 众数滤波后若某格被补上但无像素，用邻格均值兜底
    for (let k = 0; k < GX * GY; k++) {
      if (clean[k] && hit[k] === 0) {
        let r = 0, g = 0, b = 0, n = 0;
        for (let d = -1; d <= 1; d++) {
          const kk = k + d;
          if (kk < 0 || kk >= GX * GY || !hit[kk]) continue;
          r += colR[kk]; g += colG[kk]; b += colB[kk]; n++;
        }
        if (n) { colR[k] = r / n; colG[k] = g / n; colB[k] = b / n; }
        else { colR[k] = 235; colG[k] = 235; colB[k] = 235; }
      }
    }
    return { solid: clean, colR, colG, colB, GX, GY };
  }

  // ---------- 到轮廓的距离场（多遍扫描，格为单位的近似距离） ----------
  function distField(solid, GX, GY) {
    const d = new Int16Array(GX * GY);
    const BIG = 1 << 12;
    for (let y = 0; y < GY; y++) {
      for (let x = 0; x < GX; x++) {
        const i = y * GX + x;
        if (!solid[i]) { d[i] = 0; continue; }
        const edge = x === 0 || y === 0 || x === GX - 1 || y === GY - 1 ||
          !solid[i - 1] || !solid[i + 1] || !solid[i - GX] || !solid[i + GX];
        d[i] = edge ? 1 : BIG;
      }
    }
    for (let it = 0; it < Math.max(GX, GY); it++) {
      let changed = false;
      for (let y = 0; y < GY; y++) {
        for (let x = 0; x < GX; x++) {
          const i = y * GX + x;
          if (!solid[i]) continue;
          let m = d[i];
          if (x > 0 && d[i - 1] + 1 < m) m = d[i - 1] + 1;
          if (x < GX - 1 && d[i + 1] + 1 < m) m = d[i + 1] + 1;
          if (y > 0 && d[i - GX] + 1 < m) m = d[i - GX] + 1;
          if (y < GY - 1 && d[i + GX] + 1 < m) m = d[i + GX] + 1;
          if (m !== d[i]) { d[i] = m; changed = true; }
        }
      }
      if (!changed) break;
    }
    return d;
  }

  /**
   * 官方图 RGBA → 3D 实体几何
   * 坐标系：图像 x→X、图像 y→-Z、厚度→+Y（即「平放」，由调用方旋转成站立）
   */
  function buildGeometry(data, W, H, opt) {
    const grid = opt.grid || 150;
    const longSide = Math.max(W, H);
    const GX = W >= H ? grid : Math.max(8, Math.round(grid * W / H));
    const GY = H > W ? grid : Math.max(8, Math.round(grid * H / W));

    const r = rasterize(data, W, H, GX, GY);
    const dist = distField(r.solid, GX, GY);

    const bevel = Math.max(2, opt.bevel || 7);
    const depth = opt.depth || 0.06;
    const scale = 2.2 / longSide;            // 长边归一到 2.2
    const cw = (W / GX) * scale, ch = (H / GY) * scale;
    const ox = -W * scale / 2, oz = H * scale / 2;
    const hw = W * scale / 2;                // 半宽（用于弧面整形）

    const pos = [], uv = [], col = [];
    const idxOf = (x, y) => y * GX + x;
    const solidAt = (x, y) => (x < 0 || y < 0 || x >= GX || y >= GY) ? 0 : r.solid[idxOf(x, y)];

    // 高度场：内部恒定厚度，近边缘 smoothstep 收敛到 0（形成倒角）
    function heightAt(i) {
      const d = dist[i];
      if (d >= bevel) return depth;
      const t = d / bevel;
      return depth * (t * t * (3 - 2 * t));
    }

    for (let y = 0; y < GY; y++) {
      for (let x = 0; x < GX; x++) {
        const i = idxOf(x, y);
        if (!r.solid[i]) continue;
        const h = heightAt(i);
        const x0 = ox + x * cw, x1 = x0 + cw;
        const z0 = oz - y * ch, z1 = z0 - ch;
        // 该格中心 UV（顶/底与侧壁都用它，避免采样到透明像素）
        const ux = (x + 0.5) / GX, uy = 1 - (y + 0.5) / GY;
        const cr = r.colR[i] / 255, cg = r.colG[i] / 255, cb = r.colB[i] / 255;

        const At = [x0, h, z0], Bt = [x1, h, z0], Ct = [x1, h, z1], Dt = [x0, h, z1];
        const Ab = [x0, 0, z0], Bb = [x1, 0, z0], Cb = [x1, 0, z1], Db = [x0, 0, z1];

        // 顶面（+Y，逆时针）
        pos.push(...At, ...Bt, ...Ct, ...At, ...Ct, ...Dt);
        // 底面（-Y，反向）
        pos.push(...Ab, ...Cb, ...Bb, ...Ab, ...Db, ...Cb);
        for (let k = 0; k < 12; k++) { uv.push(ux, uy); col.push(cr, cg, cb); }

        // 侧壁：邻格为空则补墙（封闭实体，杜绝镂空）
        const wall = (p1, p2, p3, p4) => {
          pos.push(...p1, ...p2, ...p3, ...p1, ...p3, ...p4);
          for (let k = 0; k < 6; k++) { uv.push(ux, uy); col.push(cr, cg, cb); }
        };
        if (!solidAt(x, y - 1)) wall(At, Ab, Bb, Bt);
        if (!solidAt(x, y + 1)) wall(Dt, Bt, Cb, Db);
        if (!solidAt(x - 1, y)) wall(At, Dt, Db, Ab);
        if (!solidAt(x + 1, y)) wall(Bt, Bb, Cb, Ct);
      }
    }

    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));

    // ---------- 弧面整形：正面向外鼓出 sqrt(1-u²)，呈现杯/罐体积感 ----------
    const bulge = opt.bulge || 0;
    if (bulge > 0.001 && hw > 1e-4) {
      const P = g.attributes.position.array;
      for (let i = 0; i < P.length; i += 3) {
        const x = P[i], y = P[i + 1];
        if (y <= 1e-6) continue;                      // 背面（y=0）保持平坦
        const u = Math.max(-1, Math.min(1, x / hw));
        const k = Math.sqrt(Math.max(0, 1 - u * u));  // 中央最鼓、边缘为 0（轮廓不变）
        P[i + 1] = y + bulge * k * (y / depth > 1 ? 1 : y / depth);
      }
      g.attributes.position.needsUpdate = true;
    }

    g.computeVertexNormals();
    return g;
  }

  /**
   * 官方图 → 回转体（轮廓旋转法，silhouette revolution）
   *
   * 为什么用旋转体：杯/罐/甜筒都是近似回转体。把官方图的「逐行左右边缘」
   * 取出来绕该行中心旋转一周，就能从单张正投影照片还原出真实体积，
   * 正面看仍是官方原图（UV 取该行的 sin 投影列，等价于中心投影），
   * 侧面/俯视则是完整的圆柱，而不是一片薄板。
   *
   * 世界坐标：图像行 → 世界 +Y，圆周 → XZ 平面；θ=0 时朝向 +Z（正对相机）。
   */
  function buildRevolved(data, W, H, opt) {
    const longSide = Math.max(W, H);
    const scale = 2.2 / longSide;
    const ROWS = opt.rows || 200;
    const NA = opt.segments || 112;
    const TH = 96;                                   // alpha 阈值（与清洗图一致）
    const ox = W / 2;                                // 图像中心 → 世界 X=0

    // 1) 逐行取轮廓：左/右边缘、中心、半径
    const rows = [];
    const ROWS2 = Math.max(ROWS, Math.min(H, 320));    // 至少每像素一行，避免 v 重复
    for (let i = 0; i < ROWS2; i++) {
      const y = Math.min(H - 1, Math.round((i + 0.5) * H / ROWS2));
      let l = -1, r = -1;
      for (let x = 0; x < W; x++) {
        if (data[(y * W + x) * 4 + 3] >= TH) { if (l < 0) l = x; r = x; }
      }
      if (l < 0 || r <= l) continue;
      rows.push({ y, l, r, c: (l + r) / 2, rad: (r - l) / 2 });
    }
    if (rows.length < 4) return null;

    // 2) 中心/半径平滑（去抖，避免旋转面出现台阶、条纹与多面体感）
    for (let pass = 0; pass < 4; pass++) {
      const sc = rows.map(o => o.c), sr = rows.map(o => o.rad);
      for (let i = 0; i < rows.length; i++) {
        const i0 = Math.max(0, i - 1), i1 = Math.min(rows.length - 1, i + 1);
        rows[i].c   = (sc[i0] + 2 * sc[i] + sc[i1]) / 4;
        rows[i].rad = (sr[i0] + 2 * sr[i] + sr[i1]) / 4;
      }
    }

    const pos = [], uv = [];
    const yw = (y) => (H - y) * scale;               // 图像行 → 世界高度（上为正）
    const ring = NA + 1;                             // 首尾重合，保证缝合

    // 3) 侧面：逐行逐角度生成环带
    for (let i = 0; i < rows.length; i++) {
      const R = rows[i];
      for (let j = 0; j <= NA; j++) {
        const th = (j / NA) * Math.PI * 2;
        const s = Math.sin(th), co = Math.cos(th);
        // 中心投影：正视（θ≈0）严格还原官方原图，斜视时贴图自然包裹圆柱面
        const xImg = R.c + R.rad * s;
        pos.push((xImg - ox) * scale, yw(R.y), R.rad * co * scale);
        // v 用几何行序而非整数像素行：否则采样行重复会让纹理纵向"扫描线"化
        uv.push(Math.min(1, Math.max(0, xImg / W)), 1 - i / (rows.length - 1));
      }
    }
    const idx = [];
    for (let i = 0; i < rows.length - 1; i++) {
      for (let j = 0; j < NA; j++) {
        const a = i * ring + j, b = a + 1, c = a + ring, d = c + 1;
        idx.push(a, c, b, b, c, d);                  // 外表面（法线朝外）
      }
    }

    // 4) 顶 / 底封口（用该行中心色，避免贴图在圆盘上被拉成放射状）
    function cap(row, dir) {
      const y0 = yw(row.y), r0 = row.rad * scale;
      const base = pos.length / 3;
      const u0 = Math.min(1, Math.max(0, row.c / W)), v0 = 1 - row.y / H;
      pos.push((row.c - ox) * scale, y0, 0); uv.push(u0, v0);
      for (let j = 0; j <= NA; j++) {
        const th = (j / NA) * Math.PI * 2;
        const xImg = row.c + row.rad * Math.sin(th);
        pos.push((xImg - ox) * scale, y0, r0 * Math.cos(th));
        uv.push(u0, v0);                             // 统一取中心色
      }
      for (let j = 0; j < NA; j++) {
        const a = base, b = base + 1 + j, c = base + 2 + j;
        if (dir > 0) idx.push(a, b, c); else idx.push(a, c, b);
      }
    }
    cap(rows[rows.length - 1], -1);                  // 底（图像最下一行）
    cap(rows[0], 1);                                 // 顶（图像最上一行）

    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
    g.setIndex(idx);
    g.computeVertexNormals();
    return g;
  }

  // ---------- 浏览器：官方图 → 站立朝向的 3D 网格 ----------
  function build(code, url, onDone, onFail) {
    const spec = SPEC[code];
    if (!spec) { onFail && onFail("no-spec"); return; }
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      try {
        const cvs = document.createElement("canvas");
        cvs.width = img.naturalWidth || img.width;
        cvs.height = img.naturalHeight || img.height;
        const ctx = cvs.getContext("2d");
        ctx.drawImage(img, 0, 0);
        const px = ctx.getImageData(0, 0, cvs.width, cvs.height);

        // 轮廓旋转法：从官方图逐行轮廓还原回转体（真实体积、水密闭合）
        const geo = buildRevolved(px.data, px.width, px.height, spec);

        const tex = new THREE.CanvasTexture(cvs);
        if (THREE.sRGBEncoding !== undefined) tex.encoding = THREE.sRGBEncoding;
        tex.anisotropy = 8;   // 斜视（圆柱侧面）时抗摩尔纹/模糊
        tex.needsUpdate = true;

        // 官方图是「已烘焙光照」的产品摄影：再叠加三点光会二次过曝（发白成雾）。
        // 因此以自发光贴图（emissiveMap）为主呈现官方原色，仅保留少量漫反射
        // 让圆柱面的明暗变化（体积感）可见。
        const emis = spec.emissive != null ? spec.emissive : 0.90;
        const diff = spec.diffuse != null ? spec.diffuse : 0.12;
        const mat = new THREE.MeshStandardMaterial({
          map: tex,
          emissive: 0xffffff,
          emissiveMap: tex,
          emissiveIntensity: emis,
          transparent: false,
          side: THREE.DoubleSide,
          roughness: spec.rough,
          metalness: spec.metal
        });
        mat.envMapIntensity = 0.10;
        if (mat.color) mat.color.setScalar(diff);

        const mesh = new THREE.Mesh(geo, mat);
        mesh.userData.photo3d = true;
        mesh.userData.code = code;
        onDone(mesh);
      } catch (e) {
        console.warn("Photo3D 构建失败", code, e);
        onFail && onFail(e);
      }
    };
    img.onerror = () => { console.warn("Photo3D 官方图加载失败", code); onFail && onFail("img"); };
    img.src = url;
  }

  global.Photo3D = {
    has: c => Object.prototype.hasOwnProperty.call(SPEC, c),
    codes: CODES,
    build,
    buildGeometry,
    buildRevolved
  };
})(typeof window !== "undefined" ? window : globalThis);
