import React from 'react';

interface LogoSgopiProps {
  size?: number | string;
  className?: string;
  color?: string;
}

export const LogoSgopi: React.FC<LogoSgopiProps> = ({
  size = 40,
  className = '',
  color = 'currentColor'
}) => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 500 500"
      width={size}
      height={size}
      className={`logo-sgopi ${className}`}
      style={{ color }}
      aria-label="Logo SGOPI Sentinela"
    >
      <defs>
        <path id="logo-text-curve" d="M 85,215 Q 250,75 415,215" fill="none" />
        <mask id="logo-badge-cutout">
          <rect width="100%" height="100%" fill="#ffffff" />
          <circle cx="250" cy="305" r="115" fill="#000000" />
          <text
            fill="#000000"
            fontSize="62"
            fontFamily="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
            fontWeight="900"
            letterSpacing="14"
          >
            <textPath href="#logo-text-curve" startOffset="50%" textAnchor="middle">
              SGOPI
            </textPath>
          </text>
        </mask>
      </defs>

      <g fill="currentColor">
        <path
          mask="url(#logo-badge-cutout)"
          d="M 250,22 
             C 285,55 330,75 375,75 
             C 415,75 448,58 465,42 
             C 445,105 465,155 480,180 
             C 430,205 422,255 422,305 
             C 422,390 350,448 250,495 
             C 150,448 78,390 78,305 
             C 78,255 70,205 20,180 
             C 35,155 55,105 35,42 
             C 52,58 85,75 125,75 
             C 170,75 215,55 250,22 Z"
        />
        <polygon
          points="250,220 
                  275,272 
                  332,280 
                  291,320 
                  301,377 
                  250,350 
                  199,377 
                  209,320 
                  168,280 
                  225,272"
        />
      </g>
    </svg>
  );
};
