import React, { useEffect, useId, useMemo, useRef, useState } from 'react';
import './GlideSelect.css';

export interface GlideSelectOption {
  value: string;
  label: string;
  tag?: string;
  icon?: React.ReactNode;
  disabled?: boolean;
}

export interface GlideSelectProps {
  options: GlideSelectOption[];
  value?: string;
  defaultValue?: string;
  onChange?: (value: string, option?: GlideSelectOption) => void;
  ariaLabel?: string;
  showTags?: boolean;
  accentColor?: string;
  surfaceColor?: string;
  highlightColor?: string;
  textColor?: string;
  size?: 'sm' | 'md' | 'lg';
  radius?: number;
  menuWidth?: number | string;
  placement?: 'bottom' | 'top';
  align?: 'left' | 'right';
  popDuration?: number;
  glideDuration?: number;
  rememberPosition?: boolean;
  className?: string;
  disabled?: boolean;
  placeholder?: string;
}

export const GlideSelect: React.FC<GlideSelectProps> = ({
  options = [],
  value: controlledValue,
  defaultValue,
  onChange,
  ariaLabel = 'Select option',
  showTags = false,
  accentColor,
  surfaceColor,
  highlightColor,
  textColor,
  size = 'md',
  radius = 8,
  menuWidth,
  placement = 'bottom',
  align = 'left',
  popDuration = 180,
  glideDuration = 220,
  rememberPosition = true,
  className = '',
  disabled = false,
  placeholder = 'Selecione...',
}) => {
  const isControlled = controlledValue !== undefined;
  const [internalValue, setInternalValue] = useState<string>(() => {
    if (isControlled) return controlledValue || '';
    if (defaultValue !== undefined) return defaultValue;
    return options[0]?.value || '';
  });

  const selectedValue = isControlled ? controlledValue : internalValue;
  const [isOpen, setIsOpen] = useState(false);
  const [highlightIdx, setHighlightIdx] = useState<number>(-1);
  const [pillStyle, setPillStyle] = useState<React.CSSProperties>({ opacity: 0 });

  const containerRef = useRef<HTMLDivElement | null>(null);
  const menuRef = useRef<HTMLDivElement | null>(null);
  const itemRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const id = useId();

  const selectedOption = useMemo(
    () => options.find((opt) => opt.value === selectedValue) || options[0],
    [options, selectedValue]
  );

  const selectedIndex = useMemo(
    () => options.findIndex((opt) => opt.value === selectedValue),
    [options, selectedValue]
  );

  // Fecha ao clicar fora
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  // Atualiza posição do pill deslizante quando highlightIdx muda
  useEffect(() => {
    if (!isOpen) {
      setPillStyle({ opacity: 0 });
      return;
    }

    const targetIdx = highlightIdx >= 0 ? highlightIdx : selectedIndex;
    const targetEl = itemRefs.current[targetIdx];

    if (targetEl) {
      setPillStyle({
        transform: `translateY(${targetEl.offsetTop}px)`,
        height: `${targetEl.offsetHeight}px`,
        opacity: 1,
        transition: `transform ${glideDuration}ms cubic-bezier(0.2, 0.8, 0.2, 1), height ${glideDuration}ms ease, opacity 120ms ease`,
      });
    } else {
      setPillStyle({ opacity: 0 });
    }
  }, [highlightIdx, selectedIndex, isOpen, glideDuration]);

  // Abre menu e foca a posição
  const toggleOpen = () => {
    if (disabled) return;
    setIsOpen((prev) => {
      const next = !prev;
      if (next) {
        setHighlightIdx(rememberPosition && selectedIndex >= 0 ? selectedIndex : 0);
      }
      return next;
    });
  };

  const handleSelect = (option: GlideSelectOption) => {
    if (option.disabled) return;
    if (!isControlled) {
      setInternalValue(option.value);
    }
    onChange?.(option.value, option);
    setIsOpen(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return;

    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        setIsOpen(true);
        setHighlightIdx(selectedIndex >= 0 ? selectedIndex : 0);
      }
      return;
    }

    if (e.key === 'Escape') {
      e.preventDefault();
      setIsOpen(false);
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightIdx((prev) => {
        let next = prev + 1;
        while (next < options.length && options[next]?.disabled) {
          next++;
        }
        return next < options.length ? next : prev;
      });
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightIdx((prev) => {
        let next = prev - 1;
        while (next >= 0 && options[next]?.disabled) {
          next--;
        }
        return next >= 0 ? next : prev;
      });
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      const currentOpt = options[highlightIdx];
      if (currentOpt && !currentOpt.disabled) {
        handleSelect(currentOpt);
      }
    }
  };

  const cssVariables: React.CSSProperties = {
    ['--glide-radius' as string]: `${radius}px`,
    ['--glide-pop-duration' as string]: `${popDuration}ms`,
    ['--glide-glide-duration' as string]: `${glideDuration}ms`,
    ...(accentColor ? { ['--glide-accent' as string]: accentColor } : {}),
    ...(surfaceColor ? { ['--glide-surface' as string]: surfaceColor } : {}),
    ...(highlightColor ? { ['--glide-highlight' as string]: highlightColor } : {}),
    ...(textColor ? { ['--glide-text' as string]: textColor } : {}),
    ...(menuWidth ? { ['--glide-menu-width' as string]: typeof menuWidth === 'number' ? `${menuWidth}px` : menuWidth } : {}),
  };

  return (
    <div
      ref={containerRef}
      className={`glide-select-root glide-select--${size} ${isOpen ? 'glide-select--open' : ''} ${className}`.trim()}
      style={cssVariables}
      onKeyDown={handleKeyDown}
    >
      <button
        type="button"
        id={id}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={ariaLabel}
        disabled={disabled}
        onClick={toggleOpen}
        className="glide-select-trigger"
      >
        <span className="glide-select-trigger__content">
          {selectedOption?.icon && (
            <span className="glide-select-trigger__icon" aria-hidden="true">
              {selectedOption.icon}
            </span>
          )}
          <span className="glide-select-trigger__label">
            {selectedOption ? selectedOption.label : placeholder}
          </span>
          {showTags && selectedOption?.tag && (
            <span className="glide-select-tag">{selectedOption.tag}</span>
          )}
        </span>

        <span className="glide-select-trigger__chevron" aria-hidden="true">
          <svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="4 6 8 10 12 6" />
          </svg>
        </span>
      </button>

      {isOpen && (
        <div
          ref={menuRef}
          role="listbox"
          aria-labelledby={id}
          className={`glide-select-menu glide-select-menu--${placement} glide-select-menu--${align}`}
        >
          {/* O pill de destaque que desliza suavemente atrás dos itens */}
          <div className="glide-select-pill" style={pillStyle} aria-hidden="true" />

          {options.map((opt, idx) => {
            const isSelected = opt.value === selectedValue;
            const isHighlighted = idx === highlightIdx;

            return (
              <button
                key={opt.value}
                ref={(el) => (itemRefs.current[idx] = el)}
                type="button"
                role="option"
                aria-selected={isSelected}
                disabled={opt.disabled}
                tabIndex={-1}
                className={`glide-select-item ${isSelected ? 'glide-select-item--selected' : ''} ${isHighlighted ? 'glide-select-item--highlighted' : ''}`}
                onMouseEnter={() => setHighlightIdx(idx)}
                onClick={() => handleSelect(opt)}
              >
                {opt.icon && (
                  <span className="glide-select-item__icon" aria-hidden="true">
                    {opt.icon}
                  </span>
                )}
                <span className="glide-select-item__label">{opt.label}</span>
                {showTags && opt.tag && (
                  <span className="glide-select-tag glide-select-tag--item">{opt.tag}</span>
                )}
                {isSelected && (
                  <span className="glide-select-item__check" aria-hidden="true">
                    <svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2.2">
                      <polyline points="3 8 7 12 13 4" />
                    </svg>
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default GlideSelect;
