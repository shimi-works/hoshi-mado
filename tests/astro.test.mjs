// astro/projection の検証。index.html から純関数ブロックを抽出して Node で実行する。
// 参照値は skyfield 1.54（歳差・章動込みのapparent位置）。簡易式との差の許容は±1°。
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(here, "..", "index.html"), "utf-8");

function extract(startMark, endMark) {
  const s = html.indexOf(startMark);
  const e = html.indexOf(endMark);
  if (s === -1 || e === -1) throw new Error(`marker not found: ${startMark}`);
  return html.slice(s + startMark.length, e);
}

const src = extract("// ==ASTRO-START==", "// ==ASTRO-END==");
const { astro, projection } = new Function(src + "\nreturn { astro, projection };")();

// skyfieldで生成した参照値（scratchpad/make_reference.py）
const REF = {
  sendai_night: { lat: 38.2682, lon: 140.8694, utc: Date.UTC(2026, 6, 11, 12, 0, 0), stars: [
    ["Betelgeuse", 88.792939, 7.407064, -41.059, 334.835],
    ["Sirius", 101.287155, -16.716116, -55.171, 299.429],
    ["Vega", 279.234735, 38.783689, 67.265, 79.465],
    ["Polaris", 37.954561, 89.264109, 37.693, 0.323],
    ["Antares", 247.351915, -26.432003, 25.197, 182.49],
    ["Spica", 201.298247, -11.161319, 22.796, 232.967],
  ]},
  newyork: { lat: 40.7128, lon: -74.006, utc: Date.UTC(2026, 0, 15, 6, 0, 0), stars: [
    ["Betelgeuse", 88.792939, 7.407064, 40.29, 239.574],
    ["Sirius", 101.287155, -16.716116, 26.501, 211.377],
    ["Vega", 279.234735, 38.783689, -5.522, 23.968],
    ["Polaris", 37.954561, 89.264109, 40.774, 359.184],
    ["Antares", 247.351915, -26.432003, -36.828, 95.205],
    ["Spica", 201.298247, -11.161319, 6.6, 111.084],
  ]},
};

let pass = 0, fail = 0;
function check(label, ok, detail) {
  if (ok) { pass++; }
  else { fail++; console.error(`  NG ${label}: ${detail}`); }
}
function angDiff(a, b) {
  return Math.abs(((a - b + 540) % 360) - 180);
}

// 1) Alt/Az が参照値と±1°で一致
for (const [caseName, c] of Object.entries(REF)) {
  console.log(`case: ${caseName}`);
  const lst = astro.lst(astro.julianDate(c.utc), c.lon);
  for (const [name, ra, dec, refAlt, refAz] of c.stars) {
    const { alt, az } = astro.raDecToAltAz(ra, dec, lst, c.lat);
    const dAlt = Math.abs(alt - refAlt);
    const dAz = angDiff(az, refAz);
    // 天頂・天底付近では方位差は意味が薄いので高度で重み付け
    const azErr = dAz * Math.cos(refAlt * Math.PI / 180);
    check(`${caseName}/${name} alt`, dAlt <= 1.0, `Δalt=${dAlt.toFixed(3)}° (got ${alt.toFixed(3)}, ref ${refAlt})`);
    check(`${caseName}/${name} az`, azErr <= 1.0, `Δaz=${dAz.toFixed(3)}° (got ${az.toFixed(3)}, ref ${refAz})`);
    console.log(`  ${name.padEnd(11)} alt ${alt.toFixed(2).padStart(7)} (ref ${refAlt}), az ${az.toFixed(2).padStart(7)} (ref ${refAz})`);
  }
}

// 2) projection の基本性質
{
  const cam = projection.makeCamera(120, 30, 0);
  const focal = projection.focalLength(70, 800);
  const center = projection.project(cam, astro.altAzToVec(30, 120), focal, 400, 400);
  check("projection center", center && Math.hypot(center[0] - 400, center[1] - 400) < 1e-6,
    `got ${center}`);
  // 視線の10°上の星は画面上で上（yが小さい）に来る
  const up10 = projection.project(cam, astro.altAzToVec(40, 120), focal, 400, 400);
  check("projection up", up10 && up10[1] < 400, `got ${up10}`);
  // 期待オフセット = focal*tan(10°)
  const expected = focal * Math.tan(10 * Math.PI / 180);
  check("projection scale", Math.abs((400 - up10[1]) - expected) < 0.5,
    `got ${(400 - up10[1]).toFixed(2)}, expected ${expected.toFixed(2)}`);
  // 背後の星はnull
  const behind = projection.project(cam, astro.altAzToVec(-30, 300), focal, 400, 400);
  check("projection behind", behind === null, `got ${behind}`);
  // ロール90°: 視線の上10°の星が画面の左右方向へ移る
  const camR = projection.makeCamera(120, 30, 90);
  const rolled = projection.project(camR, astro.altAzToVec(40, 120), focal, 400, 400);
  check("projection roll", rolled && Math.abs(rolled[1] - 400) < 1 && Math.abs(rolled[0] - 400) > expected * 0.9,
    `got ${rolled}`);
}

// 3) データ整合性（埋め込みデータの健全性）
{
  const dataSrc = extract("// ==DATA-START==", "// ==DATA-END==");
  const { STARS, LINES, CONST_INFO } = new Function(dataSrc + "\nreturn { STARS, LINES, CONST_INFO };")();
  check("data stars>=900", STARS.length >= 900, `got ${STARS.length}`);
  check("data 88 constellations", Object.keys(LINES).length === 88, `got ${Object.keys(LINES).length}`);
  check("data 88 const info", Object.keys(CONST_INFO).length === 88, `got ${Object.keys(CONST_INFO).length}`);
  const badIdx = Object.values(LINES).flat().filter(i => !Number.isInteger(i) || i < 0 || i >= STARS.length);
  check("data line indices valid", badIdx.length === 0, `bad: ${badIdx.slice(0, 5)}`);
  const betelgeuse = STARS.find(s => s[3] === "ベテルギウス");
  check("data Betelgeuse", betelgeuse && Math.abs(betelgeuse[0] - 88.79) < 0.05 && Math.abs(betelgeuse[1] - 7.41) < 0.05,
    `got ${JSON.stringify(betelgeuse)}`);
}

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
