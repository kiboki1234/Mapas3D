import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Environment, Grid, OrbitControls, useGLTF } from "@react-three/drei";
import { Canvas, type ThreeEvent, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { Crosshair, RotateCcw, Square, View } from "lucide-react";
import { useAppStore } from "../../stores/appStore";
import type { SelectedFeature, ViewerStyle } from "../../types";

type CameraPreset = "fit" | "top" | "isometric";

const palette: Record<ViewerStyle, Record<string, string>> = {
  cartographic: { explicit: "#3b95ff", derived: "#35c98c", unknown: "#8993a3", road: "#232a34" },
  architectural: { explicit: "#d8dde5", derived: "#b9c5d6", unknown: "#838b96", road: "#30343a" },
  night: { explicit: "#45a6ff", derived: "#2be4a7", unknown: "#536272", road: "#151922" },
  gis: { explicit: "#277ef1", derived: "#28bf74", unknown: "#8d95a1", road: "#d8a540" },
};

function Loader() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]}>
      <ringGeometry args={[8, 11, 48]} />
      <meshBasicMaterial color="#3b95ff" transparent opacity={0.75} />
    </mesh>
  );
}

function Model({ url, style }: { url: string; style: ViewerStyle }) {
  const gltf = useGLTF(url);
  const setSelected = useAppStore((state) => state.setSelectedFeature);
  const model = useMemo(() => {
    const clone = gltf.scene.clone(true);
    clone.traverse((object) => {
      if (object instanceof THREE.Mesh) {
        object.material = Array.isArray(object.material)
          ? object.material.map((material) => material.clone())
          : object.material.clone();
        object.castShadow = true;
        object.receiveShadow = true;
      }
    });
    return clone;
  }, [gltf.scene]);

  useEffect(() => {
    model.traverse((object) => {
      if (!(object instanceof THREE.Mesh)) return;
      const data = object.userData as SelectedFeature;
      const category = data.road_class ? "road" : data.height_type ?? "unknown";
      const color = palette[style][category] ?? palette[style].unknown;
      const materials = Array.isArray(object.material) ? object.material : [object.material];
      materials.forEach((material) => {
        if (material instanceof THREE.MeshStandardMaterial) {
          material.color.set(color);
          material.roughness = style === "architectural" ? 0.62 : 0.85;
          material.metalness = style === "night" ? 0.15 : 0.02;
          material.needsUpdate = true;
        }
      });
    });
  }, [model, style]);

  const select = (event: ThreeEvent<MouseEvent>) => {
    event.stopPropagation();
    setSelected(event.object.userData as SelectedFeature);
  };
  return <primitive object={model} onClick={select} />;
}

function CameraController({ modelUrl, preset }: { modelUrl: string; preset: CameraPreset }) {
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
    camera.near = 0.1;
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
      <Canvas
        shadows
        camera={{ position: [180, 150, 180], fov: 45, near: 0.1, far: 5000 }}
        onPointerMissed={() => setSelected(null)}
        gl={{ antialias: true, preserveDrawingBuffer: false }}
      >
        <color attach="background" args={[style === "night" ? "#05070c" : "#0b1119"]} />
        <ambientLight intensity={style === "night" ? 0.55 : 1.15} />
        <directionalLight position={[120, 180, 80]} intensity={style === "night" ? 1.1 : 2.2} castShadow />
        <Suspense fallback={<Loader />}>
          <Model url={modelUrl} style={style} />
          <CameraController key={`${preset}-${presetTick}`} modelUrl={modelUrl} preset={preset} />
          {style !== "night" && <Environment preset="city" />}
        </Suspense>
        <Grid
          infiniteGrid
          fadeDistance={800}
          fadeStrength={5}
          cellSize={10}
          sectionSize={100}
          cellColor="#273343"
          sectionColor="#3e5d7d"
          position={[0, -0.03, 0]}
        />
      </Canvas>
    </div>
  );
}

