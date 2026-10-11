import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { OrbitControls, useGLTF } from "@react-three/drei";
import { Canvas, type ThreeEvent, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { Crosshair, RotateCcw, Square, View } from "lucide-react";
import { useAppStore } from "../../stores/appStore";
import type { SelectedFeature, ViewerStyle } from "../../types";

type CameraPreset = "fit" | "top" | "isometric";

const palette: Record<ViewerStyle, Record<string, string>> = {
  cartographic: { explicit: "#3b95ff", derived: "#35c98c", footprint_only: "#8993a3", unknown: "#8993a3", road: "#232a34", terrain: "#496f43" },
  architectural: { explicit: "#e5e1d9", derived: "#e5e1d9", footprint_only: "#b9a784", unknown: "#b9a784", road: "#42464c", terrain: "#73796e" },
  night: { explicit: "#45a6ff", derived: "#2be4a7", footprint_only: "#536272", unknown: "#536272", road: "#151922", terrain: "#1c3323" },
  gis: { explicit: "#277ef1", derived: "#28bf74", footprint_only: "#8d95a1", unknown: "#8d95a1", road: "#d8a540", terrain: "#668f52" },
};

function Loader() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]}>
      <ringGeometry args={[8, 11, 48]} />
      <meshBasicMaterial color="#3b95ff" transparent opacity={0.75} />
    </mesh>
  );
}

interface Layers { terrain: boolean; roads: boolean; footprints: boolean }

function Model({ url, style, layers }: { url: string; style: ViewerStyle; layers: Layers }) {
  const gltf = useGLTF(url);
  const setSelected = useAppStore((state) => state.setSelectedFeature);
  const model = useMemo(() => {
    const clone = gltf.scene.clone(true);
    clone.traverse((object) => {
      if (object instanceof THREE.Mesh) {
        // Los edificios con fachada y cubierta separadas cargan como un grupo glTF.
        let source: THREE.Object3D | null = object;
        while (source && !source.userData.feature_id) source = source.parent;
        if (source) object.userData = { ...source.userData, ...object.userData };
        object.material = Array.isArray(object.material)
          ? object.material.map((material) => material.clone())
          : object.material.clone();
        object.castShadow = Boolean(object.userData.height_m > 0);
        object.receiveShadow = true;
        const materials = Array.isArray(object.material) ? object.material : [object.material];
        materials.forEach((material) => {
          if (material instanceof THREE.MeshStandardMaterial) material.userData.originalMap = material.map;
        });
      }
    });
    return clone;
  }, [gltf.scene]);

  useEffect(() => {
    model.traverse((object) => {
      if (!(object instanceof THREE.Mesh)) return;
      const data = object.userData as SelectedFeature;
      const category = data.feature_type === "terrain"
        ? "terrain"
        : data.road_class ? "road" : data.height_type ?? "unknown";
      const color = palette[style][category] ?? palette[style].unknown;
      object.visible = category === "terrain" ? layers.terrain
        : category === "road" ? layers.roads
        : category === "footprint_only" ? layers.footprints : true;
      const materials = Array.isArray(object.material) ? object.material : [object.material];
      materials.forEach((material) => {
        if (material instanceof THREE.MeshStandardMaterial) {
          material.map = style === "architectural" ? material.userData.originalMap ?? null : null;
          material.color.set(material.map ? "#ffffff" : color);
          material.roughness = style === "architectural" ? 0.62 : 0.85;
          material.metalness = style === "night" ? 0.15 : 0.02;
          // Capas cartográficas próximas al suelo: conservar la prueba de
          // profundidad y evitar parpadeos por cuantización del depth buffer.
          material.polygonOffset = category === "road" || category === "footprint_only";
          material.polygonOffsetFactor = category === "footprint_only" ? -2 : -1;
          material.polygonOffsetUnits = -1;
          material.needsUpdate = true;
        }
      });
    });
  }, [model, style, layers]);

  useEffect(() => () => {
    model.traverse((object) => {
      if (object instanceof THREE.Mesh) {
        const materials = Array.isArray(object.material) ? object.material : [object.material];
        materials.forEach((material) => material.dispose());
      }
    });
  }, [model]);

  const select = (event: ThreeEvent<MouseEvent>) => {
    event.stopPropagation();
    setSelected(event.object.userData as SelectedFeature);
  };
  return <primitive object={model} onClick={select} />;
}

function CameraController({
  modelUrl,
  preset,
}: {
  modelUrl: string;
  preset: CameraPreset;
}) {
  const { camera } = useThree();
  const controls = useRef<any>(null);
  const gltf = useGLTF(modelUrl);
  useEffect(() => {
    const box = new THREE.Box3().setFromObject(gltf.scene);
    if (box.isEmpty()) return;
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const distance = Math.max(size.x, size.y, size.z, 50) * 1.15;
    if (preset === "top") camera.position.set(center.x, center.y + distance * 1.4, center.z + 0.01);
    else if (preset === "isometric") camera.position.set(center.x + distance, center.y + distance * 0.78, center.z + distance);
    else camera.position.set(center.x + distance * 0.75, center.y + distance * 0.65, center.z + distance * 0.75);
    camera.near = Math.max(0.5, distance / 4000);
    camera.far = Math.max(5000, distance * 10);
    camera.updateProjectionMatrix();
    controls.current?.target.copy(center);
    controls.current?.update();
  }, [camera, gltf.scene, preset]);
  return <OrbitControls ref={controls} makeDefault enableDamping dampingFactor={0.08} maxPolarAngle={Math.PI / 2.02} />;
}

export function SceneViewer({ modelUrl }: { modelUrl: string }) {
  const style = useAppStore((state) => state.viewerStyle);
  const setSelected = useAppStore((state) => state.setSelectedFeature);
  const [preset, setPreset] = useState<CameraPreset>("fit");
  const [presetTick, setPresetTick] = useState(0);
  const [layers, setLayers] = useState<Layers>({ terrain: true, roads: true, footprints: true });
  const applyPreset = (next: CameraPreset) => {
    setPreset(next);
    setPresetTick((value) => value + 1);
  };
  return (
    <div className={`viewer-shell viewer-${style}`}>
      <div className="viewer-tools" aria-label="Controles de cámara">
        <button title="Encuadrar" onClick={() => applyPreset("fit")}><RotateCcw size={16} /></button>
        <button title="Vista superior" onClick={() => applyPreset("top")}><Square size={16} /></button>
        <button title="Vista isométrica" onClick={() => applyPreset("isometric")}><View size={16} /></button>
        <button title="Deseleccionar" onClick={() => setSelected(null)}><Crosshair size={16} /></button>
      </div>
      <div className="viewer-layers" aria-label="Capas visibles">
        {([['terrain', 'Relieve'], ['roads', 'Vías'], ['footprints', 'Huellas sin altura']] as const).map(([key, label]) => (
          <label key={key}><input type="checkbox" checked={layers[key]}
            onChange={(event) => setLayers((current) => ({ ...current, [key]: event.target.checked }))} />{label}</label>
        ))}
      </div>
      <Canvas
        camera={{ position: [180, 150, 180], fov: 45, near: 0.1, far: 5000 }}
        onPointerMissed={() => setSelected(null)}
        gl={{ antialias: true, preserveDrawingBuffer: false }}
      >
        <color attach="background" args={[style === "night" ? "#05070c" : "#0b1119"]} />
        <ambientLight intensity={style === "night" ? 0.4 : 0.5} />
        <hemisphereLight args={["#ffffff", "#76726a", style === "night" ? 0.3 : 0.7]} />
        <directionalLight position={[120, 180, 80]} intensity={style === "night" ? 1.1 : 2} />
        <Suspense fallback={<Loader />}>
          <Model url={modelUrl} style={style} layers={layers} />
          <CameraController key={`${preset}-${presetTick}`} modelUrl={modelUrl} preset={preset} />
        </Suspense>
      </Canvas>
    </div>
  );
}

