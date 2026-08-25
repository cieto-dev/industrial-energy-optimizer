import React, { useEffect, useState } from "react"
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet"
import "leaflet/dist/leaflet.css"
import L from "leaflet"
import { IndustrialCluster } from "./GisMapComponent"
import { MapPin } from "lucide-react"
import { renderToString } from "react-dom/server"



// Custom Icon for clusters
const createCustomIcon = (isSelected: boolean, name: string) => {
  const iconHtml = renderToString(
    <div
      className={`h-7 w-7 rounded-full flex items-center justify-center shadow-lg transition-all ${
        isSelected
          ? "bg-primary text-primary-foreground ring-4 ring-primary/40"
          : "bg-background text-primary border border-primary/50 hover:bg-primary hover:text-primary-foreground"
      }`}
    >
      <MapPin className="h-4 w-4" />
    </div>
  )

  return L.divIcon({
    html: iconHtml,
    className: "custom-leaflet-icon",
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -14],
  })
}

interface MapViewProps {
  clusters: IndustrialCluster[]
  selectedCluster: IndustrialCluster | null
  onSelectCluster: (cluster: IndustrialCluster) => void
}

function MapUpdater({ selectedCluster }: { selectedCluster: IndustrialCluster | null }) {
  const map = useMap()

  useEffect(() => {
    if (selectedCluster) {
      map.flyTo([selectedCluster.lat, selectedCluster.lng], 9, {
        duration: 1.5,
      })
    }
  }, [selectedCluster, map])

  return null
}

export default function MapView({ clusters, selectedCluster, onSelectCluster }: MapViewProps) {
  const [isMounted, setIsMounted] = useState(false)
  const [mountKey, setMountKey] = useState('')
  
  useEffect(() => {
    setIsMounted(true)
    setMountKey(Math.random().toString(36).substring(7))
    
    // Cleanup function to help with strict mode unmounting
    return () => {
      setIsMounted(false)
    }
  }, [])

  // Center of India roughly
  const center = { lat: 20.5937, lng: 78.9629 }

  if (!isMounted) {
    return <div className="w-full h-full min-h-[400px] rounded-2xl bg-surface-muted animate-pulse" />
  }

  return (
    <div className="w-full h-full min-h-[400px] rounded-2xl overflow-hidden border border-border/40 relative">
      <MapContainer
        key={mountKey}
        center={[center.lat, center.lng]}
        zoom={5}
        style={{ width: "100%", height: "100%", zIndex: 10 }}
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.google.com/intl/en_US/help/terms_maps.html">Google Maps</a>'
          url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
        />
        
        {clusters.map((cluster) => (
          <Marker
            key={cluster.id}
            position={[cluster.lat, cluster.lng]}
            icon={createCustomIcon(selectedCluster?.id === cluster.id, cluster.name)}
            eventHandlers={{
              click: () => onSelectCluster(cluster),
            }}
          >
            <Popup className="custom-popup">
              <div className="font-semibold text-sm">{cluster.name}</div>
              <div className="text-xs text-muted-foreground">{cluster.district}, {cluster.state}</div>
            </Popup>
          </Marker>
        ))}

        <MapUpdater selectedCluster={selectedCluster} />
      </MapContainer>
    </div>
  )
}
