import React from 'react';
import { ElevatedButton, ElevatedButtonProps } from './ElevatedButton';

export type LiquidButtonVariant = 'primary' | 'secondary' | 'destructive' | 'success' | 'glass';
export type LiquidButtonSize = 'sm' | 'md' | 'lg';

export interface LiquidButtonProps extends ElevatedButtonProps {}

/**
 * LiquidButton re-routes through the enhanced 3D ElevatedButton system
 * providing realistic depth, tactile spring response, specular cursor tracking, and ripple waves.
 */
export const LiquidButton: React.FC<LiquidButtonProps> = (props) => {
  return <ElevatedButton {...props} />;
};

export { ElevatedButton };
