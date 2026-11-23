import { NodeIO } from '/usr/lib/node_modules/@gltf-transform/cli/node_modules/@gltf-transform/core/dist/index.js';
import { dequantize } from '/usr/lib/node_modules/@gltf-transform/cli/node_modules/@gltf-transform/functions/dist/index.js';
import { ALL_EXTENSIONS } from '/usr/lib/node_modules/@gltf-transform/cli/node_modules/@gltf-transform/extensions/dist/index.js';

const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const doc = await io.read('/tmp/tevy/classroom-tevy-decompressed.glb');
const root = doc.getRoot();
for (const mat of root.listMaterials()) {
  mat.setBaseColorTexture(null);
  mat.setMetallicRoughnessTexture(null);
  mat.setNormalTexture(null);
  mat.setEmissiveTexture(null);
  mat.setOcclusionTexture(null);
  mat.setDoubleSided(true);
}
// Dispose unreferenced textures/images explicitly (no prune: prune deletes TEXCOORD_0).
for (const tex of [...root.listTextures()]) tex.dispose();
// Drop sampler list leftovers are handled by writer; also drop extension props on materials
for (const mat of root.listMaterials()) {
  for (const ext of [...mat.listExtensions()]) {
    // keep emissive_strength / transmission extension objects (harmless, no textures)
    console.log('mat ext kept:', mat.getName(), ext.extensionName);
  }
}
await doc.transform(dequantize());
await io.write('/tmp/tevy/classroom-tevy-plain.glb', doc);
console.log('WROTE plain glb v2');
