/* Node 几何冒烟测试：验证 components3d（高保真）与 img2mesh（立体切片）几何路径零错误 */
const path = require("path");
const ROOT = path.join(__dirname, "..");
const THREE = require(path.join(ROOT, "assets", "vendor", "three.min.js"));
globalThis.THREE = THREE;
const Img2Mesh = require(path.join(ROOT, "assets", "img2mesh.js"));
const Components3D = require(path.join(ROOT, "assets", "components3d.js"));

let fail = 0;
function check(cond, msg) { if (!cond) { console.error("  ✗ " + msg); fail++; } else { console.log("  ✓ " + msg); } }

function countMeshes(obj) {
  let n = 0, v = 0;
  obj.traverse(o => {
    if (o.isMesh) {
      n++;
      const p = o.geometry.getAttribute("position");
      if (p) v += p.count;
      // NaN 检查
      if (p) for (let i = 0; i < p.array.length; i++) { if (Number.isNaN(p.array[i])) { fail++; console.error("  ✗ NaN at " + o.name); break; } }
    }
  });
  return { n, v };
}

console.log("=== Components3D 高保真组件 ===");
Components3D.CATALOG.forEach(c => {
  try {
    const g = Components3D.buildComponent(c.kind);
    const r = countMeshes(g);
    check(r.n >= 1 && r.v > 12, `${c.kind} 生成 ${r.n} 网格 / ${r.v} 顶点`);
  } catch (e) { check(false, c.kind + " 抛出: " + e.message); }
});

console.log("=== 堆叠 + 官方排序 ===");
const design = Components3D.stackComponents([
  { kind: "bunTop" }, { kind: "sauce" }, { kind: "beef" }, { kind: "bunBottom" }
]);
const r2 = countMeshes(design);
check(r2.n > 0, `堆叠 4 组件 -> ${r2.n} 网格`);

console.log("=== Img2Mesh 立体切片（合成圆形 alpha）===");
const W = 128, H = 128;
const data = new Uint8ClampedArray(W * H * 4);
for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
  const dx = x - W / 2, dy = y - H / 2;
  const a = (dx * dx + dy * dy) < (W * 0.4) * (W * 0.4) ? 255 : 0;
  const i = (y * W + x) * 4;
  data[i] = 220; data[i + 1] = 60; data[i + 2] = 40; data[i + 3] = a;
}
const geo = Img2Mesh.build({ data, width: W, height: H, thickness: 0.45, bevel: 6, grid: 56 });
const pos = geo.getAttribute("position");
let nan = false; for (let i = 0; i < pos.array.length; i++) if (Number.isNaN(pos.array[i])) nan = true;
check(pos && pos.count > 0 && !nan, `切片网格顶点 ${pos.count}，无 NaN`);

console.log("\n总计:", fail === 0 ? "全部通过 ✅" : (fail + " 项失败 ❌"));
process.exit(fail === 0 ? 0 : 1);
