"use client";

import { ReactNode } from "react";

interface ViewCanvasProps {
  children: ReactNode;         // The main analysis area (e.g., the Table or Workbench)
  topContext?: ReactNode;      // Optional top context window
  bottomContext?: ReactNode;   // Optional bottom context window
  unstyledMain?: boolean;      // Optional flag to remove default background and padding
}

export default function ViewCanvas({ children, topContext, bottomContext, unstyledMain = false }: ViewCanvasProps) {
  return (
    <div className="w-full h-full relative">
      
      {/*Top Context Window */}
      <div 
        className="
          absolute top-0 left-dsi-gap right-dsi-gap 
          overflow-auto
          text-dsi-contrast-background"
        style={{ 
          height: 'var(--cw)'
        }}
      >
        {topContext}
      </div>

      {/* Main Analysis Area (Fixed Boundary Constraints) */}
      <div
        className="
          absolute left-dsi-gap right-dsi-gap 
          overflow-auto
          no-scrollbar"
        style={{
          top: 'var(--cw)' ,
          bottom: 'var(--cw)' ,
        }}
      >
        {/* Conditionally render the default panel styling OR raw children */}
        {unstyledMain ? (
          children
        ) : (
          <div className="
            bg-dsi-analysis 
            text-dsi-contrast-analysis 
            min-h-full 
            p-dsi-pad">
            {children}
          </div>
        )}
      </div>

      {/*Bottom Context Window */}
      <div
        className="
          absolute bottom-0 left-dsi-gap right-dsi-gap 
          overflow-auto 
          text-dsi-contrast-background"
        style={{ 
          height: 'var(--cw)' 
        }}
      >
        {bottomContext}
      </div>

    </div>
  );
}