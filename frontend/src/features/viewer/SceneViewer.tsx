import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Environment, Grid, OrbitControls, useGLTF } from "@react-three/drei";
import { Canvas, type ThreeEvent, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { Camera, CarFront, Crosshair, RotateCcw, Square, View } from "lucide-react";
import { useAppStore } from "../../stores/appStore";
import type { SelectedFeature, ViewerStyle } from "../../types";

type CameraPreset = "fit" | "top" | "isometric";
type DrivingCamera = "chase" | "hood";

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

function VehicleController({
  modelUrl,
  enabled,
  cameraMode,
  resetToken,
  onSpeed,
}: {
  modelUrl: string;
  enabled: boolean;
  cameraMode: DrivingCamera;
  resetToken: number;
  onSpeed: (speedKmh: number) => void;
}) {
  const { camera } = useThree();
  const gltf = useGLTF(modelUrl);
  const vehicle = useRef<THREE.Group>(null);
  const pressed = useRef(new Set<string>());
  const speed = useRef(0);
  const yaw = useRef(0);
  const position = useRef(new THREE.Vector3());
  const speedReportClock = useRef(0);

  const drivingArea = useMemo(() => {
    gltf.scene.updateMatrixWorld(true);
    const sceneBounds = new THREE.Box3().setFromObject(gltf.scene).expandByScalar(25);
    let roadBounds: THREE.Box3 | null = null;
    let roadScore = -1;
    gltf.scene.traverse((object) => {
      if (!(object instanceof THREE.Mesh) || !object.userData.road_class) return;
      object.geometry.computeBoundingBox();
      if (!object.geometry.boundingBox) return;
      const bounds = object.geometry.boundingBox.clone().applyMatrix4(object.matrixWorld);
      const size = bounds.getSize(new THREE.Vector3());
      const score = Math.max(size.x, size.z);
      if (score > roadScore) {
        roadScore = score;
        roadBounds = bounds;
      }
    });
    const spawnBounds = roadBounds ?? sceneBounds;
    const spawn = spawnBounds.getCenter(new THREE.Vector3());
    spawn.y = 0;
    const roadSize = spawnBounds.getSize(new THREE.Vector3());
    return {
      bounds: sceneBounds,
      spawn,
      yaw: roadSize.x >= roadSize.z ? Math.PI / 2 : 0,
    };
  }, [gltf.scene]);

  useEffect(() => {
    position.current.copy(drivingArea.spawn);
    yaw.current = drivingArea.yaw;
    speed.current = 0;
    onSpeed(0);
    if (vehicle.current) {
      vehicle.current.position.copy(position.current);
      vehicle.current.rotation.y = yaw.current;
    }
  }, [drivingArea, onSpeed, resetToken]);

  useEffect(() => {
    if (!enabled) {
      pressed.current.clear();
      speed.current = 0;
      onSpeed(0);
      return;
    }
    const controlledKeys = new Set([
      "w", "a", "s", "d", "arrowup", "arrowleft", "arrowdown", "arrowright", " ",
    ]);
    const keydown = (event: KeyboardEvent) => {
      const key = event.key.toLowerCase();
      if (!controlledKeys.has(key)) return;
      event.preventDefault();
      pressed.current.add(key);
    };
    const keyup = (event: KeyboardEvent) => pressed.current.delete(event.key.toLowerCase());
    const blur = () => pressed.current.clear();
    window.addEventListener("keydown", keydown);
    window.addEventListener("keyup", keyup);
    window.addEventListener("blur", blur);
    return () => {
      window.removeEventListener("keydown", keydown);
      window.removeEventListener("keyup", keyup);
      window.removeEventListener("blur", blur);
      pressed.current.clear();
    };
  }, [enabled, onSpeed]);

  useFrame((_, rawDelta) => {
    if (!enabled || !vehicle.current) return;
    const delta = Math.min(rawDelta, 0.05);
    const keys = pressed.current;
    const accelerate = keys.has("w") || keys.has("arrowup");
    const reverse = keys.has("s") || keys.has("arrowdown");
    const steer = (keys.has("a") || keys.has("arrowleft") ? 1 : 0)
      - (keys.has("d") || keys.has("arrowright") ? 1 : 0);

    if (accelerate) speed.current += 8.5 * delta;
    else if (reverse) speed.current -= (speed.current > 0 ? 15 : 5) * delta;
    else speed.current = THREE.MathUtils.damp(speed.current, 0, 2.2, delta);
    if (keys.has(" ")) speed.current = THREE.MathUtils.damp(speed.current, 0, 12, delta);
    speed.current = THREE.MathUtils.clamp(speed.current, -7, 24);

    if (Math.abs(speed.current) > 0.15 && steer !== 0) {
      const direction = Math.sign(speed.current);
      const steeringStrength = Math.min(Math.abs(speed.current) / 5, 1);
      yaw.current += steer * direction * steeringStrength * 1.55 * delta;
    }

    const forward = new THREE.Vector3(Math.sin(yaw.current), 0, Math.cos(yaw.current));
    position.current.addScaledVector(forward, speed.current * delta);
    const bounds = drivingArea.bounds;
    const clampedX = THREE.MathUtils.clamp(position.current.x, bounds.min.x, bounds.max.x);
    const clampedZ = THREE.MathUtils.clamp(position.current.z, bounds.min.z, bounds.max.z);
    if (clampedX !== position.current.x || clampedZ !== position.current.z) speed.current = 0;
    position.current.set(clampedX, 0, clampedZ);

    vehicle.current.position.copy(position.current);
    vehicle.current.rotation.y = yaw.current;

    const lookAt = position.current.clone().addScaledVector(forward, cameraMode === "hood" ? 14 : 4);
    lookAt.y = cameraMode === "hood" ? 1.35 : 1.1;
    const desiredCamera = cameraMode === "hood"
      ? position.current.clone().addScaledVector(forward, 0.75).add(new THREE.Vector3(0, 1.45, 0))
      : position.current.clone().addScaledVector(forward, -8.5).add(new THREE.Vector3(0, 4.2, 0));
    camera.position.lerp(desiredCamera, 1 - Math.exp(-8 * delta));
    camera.lookAt(lookAt);

    speedReportClock.current += delta;
    if (speedReportClock.current >= 0.1) {
      speedReportClock.current = 0;
      onSpeed(Math.abs(speed.current) * 3.6);
    }
  });

  return (
    <group ref={vehicle} visible={enabled}>
      <mesh position={[0, 0.72, 0]} castShadow>
        <boxGeometry args={[1.75, 0.55, 3.5]} />
        <meshStandardMaterial color="#258cf4" roughness={0.42} metalness={0.3} />
      </mesh>
      <mesh position={[0, 1.2, -0.25]} castShadow>
        <boxGeometry args={[1.48, 0.52, 1.7]} />
        <meshStandardMaterial color="#b9d9ed" roughness={0.2} metalness={0.12} />
      </mesh>
      {([-0.96, 0.96] as const).flatMap((x) => ([-1.1, 1.1] as const).map((z) => (
        <mesh key={`${x}-${z}`} position={[x, 0.42, z]} rotation={[0, 0, Math.PI / 2]} castShadow>
          <cylinderGeometry args={[0.38, 0.38, 0.25, 16]} />
          <meshStandardMaterial color="#0b0d10" roughness={0.9} />
        </mesh>
      )))}
      <mesh position={[0, 0.78, 1.79]}>
        <boxGeometry args={[1.2, 0.18, 0.06]} />
        <meshStandardMaterial color="#d9f1ff" emissive="#a9ddff" emissiveIntensity={1.4} />
      </mesh>
    </group>
  );
}

function CameraController({
  modelUrl,
  preset,
  enabled,
}: {
  modelUrl: string;
  preset: CameraPreset;
  enabled: boolean;
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
    camera.near = 0.1;
    camera.far = Math.max(5000, distance * 10);
    camera.updateProjectionMatrix();
    controls.current?.target.copy(center);
    controls.current?.update();
  }, [camera, gltf.scene, preset]);
  return <OrbitControls ref={controls} makeDefault enabled={enabled} enableDamping dampingFactor={0.08} maxPolarAngle={Math.PI / 2.02} />;
}

export function SceneViewer({ modelUrl }: { modelUrl: string }) {
  const style = useAppStore((state) => state.viewerStyle);
  const setSelected = useAppStore((state) => state.setSelectedFeature);
  const [preset, setPreset] = useState<CameraPreset>("fit");
  const [presetTick, setPresetTick] = useState(0);
  const [driving, setDriving] = useState(false);
  const [drivingCamera, setDrivingCamera] = useState<DrivingCamera>("chase");
  const [speedKmh, setSpeedKmh] = useState(0);
  const [vehicleResetToken, setVehicleResetToken] = useState(0);
  const applyPreset = (next: CameraPreset) => {
    setPreset(next);
    setPresetTick((value) => value + 1);
  };
  const toggleDriving = () => {
    if (driving) {
      setDriving(false);
      setSpeedKmh(0);
      applyPreset("fit");
      return;
    }
    setSelected(null);
    setDriving(true);
  };
  useEffect(() => {
    setDriving(false);
    setSpeedKmh(0);
  }, [modelUrl]);
  return (
    <div className={`viewer-shell viewer-${style}`}>
      <div className="viewer-tools" aria-label="Controles de cámara">
        <button title="Encuadrar" disabled={driving} onClick={() => applyPreset("fit")}><RotateCcw size={16} /></button>
        <button title="Vista superior" disabled={driving} onClick={() => applyPreset("top")}><Square size={16} /></button>
        <button title="Vista isométrica" disabled={driving} onClick={() => applyPreset("isometric")}><View size={16} /></button>
        <button title="Deseleccionar" onClick={() => setSelected(null)}><Crosshair size={16} /></button>
        <button className={driving ? "active" : ""} title={driving ? "Salir del modo vehículo" : "Conducir"} onClick={toggleDriving}><CarFront size={16} /></button>
        {driving && <button title="Cambiar cámara" onClick={() => setDrivingCamera((current) => current === "chase" ? "hood" : "chase")}><Camera size={16} /></button>}
        {driving && <button title="Reiniciar vehículo" onClick={() => setVehicleResetToken((value) => value + 1)}><RotateCcw size={16} /></button>}
      </div>
      {driving && (
        <div className="drive-hud" aria-live="polite">
          <div className="drive-speed"><strong>{Math.round(speedKmh)}</strong><span>km/h</span></div>
          <div className="drive-status">
            <b>MODO VEHÍCULO</b>
            <span>{drivingCamera === "chase" ? "Cámara exterior" : "Cámara de capó"}</span>
          </div>
          <div className="drive-keys"><kbd>WASD</kbd><span>mover</span><kbd>ESPACIO</kbd><span>frenar</span></div>
        </div>
      )}
      <Canvas
        shadows
        camera={{ position: [180, 150, 180], fov: 45, near: 0.1, far: 5000 }}
        onPointerMissed={() => !driving && setSelected(null)}
        gl={{ antialias: true, preserveDrawingBuffer: false }}
      >
        <color attach="background" args={[style === "night" ? "#05070c" : "#0b1119"]} />
        <ambientLight intensity={style === "night" ? 0.55 : 1.15} />
        <directionalLight position={[120, 180, 80]} intensity={style === "night" ? 1.1 : 2.2} castShadow />
        <Suspense fallback={<Loader />}>
          <Model url={modelUrl} style={style} />
          <VehicleController
            modelUrl={modelUrl}
            enabled={driving}
            cameraMode={drivingCamera}
            resetToken={vehicleResetToken}
            onSpeed={setSpeedKmh}
          />
          <CameraController key={`${preset}-${presetTick}`} modelUrl={modelUrl} preset={preset} enabled={!driving} />
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

