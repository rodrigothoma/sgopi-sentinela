import React, { useCallback, useEffect, useId, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

interface Pedido {
  mensagem: string;
  resolver: (confirmado: boolean) => void;
}

/**
 * Confirmação acessível no lugar de ``window.confirm`` (bloqueante, sem tema, sem i18n do botão):
 * ``role="alertdialog"`` com rótulo, foco inicial em "Cancelar" (ação destrutiva nunca é o padrão)
 * e Esc/clique fora cancelam.
 *
 * Uso: ``const [confirmar, dialogo] = useConfirmacao();`` → ``if (!(await confirmar(texto))) return;``
 * e renderizar ``{dialogo}`` na página.
 */
export function useConfirmacao(): [(mensagem: string) => Promise<boolean>, React.ReactNode] {
  const [pedido, setPedido] = useState<Pedido | null>(null);
  const confirmar = useCallback(
    (mensagem: string) => new Promise<boolean>((resolver) => setPedido({ mensagem, resolver })),
    [],
  );
  const responder = useCallback(
    (confirmado: boolean) => {
      pedido?.resolver(confirmado);
      setPedido(null);
    },
    [pedido],
  );
  const dialogo = pedido ? <ConfirmDialog mensagem={pedido.mensagem} onResponder={responder} /> : null;
  return [confirmar, dialogo];
}

const ConfirmDialog: React.FC<{ mensagem: string; onResponder: (confirmado: boolean) => void }> = ({ mensagem, onResponder }) => {
  const { t } = useTranslation();
  const idTexto = useId();
  const cancelarRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    cancelarRef.current?.focus();
    const aoTeclar = (e: KeyboardEvent) => e.key === 'Escape' && onResponder(false);
    window.addEventListener('keydown', aoTeclar);
    return () => window.removeEventListener('keydown', aoTeclar);
  }, [onResponder]);

  return (
    <div className="modal-backdrop" onClick={() => onResponder(false)}>
      <div
        className="modal-box"
        role="alertdialog"
        aria-modal="true"
        aria-describedby={idTexto}
        style={{ maxWidth: 440 }}
        onClick={(e) => e.stopPropagation()}
      >
        <p id={idTexto} style={{ marginTop: 0 }}>{mensagem}</p>
        <div className="acoes" style={{ justifyContent: 'flex-end' }}>
          <button ref={cancelarRef} type="button" className="btn btn-outline" onClick={() => onResponder(false)}>
            {t('actions.cancel')}
          </button>
          <button type="button" className="btn btn-danger" onClick={() => onResponder(true)}>
            {t('actions.confirmar')}
          </button>
        </div>
      </div>
    </div>
  );
};
