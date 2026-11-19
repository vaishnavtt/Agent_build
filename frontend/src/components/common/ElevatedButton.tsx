import React, { useState, useRef, useCallback } from 'react';
import { Loader2, Check } from 'lucide-react';

export type ElevatedButtonVariant =
  | 'primary'
  | 'secondary'
  | 'destructive'
  | 'success'
  | 'glass'
  | 'ghost';

export type ElevatedButtonSize = 'sm' | 'md' | 'lg';

export interface ElevatedButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ElevatedButtonVariant;
  size?: ElevatedButtonSize;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  loading?: boolean;
  loadingText?: string;
  success?: boolean;
  successText?: string;
  glow?: boolean;
  elevatedDepth?: 'subtle' | 'medium' | 'deep';
  className?: string;
  children: React.ReactNode;
}

interface Ripple {
  id: number;
  x: number;
  y: number;
  size: number;
}

export const ElevatedButton: React.FC<ElevatedButtonProps> = ({
  variant = 'primary',
  size = 'md',
  icon,
  iconPosition = 'left',
  loading = false,
  loadingText,
  success = false,
  successText,
  glow = false,
  elevatedDepth = 'medium',
  className = '',
  disabled = false,
  onClick,
  children,
  ...props
}) => {
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [ripples, setRipples] = useState<Ripple[]>([]);
  const [mousePos, setMousePos] = useState<{ x: number; y: number } | null>(null);

  // Mouse move for dynamic surface reflection highlight that follows the cursor
  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLButtonElement>) => {
      if (disabled || loading) return;
      const rect = e.currentTarget.getBoundingClientRect();
      setMousePos({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      });
    },
    [disabled, loading]
  );

  const handleMouseLeave = useCallback(() => {
    setMousePos(null);
  }, []);

  // Click handler with ripple effect
  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLButtonElement>) => {
      if (disabled || loading) return;

      const rect = e.currentTarget.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const clickY = e.clientY - rect.top;
      const rippleSize = Math.max(rect.width, rect.height) * 2.2;

      const newRipple: Ripple = {
        id: Date.now() + Math.random(),
        x: clickX,
        y: clickY,
        size: rippleSize,
      };

      setRipples((prev) => [...prev, newRipple]);

      setTimeout(() => {
        setRipples((prev) => prev.filter((r) => r.id !== newRipple.id));
      }, 600);

      if (onClick) {
        onClick(e);
      }
    },
    [disabled, loading, onClick]
  );

  // Sizing definitions with comfortable touch targets
  const sizeClasses = {
    sm: 'px-3.5 py-1.5 text-xs gap-1.5 rounded-full min-h-[32px]',
    md: 'px-5 py-2.5 text-xs sm:text-sm gap-2 rounded-full min-h-[42px]',
    lg: 'px-7 py-3.5 text-sm sm:text-base gap-2.5 rounded-full min-h-[50px]',
  }[size];

  // 3D Depth & Bottom Bevel Lip Styles
  // Real tactile 3D: raised default, hover lifts -2px with deeper shadow, active presses +2px with compressed lip
  const depthStyles = {
    subtle: {
      primary:
        'shadow-[0_2px_0_#8B431B,0_4px_10px_rgba(177,95,44,0.3)] hover:shadow-[0_4px_0_#8B431B,0_8px_16px_rgba(177,95,44,0.4)] active:shadow-[0_1px_0_#8B431B,0_2px_4px_rgba(177,95,44,0.3)]',
      secondary:
        'shadow-[0_2px_0_#DCD8D3,0_3px_8px_rgba(0,0,0,0.04)] hover:shadow-[0_4px_0_#DCD8D3,0_6px_14px_rgba(0,0,0,0.08)] active:shadow-[0_1px_0_#DCD8D3,0_2px_3px_rgba(0,0,0,0.03)]',
      destructive:
        'shadow-[0_2px_0_#991B1B,0_4px_10px_rgba(220,38,38,0.3)] hover:shadow-[0_4px_0_#991B1B,0_8px_16px_rgba(220,38,38,0.4)] active:shadow-[0_1px_0_#991B1B,0_2px_4px_rgba(220,38,38,0.3)]',
      success:
        'shadow-[0_2px_0_#065F46,0_4px_10px_rgba(16,185,129,0.3)] hover:shadow-[0_4px_0_#065F46,0_8px_16px_rgba(16,185,129,0.4)] active:shadow-[0_1px_0_#065F46,0_2px_4px_rgba(16,185,129,0.3)]',
      glass:
        'shadow-[0_2px_0_#EAE8E5,0_4px_12px_rgba(0,0,0,0.03)] hover:shadow-[0_4px_0_#EAE8E5,0_8px_18px_rgba(0,0,0,0.06)] active:shadow-[0_1px_0_#EAE8E5,0_2px_4px_rgba(0,0,0,0.03)]',
      ghost:
        'hover:shadow-[0_2px_8px_rgba(0,0,0,0.04)]',
    },
    medium: {
      primary:
        'shadow-[0_3.5px_0_#7F3B15,0_6px_16px_rgba(177,95,44,0.38)] hover:shadow-[0_5.5px_0_#7F3B15,0_12px_24px_rgba(177,95,44,0.48)] active:shadow-[0_1px_0_#7F3B15,0_2px_6px_rgba(177,95,44,0.25)]',
      secondary:
        'shadow-[0_3px_0_#D8D4CE,0_4px_12px_rgba(0,0,0,0.05)] hover:shadow-[0_5px_0_#D8D4CE,0_8px_20px_rgba(0,0,0,0.09)] active:shadow-[0_1px_0_#D8D4CE,0_2px_4px_rgba(0,0,0,0.04)]',
      destructive:
        'shadow-[0_3.5px_0_#991B1B,0_6px_16px_rgba(220,38,38,0.35)] hover:shadow-[0_5.5px_0_#991B1B,0_12px_22px_rgba(220,38,38,0.45)] active:shadow-[0_1px_0_#991B1B,0_2px_5px_rgba(220,38,38,0.25)]',
      success:
        'shadow-[0_3.5px_0_#065F46,0_6px_16px_rgba(16,185,129,0.35)] hover:shadow-[0_5.5px_0_#065F46,0_12px_22px_rgba(16,185,129,0.45)] active:shadow-[0_1px_0_#065F46,0_2px_5px_rgba(16,185,129,0.25)]',
      glass:
        'shadow-[0_3px_0_#E5E2DC,0_6px_16px_rgba(0,0,0,0.04)] hover:shadow-[0_5px_0_#E5E2DC,0_10px_24px_rgba(0,0,0,0.08)] active:shadow-[0_1px_0_#E5E2DC,0_2px_5px_rgba(0,0,0,0.03)]',
      ghost:
        'hover:shadow-[0_3px_10px_rgba(0,0,0,0.05)]',
    },
    deep: {
      primary:
        'shadow-[0_5px_0_#743310,0_10px_24px_rgba(177,95,44,0.45)] hover:shadow-[0_7px_0_#743310,0_16px_32px_rgba(177,95,44,0.55)] active:shadow-[0_1.5px_0_#743310,0_3px_8px_rgba(177,95,44,0.3)]',
      secondary:
        'shadow-[0_4px_0_#D4CFCE,0_6px_18px_rgba(0,0,0,0.06)] hover:shadow-[0_6.5px_0_#D4CFCE,0_12px_26px_rgba(0,0,0,0.11)] active:shadow-[0_1.5px_0_#D4CFCE,0_3px_6px_rgba(0,0,0,0.04)]',
      destructive:
        'shadow-[0_5px_0_#7F1D1D,0_10px_24px_rgba(220,38,38,0.45)] hover:shadow-[0_7px_0_#7F1D1D,0_16px_30px_rgba(220,38,38,0.55)] active:shadow-[0_1.5px_0_#7F1D1D,0_3px_8px_rgba(220,38,38,0.3)]',
      success:
        'shadow-[0_5px_0_#064E3B,0_10px_24px_rgba(16,185,129,0.45)] hover:shadow-[0_7px_0_#064E3B,0_16px_30px_rgba(16,185,129,0.55)] active:shadow-[0_1.5px_0_#064E3B,0_3px_8px_rgba(16,185,129,0.3)]',
      glass:
        'shadow-[0_4px_0_#DEDAD4,0_8px_20px_rgba(0,0,0,0.05)] hover:shadow-[0_6.5px_0_#DEDAD4,0_14px_30px_rgba(0,0,0,0.09)] active:shadow-[0_1.5px_0_#DEDAD4,0_3px_7px_rgba(0,0,0,0.04)]',
      ghost:
        'hover:shadow-[0_4px_14px_rgba(0,0,0,0.06)]',
    },
  }[elevatedDepth];

  // Colors & Gradients
  const variantClasses = {
    primary:
      `bg-gradient-to-b from-[#C46B34] via-[#B15F2C] to-[#984D20] text-white border border-[#E08A52]/40 ${depthStyles.primary}`,
    secondary:
      `bg-gradient-to-b from-[#FFFFFF] via-[#FAF9F7] to-[#F1EFEA] text-[#111111] border border-[#EAE8E5] ${depthStyles.secondary}`,
    destructive:
      `bg-gradient-to-b from-[#EF4444] via-[#DC2626] to-[#B91C1C] text-white border border-rose-300/40 ${depthStyles.destructive}`,
    success:
      `bg-gradient-to-b from-[#10B981] via-[#059669] to-[#047857] text-white border border-emerald-300/40 ${depthStyles.success}`,
    glass:
      `backdrop-blur-md bg-white/90 text-[#111111] border border-white/80 ${depthStyles.glass}`,
    ghost:
      'bg-transparent hover:bg-[#F7F6F4] text-[#111111] border border-transparent hover:border-[#EAE8E5]',
  }[variant];

  // Specular top highlight bevel
  const topBevel =
    variant === 'secondary' || variant === 'glass'
      ? 'border-white/95'
      : 'border-white/35';

  return (
    <button
      ref={buttonRef}
      disabled={disabled || loading}
      onClick={handleClick}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`relative inline-flex items-center justify-center font-bold tracking-tight select-none overflow-hidden transition-all duration-150 ease-out focus:outline-none focus-visible:ring-2 focus-visible:ring-[#B15F2C] focus-visible:ring-offset-2 ${
        disabled
          ? 'opacity-40 cursor-not-allowed shadow-none translate-y-0'
          : 'hover:-translate-y-[2px] active:translate-y-[2px] cursor-pointer'
      } ${
        glow && variant === 'primary' && !disabled
          ? 'ring-2 ring-[#B15F2C]/30 animate-pulse'
          : ''
      } ${sizeClasses} ${variantClasses} ${className}`}
      {...props}
    >
      {/* 1. Specular Top Rim Highlight (Simulates physical rounded glass top) */}
      <span
        aria-hidden="true"
        className={`pointer-events-none absolute inset-x-3 top-0 h-[1.5px] rounded-full border-t ${topBevel} opacity-90`}
      />

      {/* 2. Interactive Cursor Refraction Follower */}
      {mousePos && !disabled && !loading && (
        <span
          aria-hidden="true"
          className="pointer-events-none absolute -inset-px rounded-full opacity-60 transition-opacity duration-200"
          style={{
            background: `radial-gradient(circle 50px at ${mousePos.x}px ${mousePos.y}px, rgba(255, 255, 255, ${
              variant === 'secondary' || variant === 'glass' ? '0.35' : '0.28'
            }), transparent 70%)`,
          }}
        />
      )}

      {/* 3. Concentric Tactile Ripples */}
      {ripples.map((r) => (
        <span
          key={r.id}
          aria-hidden="true"
          className="pointer-events-none absolute rounded-full animate-liquid-ripple"
          style={{
            left: r.x,
            top: r.y,
            width: r.size,
            height: r.size,
            background:
              variant === 'secondary' || variant === 'glass'
                ? 'radial-gradient(circle, rgba(177, 95, 44, 0.25) 15%, transparent 60%)'
                : 'radial-gradient(circle, rgba(255, 255, 255, 0.45) 15%, transparent 60%)',
          }}
        />
      ))}

      {/* 4. Content Area with Icons & State Animations */}
      <span className="relative z-10 flex items-center justify-center gap-2">
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin flex-shrink-0" />
            <span>{loadingText || 'Working on it...'}</span>
          </>
        ) : success ? (
          <>
            <Check className="w-4 h-4 text-emerald-400 animate-bounce flex-shrink-0" />
            <span>{successText || 'Completed!'}</span>
          </>
        ) : (
          <>
            {icon && iconPosition === 'left' && (
              <span className="flex-shrink-0 transition-transform group-hover:scale-110">
                {icon}
              </span>
            )}
            <span className="truncate">{children}</span>
            {icon && iconPosition === 'right' && (
              <span className="flex-shrink-0 transition-transform group-hover:translate-x-0.5">
                {icon}
              </span>
            )}
          </>
        )}
      </span>
    </button>
  );
};
