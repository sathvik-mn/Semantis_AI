import { useEffect, useRef, useState, useCallback } from 'react';

interface TubesBackgroundProps {
  children?: React.ReactNode;
  className?: string;
  enableClickInteraction?: boolean;
  tubeColors?: string[];
  lightColors?: string[];
  lightIntensity?: number;
}

const randomColors = (count: number): string[] =>
  Array.from({ length: count }, () =>
    '#' + Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0')
  );

const SEMANTIS_TUBE_COLORS = ['#3b82f6', '#8b5cf6', '#2563eb'];
const SEMANTIS_LIGHT_COLORS = ['#60a5fa', '#a78bfa', '#3b82f6', '#7c3aed'];

export function TubesBackground({
  children,
  className,
  enableClickInteraction = true,
  tubeColors = SEMANTIS_TUBE_COLORS,
  lightColors = SEMANTIS_LIGHT_COLORS,
  lightIntensity = 200,
}: TubesBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const tubesRef = useRef<any>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    let mounted = true;

    const initTubes = async () => {
      if (!canvasRef.current) return;

      try {
        // @ts-ignore — CDN ES module, not typed
        const module = await import(
          /* @vite-ignore */
          'https://cdn.jsdelivr.net/npm/threejs-components@0.0.19/build/cursors/tubes1.min.js'
        );
        const TubesCursor = module.default;

        if (!mounted) return;

        const app = TubesCursor(canvasRef.current, {
          tubes: {
            colors: tubeColors,
            lights: {
              intensity: lightIntensity,
              colors: lightColors,
            },
          },
        });

        tubesRef.current = app;
        setIsLoaded(true);
      } catch (error) {
        console.error('Failed to load TubesCursor:', error);
      }
    };

    initTubes();

    return () => {
      mounted = false;
      tubesRef.current = null;
    };
  }, []);

  const handleClick = useCallback(() => {
    if (!enableClickInteraction || !tubesRef.current) return;
    tubesRef.current.tubes.setColors(randomColors(3));
    tubesRef.current.tubes.setLightsColors(randomColors(4));
  }, [enableClickInteraction]);

  return (
    <div
      className={`relative w-full h-full min-h-[400px] overflow-hidden bg-surface ${className || ''}`}
      onClick={handleClick}
    >
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full block"
        style={{ touchAction: 'none' }}
      />

      {/* Subtle vignette overlay for depth */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse at center, transparent 40%, rgba(10,10,11,0.5) 100%)',
        }}
      />

      {/* Fade transition while loading */}
      <div
        className="absolute inset-0 bg-surface transition-opacity duration-1000 pointer-events-none"
        style={{ opacity: isLoaded ? 0 : 1 }}
      />

      {/* Content overlay */}
      <div className="relative z-10 w-full h-full pointer-events-none">
        {children}
      </div>
    </div>
  );
}

export default TubesBackground;
