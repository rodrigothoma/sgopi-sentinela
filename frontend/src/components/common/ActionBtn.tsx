import React from 'react';
import './ActionBtn.css';

export interface ActionBtnProps {
  label: string;
  icon?: React.ReactNode;
  variant?: 'primary' | 'ghost' | 'outline' | 'secondary';
  size?: 'sm' | 'md';
  width?: string | number;
  disabled?: boolean;
  loading?: boolean;
  title?: string;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  className?: string;
  style?: React.CSSProperties;
}

export const ActionBtn: React.FC<ActionBtnProps> = ({
  label,
  icon,
  variant = 'primary',
  size = 'sm',
  width = '145px',
  disabled = false,
  loading = false,
  title,
  onClick,
  className = '',
  style,
}) => {
  const widthStyle = typeof width === 'number' ? `${width}px` : width;

  return (
    <button
      type="button"
      className={`sgopi-action-btn sgopi-action-btn--${variant} sgopi-action-btn--${size} ${className}`}
      disabled={disabled || loading}
      title={title || label}
      onClick={onClick}
      style={{
        width: widthStyle,
        minWidth: widthStyle,
        maxWidth: widthStyle,
        ...style,
      }}
    >
      {icon && <span className="sgopi-action-btn__icon">{icon}</span>}
      <span className="sgopi-action-btn__label">{label}</span>
    </button>
  );
};

export default ActionBtn;
