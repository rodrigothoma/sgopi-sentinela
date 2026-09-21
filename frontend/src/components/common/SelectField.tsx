import React, { useId } from 'react';
import './SelectField.css';

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectFieldProps {
  /** Label visível acima do select */
  label?: string;
  /** Opções do menu */
  options: SelectOption[];
  /** Valor selecionado (controlled) */
  value: string;
  /** Callback ao selecionar */
  onChange: (value: string) => void;
  /** Texto quando nenhum valor selecionado */
  placeholder?: string;
  /** Desabilitar o campo */
  disabled?: boolean;
  /** Mensagem de erro abaixo do campo */
  error?: string;
  /** Texto auxiliar abaixo do campo (não mostrado quando há erro) */
  hint?: string;
  /** Torna o campo obrigatório */
  required?: boolean;
  /** Classes extras no wrapper */
  className?: string;
  /** Tamanho: "sm" | "md" (default) | "lg" */
  size?: 'sm' | 'md' | 'lg';
  /** id do select (gerado automaticamente se omitido) */
  id?: string;
  /** aria-label quando não houver label visual */
  'aria-label'?: string;
}

/**
 * SelectField — select estilizado para todo o projeto.
 *
 * Uso:
 * ```tsx
 * <SelectField
 *   label="Natureza da Ocorrência"
 *   options={naturezas}
 *   value={natureza}
 *   onChange={setNatureza}
 *   placeholder="Selecione..."
 * />
 * ```
 */
export const SelectField: React.FC<SelectFieldProps> = ({
  label,
  options,
  value,
  onChange,
  placeholder,
  disabled = false,
  error,
  hint,
  required = false,
  className = '',
  size = 'md',
  id: externalId,
  'aria-label': ariaLabel,
}) => {
  const autoId = useId();
  const id = externalId ?? autoId;
  const descId = `${id}-desc`;
  const hasDesc = !!(error ?? hint);

  return (
    <div
      className={[
        'select-field',
        `select-field--${size}`,
        error ? 'select-field--error' : '',
        disabled ? 'select-field--disabled' : '',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {label && (
        <label htmlFor={id} className="select-field__label">
          {label}
          {required && (
            <span className="select-field__required" aria-hidden="true">
              {' *'}
            </span>
          )}
        </label>
      )}

      <div className="select-field__wrapper">
        <select
          id={id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          required={required}
          aria-label={ariaLabel}
          aria-describedby={hasDesc ? descId : undefined}
          aria-invalid={error ? 'true' : undefined}
          className="select-field__select"
        >
          {placeholder && (
            <option value="" disabled hidden>
              {placeholder}
            </option>
          )}
          {options.map((opt) => (
            <option key={opt.value} value={opt.value} disabled={opt.disabled}>
              {opt.label}
            </option>
          ))}
        </select>

        {/* seta customizada */}
        <span className="select-field__arrow" aria-hidden="true">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 16 16"
            width="14"
            height="14"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="4 6 8 10 12 6" />
          </svg>
        </span>
      </div>

      {hasDesc && (
        <p id={descId} className={error ? 'select-field__error' : 'select-field__hint'}>
          {error ?? hint}
        </p>
      )}
    </div>
  );
};

export default SelectField;
