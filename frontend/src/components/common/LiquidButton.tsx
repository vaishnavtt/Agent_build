import React, { useState, useRef, useCallback } from 'react';
import { Loader2 } from 'lucide-react';

export type LiquidButtonVariant = 'primary' | 'secondary' | 'destructive' | 'success' | 'glass';
export type LiquidButtonSize = 'sm' | 'md' | 'lg';

export interface LiquidButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: LiquidButtonVariant;
  size?: LiquidButtonSize;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  loading?: boolean;
  loadingText?: string;
  className?: string;
  glow?: boolean;
  children: React.ReactNode;
}

interface Ripple {
  id: number;
  x: number;
  y: number;
  size: number;
}

export const LiquidButton: React.FC<LiquidButtonProps> = ({
  variant = 'primary',
  size = 'md',
  icon,
  iconPosition = 'left',
  loading = false,
  loadingText,
  className = '',
  glow = false,
  disabled = false,
  onClick,
  children,
  ...props
}) => {
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [ripples, setRipples] = useState<Ripple[]>([]);
  const [mousePos, setMousePos] = useState<{ x: number; y: number } | null>(null);

  // Mouse move for dynamic glass specular refraction highlight
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled || loading) return;
    const rect = e.currentTarget.getBoundingClientRect();
    setMousePos({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  }, [disabled, loading]);

  const handleMouseLeave = useCallback(() => {
    setMousePos(null);
  }, []);

  // Liquid ripple physics on impact/click
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
      }, 650);

      if (onClick) {
        onClick(e);
      }
    },
    [disabled, loading, onClick]
  );

  // Size styling
  const sizeClasses = {
    sm: 'px-3.5 py-1.5 text-xs gap-1.5 rounded-full',
    md: 'px-5 py-2.5 text-xs sm:text-sm gap-2 rounded-full',
    lg: 'px-6 py-3.5 text-sm sm:text-base gap-2.5 rounded-full',
  }[size];

  // Variant styling matching Lumora light theme + liquid glass lozenges
  const variantClasses = {
    primary:
      'bg-gradient-to-b from-[#B15F2C] to-[#984D20] text-white shadow-[0_4px_14px_-2px_rgba(177,95,44,0.4),0_1px_2px_rgba(0,0,0,0.1)] hover:shadow-[0_8px_22px_-2px_rgba(177,95,44,0.55),0_2px_4px_rgba(0,0,0,0.15)] hover:from-[#CF8047] hover:to-[#B15F2C] border border-[#CF8047]/40',
    secondary:
      'bg-gradient-to-b from-[#FFFFFF] to-[#F1F0EE] text-[#111111] shadow-[0_2px_8px_rgba(0,0,0,0.04)] hover:shadow-[0_6px_16px_rgba(0,0,0,0.08)] hover:from-[#FFFFFF] hover:to-[#E3E2DF] border border-[#E6E5E2]',
    destructive:
      'bg-gradient-to-b from-[#DC2626] to-[#B91C1C] text-white shadow-[0_4px_14px_-2px_rgba(220,38,38,0.4)] hover:shadow-[0_8px_20px_-2px_rgba(220,38,38,0.55)] hover:from-[#EF4444] hover:to-[#DC2626] border border-rose-400/40',
    success:
      'bg-gradient-to-b from-[#059669] to-[#047857] text-white shadow-[0_4px_14px_-2px_rgba(5,150,105,0.4)] hover:shadow-[0_8px_20px_-2px_rgba(5,150,105,0.55)] hover:from-[#10B981] hover:to-[#059669] border border-emerald-400/40',
    glass:
      'backdrop-blur-md bg-white/80 text-[#111111] shadow-[0_4px_16px_rgba(0,0,0,0.05)] hover:shadow-[0_8px_24px_rgba(0,0,0,0.08)] hover:bg-white/95 border border-[#E6E5E2]',
  }[variant];

  // Specular top bevel highlight based on variant
  const topBevelColor =
    variant === 'secondary' || variant === 'glass'
      ? 'border-white/90'
      : 'border-white/35';

  const rippleGradient =
    variant === 'secondary' || variant === 'glass'
      ? 'radial-gradient(circle, rgba(177, 95, 44, 0.3) 15%, transparent 35%, rgba(177, 95, 44, 0.18) 55%, transparent 75%)'
      : 'radial-gradient(circle, rgba(255, 255, 255, 0.5) 15%, transparent 35%, rgba(255, 255, 255, 0.3) 55%, transparent 75%)';

  return (
    <button
      ref={buttonRef}
      disabled={disabled || loading}
      onClick={handleClick}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`relative inline-flex items-center justify-center font-semibold select-none overflow-hidden transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#B15F2C] focus-visible:ring-offset-2 ${
        disabled
          ? 'opacity-45 cursor-not-allowed shadow-none'
          : 'hover:-translate-y-0.5 active:translate-y-0.5 active:scale-[0.98] cursor-pointer'
      } ${glow && variant === 'primary' && !disabled ? 'animate-[liquidGlowPulse_3s_infinite_ease-in-out]' : ''} ${sizeClasses} ${variantClasses} ${className}`}
      {...props}
    >
      {/* 1. Sharp Bevel Specular Top Highlight (Glass Lozenge Rim) */}
      <span
        aria-hidden="true"
        className={`pointer-events-none absolute inset-x-2 top-0 h-[1.5px] rounded-full border-t ${topBevelColor} opacity-90`}
      />

      {/* 2. Interactive Liquid Cursor Refraction Follower */}
      {mousePos && !disabled && !loading && (
        <span
          aria-hidden="true"
          className="pointer-events-none absolute -inset-px rounded-full opacity-60 transition-opacity duration-300"
          style={{
            background: `radial-gradient(circle 50px at ${mousePos.x}px ${mousePos.y}px, rgba(255, 255, 255, ${
              variant === 'secondary' || variant === 'glass' ? '0.35' : '0.28'
            }), transparent 70%)`,
          }}
        />
      )}

      {/* 3. Liquid Shimmer / Wave for Loading State */}
      {loading && (
        <span
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 w-full h-full animate-liquid-shimmer bg-gradient-to-r from-transparent via-white/25 to-transparent"
        />
      )}

      {/* 4. Fluid Waves (Concentric Impact Ripples on Click) */}
      {ripples.map((ripple) => (
        <span
          key={ripple.id}
          aria-hidden="true"
          className="pointer-events-none absolute rounded-full animate-liquid-ripple blur-[0.5px]"
          style={{
            left: `${ripple.x}px`,
            top: `${ripple.y}px`,
            width: `${ripple.size}px`,
            height: `${ripple.size}px`,
            background: rippleGradient,
          }}
        />
      ))}

      {/* 5. Button Content & Icons */}
      <span className="relative z-10 flex items-center justify-center gap-2 font-medium">
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin text-current" />
            <span>{loadingText || children}</span>
          </>
        ) : (
          <>
            {icon && iconPosition === 'left' && <span className="flex-shrink-0">{icon}</span>}
            <span>{children}</span>
            {icon && iconPosition === 'right' && <span className="flex-shrink-0">{icon}</span>}
          </>
        )}
      </span>
    </button>
  );
};
