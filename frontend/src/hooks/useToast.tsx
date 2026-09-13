import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';

type Tipo = 'sucesso' | 'erro' | 'info';
interface Toast { id: number; tipo: Tipo; texto: string }
interface ToastCtx { avisar: (texto: string, tipo?: Tipo) => void }

const Ctx = createContext<ToastCtx | null>(null);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const avisar = useCallback((texto: string, tipo: Tipo = 'info') => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, tipo, texto }]);
    window.setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 5000);
  }, []);
  const valor = useMemo(() => ({ avisar }), [avisar]);
  return (
    <Ctx.Provider value={valor}>
      {children}
      <div className="toasts" role="status" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`toast toast-${t.tipo}`}>{t.texto}</div>
        ))}
      </div>
    </Ctx.Provider>
  );
};

export function useToast(): ToastCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useToast fora do ToastProvider');
  return ctx;
}
