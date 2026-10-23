/* =========================================================================
 *  麦当劳「真」随心配 · 图像转 3D 网格工具 (Img2Mesh)  v1.0
 *  ——「将现有素材图转换为 3D 模型」的可实践方案
 *
 *  原理（2D→3D 落地路径，无需云端/模型权重，纯几何）：
 *    1. 读取官方透明 PNG 的 RGBA，得到 alpha 轮廓（2D 形状）；
 *    2. 把轮廓栅格化为 GX×GY 网格，统计每格"是否实心"与平均色；
 *    3. 赋予"恒定厚度 + 边缘倒角"高度场：内部恒厚、靠近轮廓的若干格
 *       平滑收敛到 0，形成一块"带圆角厚度的立体切片"（而非鼓包/纸片）；
 *    4. 生成 顶面(带官方贴图 UV，受光 MeshStandardMaterial) + 底面 + 倒角侧壁
 *       的封闭实体，旋转时呈现真实体积与光影。
 *
 *  用途：
 *    - 把每个官方成品图（巨无霸/薯条/可乐…）转成可独立旋转、摆放的 3D 模型，
 *      打破"界面只展示套餐整体"的限制——每个单品都是独立 3D 对象。
 *  依赖：three.min.js (r128)（global.THREE）
 *  兼容：浏览器（用 canvas 取像素）+ Node（直接喂 RGBA 数组做几何路径测试）。
 * ========================================================================= */
(function (global) {
  "use strict";
  const THREE = global.THREE;

  // ---- 工具：根据阈值把图像栅格化为实心网格（含平均色） ----
  function rasterize(data, W, H, GX, GY) {
    const cellW = W / GX, cellH = H / GY;
    const solid = new Uint8Array(GX * GY);
    const colR = new Float32Array(GX * GY);
    const colG = new Float32Array(GX * GY);
    const colB = new Float32Array(GX * GY);
    const cnt = new Float32Array(GX * GY);
    for (let y = 0; y < H; y++) {
      const gyy = Math.min(GY - 1, (y / cellH) | 0);
      for (let x = 0; x < W; x++) {
        const gxx = Math.min(GX - 1, (x / cellW) | 0);
        const i = y * W + x;
        const a = data[i * 4 + 3];
        if (a > 40) {
          const idx = gyy * GX + gxx;
          solid[idx] = 1;
          colR[idx] += data[i * 4];
          colG[idx] += data[i * 4 + 1];
          colB[idx] += data[i * 4 + 2];
          cnt[idx] += 1;
        }
      }
    }
    for (let k = 0; k < GX * GY; k++) {
      if (cnt[k] > 0) { colR[k] /= cnt[k]; colG[k] /= cnt[k]; colB[k] /= cnt[k]; }
    }
    return { solid, colR, colG, colB, GX, GY, cellW, cellH };
  }

  // ---- 距离边界（多遍侵蚀），用于高度场膨胀 ----
  function edt(solid, GX, GY) {
    const dist = new Int16Array(GX * GY).fill(0);
    // 0 表示非实心；实心从 1 开始，向外扩散计数
    const pass = (inc) => {
      for (let y = 0; y < GY; y++) for (let x = 0; x < GX; x++) {
        const idx = y * GX + x;
        if (!solid[idx]) continue;
        let m = 1e9;
        if (x > 0) m = Math.min(m, dist[idx - 1] + 1);
        if (x < GX - 1) m = Math.min(m, dist[idx + 1] + 1);
        if (y > 0) m = Math.min(m, dist[idx - GX] + 1);
        if (y < GY - 1) m = Math.min(m, dist[idx + GX] + 1);
        if (m < dist[idx]) dist[idx] = m;
      }
    };
    // 初始：实心且与空心相邻 = 1
    for (let y = 0; y < GY; y++) for (let x = 0; x < GX; x++) {
      const idx = y * GX + x;
      if (!solid[idx]) { dist[idx] = 0; continue; }
      let edge = false;
      if (x === 0 || x === GX - 1 || y === 0 || y === GY - 1) edge = true;
      else {
        if (!solid[idx - 1] || !solid[idx + 1] || !solid[idx - GX] || !solid[idx + GX]) edge = true;
      }
      dist[idx] = edge ? 1 : 1e9;
    }
    for (let k = 0; k < Math.max(GX, GY); k++) pass();
    return dist;
  }

  /**
   * 核心：把 RGBA 数组转成 3D 实体几何
   * @param {Object} o
   *   data: Uint8ClampedArray RGBA
   *   width,height
   *   thickness: 物体厚度（世界单位）
   *   grid: 长边栅格数（默认 56）
   *   flat: true 时为薄板（高度恒定），false 为膨胀圆顶
   *   radius: 膨胀半径（格），越大越圆
   * @returns {THREE.BufferGeometry}  Y-up：图像 x→X，图像 y→-Z，高度→Y
   */
  function build(o) {
    const W = o.width, H = o.height;
    const longSide = Math.max(W, H);
    const GX = W >= H ? (o.grid || 56) : Math.max(8, Math.round((o.grid || 56) * W / H));
    const GY = H > W ? (o.grid || 56) : Math.max(8, Math.round((o.grid || 56) * H / W));
    const r = rasterize(o.data, W, H, GX, GY);
    const dist = edt(r.solid, GX, GY);
    const bevel = o.bevel || 5;        // 边缘倒角宽度（格）
    const thickness = o.thickness || 0.45;
    const flat = !!o.flat;
    const pillow = o.pillow != null ? o.pillow : 0.12; // 顶面极轻微拱起，避免死板

    // 世界尺度：长边 = 2.2
    const scale = 2.2 / longSide;
    const ox = -W * scale / 2, oz = H * scale / 2;

    const pos = [];
    const uv = [];
    const col = [];

    function heightAt(idx) {
      if (flat) return thickness;
      const d = dist[idx];
      // 恒定厚度 + 边缘 smoothstep 倒角
      let h = thickness;
      if (d < bevel) {
        const t = Math.max(0, d / bevel);
        const s = t * t * (3 - 2 * t);
        h = thickness * s;
      }
      // 极轻微 pillow 拱起（仅内部），让正面不死板
      const interior = Math.min(1, d / (bevel + 2));
      h += thickness * pillow * interior * (1 - interior) * 4;
      return h;
    }
    function corner(gx, gy) {
      return [ox + (gx + 0.5) * (W / GX) * scale, 0, oz - (gy + 0.5) * (H / GY) * scale];
    }

    const idxOf = (x, y) => y * GX + x;
    const solidAt = (x, y) => (x < 0 || y < 0 || x >= GX || y >= GY) ? 0 : r.solid[idxOf(x, y)];

    for (let y = 0; y < GY; y++) for (let x = 0; x < GX; x++) {
      const idx = idxOf(x, y);
      if (!r.solid[idx]) continue;
      const h = heightAt(idx);
      const c = [
        r.colR[idx] / 255, r.colG[idx] / 255, r.colB[idx] / 255
      ];
      const uvx = (x + 0.5) / GX, uvy = 1 - (y + 0.5) / GY;

      const a = corner(x, y), b = corner(x + 1, y), cc = corner(x + 1, y + 1), d = corner(x, y + 1);
      // 顶 / 底顶点（每格独立，避免索引复杂）
      const At = [a[0], h, a[2]], Bt = [b[0], h, b[2]], Ct = [cc[0], h, cc[2]], Dt = [d[0], h, d[2]];
      const Ab = [a[0], 0, a[2]], Bb = [b[0], 0, b[2]], Cb = [cc[0], 0, cc[2]], Db = [d[0], 0, d[2]];

      // 顶面（Y 朝上，逆时针）
      pos.push(...At, ...Bt, ...Ct, ...At, ...Ct, ...Dt);
      uv.push(uvx, uvy, uvx + 1 / GX, uvy, uvx + 1 / GX, uvy + 1 / GY, uvx, uvy, uvx + 1 / GX, uvy + 1 / GY, uvx, uvy + 1 / GY);
      for (let k = 0; k < 6; k++) col.push(...c);
      // 底面（反向）
      pos.push(...Ab, ...Cb, ...Bb, ...Ab, ...Db, ...Cb);
      uv.push(uvx, uvy, uvx + 1 / GX, uvy + 1 / GY, uvx + 1 / GX, uvy, uvx, uvy, uvx, uvy + 1 / GY, uvx + 1 / GX, uvy + 1 / GY);
      for (let k = 0; k < 6; k++) col.push(...c);
      // 侧壁：4 条边若邻格非实心则补墙
      if (!solidAt(x, y - 1)) { pos.push(...At, ...Ab, ...Bb, ...At, ...Bb, ...Bt); addWallUV(uv, uvx, uvy); addWallCol(col, c, 6); }
      if (!solidAt(x, y + 1)) { pos.push(...Dt, ...Bt, ...Cb, ...Dt, ...Cb, ...Db); addWallUV(uv, uvx, uvy); addWallCol(col, c, 6); }
      if (!solidAt(x - 1, y)) { pos.push(...At, ...Dt, ...Db, ...At, ...Db, ...Ab); addWallUV(uv, uvx, uvy); addWallCol(col, c, 6); }
      if (!solidAt(x + 1, y)) { pos.push(...Bt, ...Bb, ...Cb, ...Bt, ...Cb, ...Ct); addWallUV(uv, uvx, uvy); addWallCol(col, c, 6); }
    }

    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
    g.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
    g.computeVertexNormals();
    g.userData.scale = scale;
    return g;
  }

  function addWallUV(uv, uvx, uvy) {
    // 壁用单元 UV 近似
    for (let k = 0; k < 6; k++) uv.push(uvx + (k % 2) / 2, uvy);
  }
  function addWallCol(col, c, n) { for (let k = 0; k < n; k++) col.push(...c); }

  /**
   * 浏览器：从 <img>/Image 构建带官方贴图的 3D 网格
   * @returns {THREE.Mesh}  受光 MeshStandardMaterial（呈现真实体积与光影）
   */
  function fromImageElement(img, opts) {
    opts = opts || {};
    const canvas = global.document.createElement("canvas");
    canvas.width = img.naturalWidth || img.width;
    canvas.height = img.naturalHeight || img.height;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(img, 0, 0);
    const d = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const geo = build({ data: d.data, width: d.width, height: d.height,
      thickness: opts.thickness, grid: opts.grid, flat: opts.flat, bevel: opts.bevel });
    const tex = new THREE.CanvasTexture(canvas);
    if (THREE.sRGBEncoding) tex.encoding = THREE.sRGBEncoding;
    const mat = new THREE.MeshStandardMaterial({
      map: tex, transparent: true, alphaTest: 0.06,
      roughness: 0.72, metalness: 0.0, side: THREE.DoubleSide,
      vertexColors: false
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.userData.isImg2Mesh = true;
    return mesh;
  }

  global.Img2Mesh = { build, fromImageElement, rasterize, edt };
  if (typeof module !== "undefined" && module.exports) module.exports = global.Img2Mesh;
})(typeof window !== "undefined" ? window : globalThis);
