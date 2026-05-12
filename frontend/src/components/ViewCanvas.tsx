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
          absolute top-0 
          left-generate-gap right-generate-gap"
          style={{ 
            height: topContext ? ('var(--cw)') : (0) ,
          }}
      >
        {topContext}
      </div>

      {/* Main Analysis Area (Fixed Boundary Constraints) */}
      <div
        className="
          absolute 
          left-generate-gap right-generate-gap 
          no-scrollbar"
          style={{
            top: topContext ? ('var(--cw)') : (0) ,
            bottom: bottomContext ? ('var(--cw)') : (0) ,
          }}
      >
        {/* Conditionally render the default panel styling OR raw children */}
        {unstyledMain ? (
          children
        ) : (
          <div className="
            min-h-full  
            p-generate-pad">
            {children}
          </div>
        )}
      </div>

      {/*Optional Bottom Context Window */}
      <div
        className="
          absolute bottom-0 
          left-generate-gap right-generate-gap"
          style={{ 
            height: bottomContext ? ('var(--cw)') : (0) 
          }}
      >
        {bottomContext}
      </div>
    </div>
  );
}