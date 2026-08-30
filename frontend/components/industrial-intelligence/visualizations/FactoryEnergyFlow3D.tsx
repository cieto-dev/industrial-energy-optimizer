"use client"

import React, { useRef, useState } from "react"
import { Canvas, useFrame } from "@react-three/fiber"
import { OrbitControls, Environment, Html, Box, Sphere, Line } from "@react-three/drei"
import * as THREE from "three"

const ParticleStream = ({ start, end, color, speed = 1, count = 20 }: any) => {
  const points = React.useMemo(() => new Array(count).fill(0).map(() => {
    return {
      progress: Math.random(),
      speed: (Math.random() * 0.5 + 0.5) * speed
    }
  }), [count, speed]);

  const linesRef = useRef<THREE.Group>(null);
  
  useFrame((state, delta) => {
    if (!linesRef.current) return;
    linesRef.current.children.forEach((child: any, i) => {
      if (!points[i]) return;
      points[i].progress += delta * points[i].speed;
      if (points[i].progress > 1) points[i].progress = 0;
      
      const pos = new THREE.Vector3().lerpVectors(
        new THREE.Vector3(...start),
        new THREE.Vector3(...end),
        points[i].progress
      );
      child.position.copy(pos);
    });
  });

  return (
    <group>
      <group ref={linesRef}>
        {points.map((_, i) => (
          <mesh key={i}>
            <sphereGeometry args={[0.05, 8, 8]} />
            <meshBasicMaterial color={color} transparent opacity={0.6} />
          </mesh>
        ))}
      </group>
      <Line points={[start, end]} color={color} transparent opacity={0.2} dashed dashSize={0.2} gapSize={0.1} />
    </group>
  );
};

const Equipment = ({ position, size, name, color, isOperating }: any) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHover] = useState(false);
  
  useFrame((state) => {
    if (isOperating && meshRef.current) {
      meshRef.current.rotation.y = Math.sin(state.clock.elapsedTime) * 0.05;
    }
  });

  return (
    <group position={position}>
      <mesh 
        ref={meshRef}
        onPointerOver={() => setHover(true)}
        onPointerOut={() => setHover(false)}
      >
        <boxGeometry args={size} />
        <meshStandardMaterial color={hovered ? "#fff" : color} wireframe={hovered} />
      </mesh>
      
      {hovered && (
        <Html position={[0, size[1]/2 + 0.5, 0]} center zIndexRange={[100, 0]}>
          <div className="bg-neutral-900/90 backdrop-blur border border-neutral-700 text-white px-3 py-2 text-xs font-mono uppercase tracking-wider whitespace-nowrap">
            {name}
            <div className="text-[9px] text-emerald-400 mt-1">Status: Nominal</div>
          </div>
        </Html>
      )}
    </group>
  );
};

export const FactoryEnergyFlow3D = () => {
  return (
    <div className="w-full h-full bg-[#050505]">
      <Canvas camera={{ position: [5, 5, 8], fov: 45 }}>
        <color attach="background" args={['#050505']} />
        <fog attach="fog" args={['#050505', 10, 25]} />
        <ambientLight intensity={0.2} />
        <directionalLight position={[10, 10, 5]} intensity={1} color="#ffffff" />
        
        {/* Ground */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.5, 0]}>
          <planeGeometry args={[20, 20]} />
          <meshBasicMaterial color="#111" wireframe transparent opacity={0.2} />
        </mesh>

        {/* Equipment */}
        <Equipment position={[-3, 0.5, -2]} size={[2, 2, 2]} name="Boiler Unit 1" color="#333" isOperating={true} />
        <Equipment position={[0, 0.5, 2]} size={[3, 1, 1.5]} name="Steam Header" color="#444" isOperating={true} />
        <Equipment position={[3, 0.5, -1]} size={[1.5, 3, 1.5]} name="Process Heater" color="#2a2a2a" isOperating={true} />
        
        {/* Energy Streams */}
        <ParticleStream start={[-2, 1, -2]} end={[0, 1, 2]} color="#ff4400" speed={0.5} count={15} /> {/* High pressure steam */}
        <ParticleStream start={[0, 0.5, 2]} end={[3, 1, -1]} color="#ffaa00" speed={0.8} count={20} /> {/* Process steam */}
        
        <OrbitControls 
          enablePan={false} 
          minPolarAngle={Math.PI/4} 
          maxPolarAngle={Math.PI/2 - 0.1}
          minDistance={5}
          maxDistance={15}
          autoRotate
          autoRotateSpeed={0.5}
        />
        
        <Environment preset="city" />
      </Canvas>
    </div>
  );
};
