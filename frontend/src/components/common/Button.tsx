import React from 'react';
import { Link } from 'react-router-dom';
import './Button.css';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
  loading?: boolean;
  fullWidth?: boolean;
  to?: string;
  className?: string;
  children?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  icon,
  iconRight,
  loading = false,
  fullWidth = false,
  to,
  disabled = false,
  className = '',
  children,
  ...props
}) => {
  const classes = [
    'button-ui',
    `button-ui--${variant}`,
    `button-ui--${size}`,
    fullWidth ? 'button-ui--full' : '',
    loading ? 'button-ui--loading' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  const content = (
    <>
      {loading ? (
        <span className="button-ui__spinner" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
            <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round" />
          </svg>
        </span>
      ) : icon ? (
        <span className="button-ui__icon" aria-hidden="true">
          {icon}
        </span>
      ) : null}

      {children && <span className="button-ui__text">{children}</span>}

      {!loading && iconRight && (
        <span className="button-ui__icon button-ui__icon--right" aria-hidden="true">
          {iconRight}
        </span>
      )}
    </>
  );

  if (to && !disabled && !loading) {
    return (
      <Link to={to} className={classes} role="button">
        {content}
      </Link>
    );
  }

  return (
    <button
      type={props.type || 'button'}
      disabled={disabled || loading}
      className={classes}
      {...props}
    >
      {content}
    </button>
  );
};

export default Button;
