// 无 GPU 冒烟测试：加载真实 three.js(r128) + burger3d.js v3，跑 buildBurger / classify / rolePriority 路径
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
global.window = global;
global.document = {
  createElement() {
    return {
      width: 0, height: 0,
      getContext() {
        return {
          fillRect() {}, beginPath() {}, arc() {}, fill() {},
          createRadialGradient() { return { addColorStop() {} }; },
          set fillStyle(v) {}, get fillStyle() { return ""; },
        };
      },
    };
  },
};
const THREE = require(path.join(ROOT, "assets", "vendor", "three.min.js"));
global.THREE = THREE;

const code = fs.readFileSync(path.join(ROOT, "assets", "burger3d.js"), "utf8");
eval(code);
const B = global.Burger3D;
if (!B) throw new Error("Burger3D 未导出");

// 仿真官方产品图加载器：返回带尺寸的假纹理
const fakeTex = { image: { width: 600, height: 400 }, encoding: 0, dispose() {} };
B.setPhotoLoader((code) => fakeTex);

const MAT = JSON.parse(fs.readFileSync(path.join(ROOT, "assets", "materials.json"), "utf8")).materials;
const BY = {}; MAT.forEach((m) => (BY[m.code] = m));

let totalMeshes = 0, designs = 0;
const tests = [
  ["1440"], ["521903"], ["521903", "1440", "4810"], ["1600", "6102"],
  ["511781", "1120", "4810"], ["521950", "515837", "521917"], ["1440", "521903", "1120", "4810", "521946"],
];
for (const layers of tests) {
  const r = B.buildBurger(layers, BY, {});
  let meshes = 0;
  r.group.traverse((o) => { if (o.isMesh) meshes++; });
  totalMeshes += meshes; designs++;
  if (r.ordered.length !== layers.length) throw new Error("ordered 长度不符 " + layers);
  console.log("设计", layers.join("+"), "=> meshes:", meshes, "height:", r.totalHeight.toFixed(2), "序:", r.ordered.length);
}
const sample = ["521903", "1440", "4810", "521946", "521950", "6102"];
for (const c of sample) {
  const cl = B.classify(BY[c]);
  console.log("classify", BY[c].name, "=>", cl.kind, "priority", B.rolePriority(cl.kind));
}
const combo = ["521946", "521903", "1440", "4810"];
const sorted = combo.slice().sort((a, b) => B.rolePriority(B.classify(BY[a]).kind) - B.rolePriority(B.classify(BY[b]).kind));
console.log("官方排序前:", combo.join(","), "后:", sorted.join(","));
console.log("ALL OK. total meshes:", totalMeshes, "designs:", designs);
