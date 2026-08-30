"use client"

import React, { useRef } from "react"
import { Canvas, useFrame } from "@react-three/fiber"
import { OrbitControls, Environment, Cylinder, Sphere } from "@react-three/drei"
import * as THREE from "three"

const FlowParticle = ({ position, speed, color }: any) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const initialX = position[0];

  useFrame((state, delta) => {
    if (!meshRef.current) return;
    meshRef.current.position.x += speed * delta;
    // reset position
    if (meshRef.current.position.x > 5) {
      meshRef.current.position.x = -5;
    }
  });

  return (
    <mesh ref={meshRef} position={position}>
      <sphereGeometry args={[0.08, 8, 8]} />
      <meshBasicMaterial color={color} transparent opacity={0.6} />
    </mesh>
  );
};

const HeatExchangerTubes = () => {
  const tubes = [];
  for (let z = -1.5; z <= 1.5; z += 1) {
    for (let x = -2; x <= 2; x += 1) {
      tubes.push(
        <Cylinder key={`${x}-${z}`} args={[0.1, 0.1, 4, 16]} rotation={[Math.PI / 2, 0, 0]} position={[x, 0, z]}>
          <meshStandardMaterial color="#88ccff" metalness={0.8} roughness={0.2} />
        </Cylinder>
      );
    }
  }
  return <group>{tubes}</group>;
};

export const WasteHeatRecovery3D = () => {
  const particles = [];
  for (let i = 0; i < 50; i++) {
    particles.push(
      <FlowParticle 
        key={i} 
        position={[-5 + Math.random() * 10, (Math.random() - 0.5) * 2, (Math.random() - 0.5) * 3]} 
        speed={1 + Math.random() * 2} 
        color={i % 2 === 0 ? "#ff4400" : "#ffaa00"} 
      />
    );
  }

  return (
    <div className="w-full h-full bg-[#050505]">
      <Canvas camera={{ position: [5, 4, 5], fov: 45 }}>
        <color attach="background" args={['#050505']} />
        <ambientLight intensity={0.4} />
        <directionalLight position={[5, 10, 5]} intensity={1.5} color="#ffffff" />
        
        <HeatExchangerTubes />
        
        {particles}

        <OrbitControls 
          enablePan={false} 
          minPolarAngle={Math.PI/4} 
          maxPolarAngle={Math.PI/2}
          minDistance={3}
          maxDistance={12}
          autoRotate
          autoRotateSpeed={1}
        />
        
        <Environment preset="studio" />
      </Canvas>
      
      <div className="absolute top-6 left-6 max-w-[250px] bg-neutral-900/80 backdrop-blur border border-neutral-700 p-4">
         <h3 className="font-medium text-sm text-white mb-2">Cross-Flow Heat Exchanger</h3>
         <p className="text-xs text-neutral-400">
           Hot exhaust gases (orange) flow over cold water tubes (blue), transferring thermal energy without direct fluid contact.
         </p>
      </div>
    </div>
  );
};
