import React, { useEffect, useRef } from 'react';

export interface WebThreadsProps {
  color1?: string;
  color2?: string;
  color3?: string;
  speed?: number;
  threadCount?: number;
  frequency?: number;
  spread?: number;
  taper?: number;
  position?: number;
  fanMode?: 'center' | 'top' | 'bottom';
  glow?: number;
  falloff?: number;
  thickness?: number;
  brightness?: number;
  opacity?: number;
  mirror?: boolean;
  shimmer?: boolean;
  grain?: boolean;
  grainIntensity?: number;
  mouseInteraction?: boolean;
  mouseStrength?: number;
  className?: string;
  style?: React.CSSProperties;
}

export const WebThreads: React.FC<WebThreadsProps> = ({
  color1 = '#0515d3',
  color2 = '#0b4aaf',
  color3 = '#FFFFFF',
  speed = 0.2,
  threadCount = 6,
  frequency = 5.0,
  spread = 0.18,
  taper = 1.0,
  position = 0.5,
  fanMode = 'center',
  glow = 0.02,
  falloff = 0.6,
  thickness = 1.1,
  brightness = 0.6,
  opacity = 1.0,
  mirror = true,
  shimmer = false,
  grain = true,
  grainIntensity = 0.05,
  mouseInteraction = true,
  mouseStrength = 0.3,
  className = '',
  style = {},
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mouseRef = useRef({ x: 0, y: 0, targetX: 0, targetY: 0, active: false });

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = 0;
    let height = 0;
    let time = 0;

    // Grain buffer
    let grainCanvas: HTMLCanvasElement | null = null;
    let grainPattern: CanvasPattern | null = null;

    const initGrain = () => {
      if (!grain) return;
      grainCanvas = document.createElement('canvas');
      grainCanvas.width = 128;
      grainCanvas.height = 128;
      const gCtx = grainCanvas.getContext('2d');
      if (!gCtx) return;

      const imgData = gCtx.createImageData(128, 128);
      const data = imgData.data;
      for (let i = 0; i < data.length; i += 4) {
        const val = Math.floor(Math.random() * 255);
        data[i] = val;
        data[i + 1] = val;
        data[i + 2] = val;
        data[i + 3] = Math.floor(grainIntensity * 255);
      }
      gCtx.putImageData(imgData, 0, 0);
      grainPattern = ctx.createPattern(grainCanvas, 'repeat');
    };

    initGrain();

    const resize = () => {
      const rect = container.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = rect.width;
      height = rect.height;

      canvas.width = Math.max(width * dpr, 1);
      canvas.height = Math.max(height * dpr, 1);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;

      ctx.scale(dpr, dpr);
    };

    resize();
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(container);

    const handleMouseMove = (e: MouseEvent) => {
      if (!mouseInteraction) return;
      const rect = container.getBoundingClientRect();
      mouseRef.current.targetX = (e.clientX - rect.left) / width;
      mouseRef.current.targetY = (e.clientY - rect.top) / height;
      mouseRef.current.active = true;
    };

    const handleMouseLeave = () => {
      mouseRef.current.active = false;
    };

    container.addEventListener('mousemove', handleMouseMove);
    container.addEventListener('mouseleave', handleMouseLeave);

    const render = () => {
      time += speed * 0.02;

      // Mouse smooth interpolation
      mouseRef.current.x += (mouseRef.current.targetX - mouseRef.current.x) * 0.06;
      mouseRef.current.y += (mouseRef.current.targetY - mouseRef.current.y) * 0.06;

      ctx.clearRect(0, 0, width, height);

      const basePosY = height * position;
      const stepX = Math.max(width / 60, 4);

      ctx.save();
      ctx.globalAlpha = opacity;

      // Glow setting
      if (glow > 0) {
        ctx.shadowBlur = glow * 80;
        ctx.shadowColor = color2;
      }

      for (let i = 0; i < threadCount; i++) {
        const threadRatio = i / Math.max(threadCount - 1, 1);
        const offsetRatio = threadRatio - 0.5;

        // Fan distribution
        let fanOffset = 0;
        if (fanMode === 'center') {
          fanOffset = offsetRatio * spread * height;
        } else if (fanMode === 'top') {
          fanOffset = threadRatio * spread * height;
        } else if (fanMode === 'bottom') {
          fanOffset = -threadRatio * spread * height;
        }

        // Shimmer variation
        const shimmerVal = shimmer ? 0.7 + Math.sin(time * 2 + i) * 0.3 : 1;

        // Create thread gradient
        const gradient = ctx.createLinearGradient(0, 0, width, 0);
        gradient.addColorStop(0, color1);
        gradient.addColorStop(0.5, color2);
        gradient.addColorStop(1, color3);

        ctx.strokeStyle = gradient;
        ctx.lineWidth = thickness * (brightness * shimmerVal);
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        // Draw primary thread wave
        const drawWave = (dirMultiplier: number) => {
          ctx.beginPath();
          let firstPoint = true;

          for (let x = 0; x <= width; x += stepX) {
            const normX = x / width;

            // Tapering at edges
            const taperFactor = taper > 0 ? Math.sin(normX * Math.PI) ** taper : 1;

            // Multi-frequency wave calculation
            const wave1 = Math.sin(normX * frequency * Math.PI + time + i * 0.4) * 28;
            const wave2 = Math.cos(normX * frequency * 1.6 * Math.PI - time * 0.8 + i * 0.2) * 14;
            const wave3 = Math.sin(normX * frequency * 0.5 * Math.PI + time * 1.2) * 8;

            // Mouse repulsion/attraction
            let mouseDisp = 0;
            if (mouseInteraction && mouseRef.current.active) {
              const dx = normX - mouseRef.current.x;
              const dy = 0.5 - mouseRef.current.y;
              const dist = Math.sqrt(dx * dx + dy * dy);
              if (dist < 0.4) {
                mouseDisp = Math.sin((1 - dist / 0.4) * Math.PI) * mouseStrength * 60;
              }
            }

            const y =
              basePosY +
              (fanOffset + (wave1 + wave2 + wave3) * taperFactor * falloff + mouseDisp) *
                dirMultiplier;

            if (firstPoint) {
              ctx.moveTo(x, y);
              firstPoint = false;
            } else {
              ctx.lineTo(x, y);
            }
          }

          ctx.stroke();
        };

        drawWave(1);
        if (mirror) {
          drawWave(-1);
        }
      }

      // Render grain overlay if enabled
      if (grain && grainPattern) {
        ctx.save();
        ctx.globalAlpha = grainIntensity;
        ctx.fillStyle = grainPattern;
        ctx.fillRect(0, 0, width, height);
        ctx.restore();
      }

      ctx.restore();

      animationFrameId = requestAnimationFrame(render);
    };

    animationFrameId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animationFrameId);
      resizeObserver.disconnect();
      container.removeEventListener('mousemove', handleMouseMove);
      container.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, [
    color1,
    color2,
    color3,
    speed,
    threadCount,
    frequency,
    spread,
    taper,
    position,
    fanMode,
    glow,
    falloff,
    thickness,
    brightness,
    opacity,
    mirror,
    shimmer,
    grain,
    grainIntensity,
    mouseInteraction,
    mouseStrength,
  ]);

  return (
    <div
      ref={containerRef}
      className={`web-threads-container ${className}`.trim()}
      style={{
        width: '100%',
        height: '100%',
        position: 'absolute',
        top: 0,
        left: 0,
        overflow: 'hidden',
        pointerEvents: 'none',
        ...style,
      }}
      aria-hidden="true"
    >
      <canvas
        ref={canvasRef}
        style={{
          display: 'block',
          width: '100%',
          height: '100%',
        }}
      />
    </div>
  );
};

export default WebThreads;
