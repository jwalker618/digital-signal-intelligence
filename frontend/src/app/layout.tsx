"use client";

import { useState, useRef, useEffect } from "react";
import { IBM_Plex_Sans, Inter } from "next/font/google";
import { 
  PanelRightClose, PanelRightOpen, Lightbulb, LightbulbOff, Bug, CircleUserRound, ArrowLeftToLine,
  Inbox, FileStack, Shield, FolderKanban, UserStar, Rows4, Bot
} from "lucide-react";

import { useDsiStore } from "@/store/dsiStore";
import "./globals.css";

// 1. Font Configuration
const ibmPlex = IBM_Plex_Sans({ 
  weight: ['400', '500', '600', '700'],
  subsets: ['latin'],
  variable: '--font-ibm'
});

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter'
});

// Helper component to stop repeating button code
const SidebarIconBtn = ({ icon: Icon, onClick, className, style }: { icon: any, onClick?: () => void, className: string, style?: any }) => (
  <button onClick={onClick} className={`absolute p-dsi-pad text-dsi-background hover:text-dsi-selected ${className}`} style={style}>
    <Icon className="icon" />
  </button>
);

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isDark, setIsDark] = useState(false);
  
  const [isSubmissionsExpanded, setIsSubmissionsExpanded] = useState(true);
  const { activeMenu, setActiveMenu, daysFilter, setDaysFilter, previousMenu, activeSubmission, navigateBack } = useDsiStore();

  const sidebarRef = useRef<HTMLDivElement>(null);
  const [collapsedWidthPx, setCollapsedWidthPx] = useState<number | null>(null);

  // Measure sidebar width perfectly based on the parent DOM
  useEffect(() => {
    if (!sidebarRef.current || !sidebarRef.current.parentElement) return;

    const measure = () => {
      // Get the true pixel width of the whole screen/parent container
      const parentWidth = sidebarRef.current?.parentElement?.getBoundingClientRect().width;
      
      // Mathematically lock the collapsed width to exactly 5% of the usable screen.
      // This stays completely stable during open/close animations!
      if (parentWidth) {
        setCollapsedWidthPx(parentWidth * 0.05);
      }
    };

    // Observe the parent container instead of the sidebar. 
    // It will only fire when the user physically resizes the browser window.
    const observer = new ResizeObserver(measure);
    if (sidebarRef.current?.parentElement) {
      observer.observe(sidebarRef.current.parentElement);
    }

    measure();

    return () => observer.disconnect();
  }, []); // Removed [isOpen] so it doesn't recalculate during the click transition

  useEffect(() => {
    const html = document.documentElement;
    if (isDark) html.classList.add("dark");
    else html.classList.remove("dark");
  }, [isDark]);

  return (
    <html lang="en" suppressHydrationWarning> 
      <body className={`${ibmPlex.variable} ${inter.variable} font-ibm h-screen w-screen overflow-hidden`}>

        <div className="flex h-full w-full">

          {/* SIDEBAR */}
          <aside
            ref={sidebarRef}
            className={`
              relative h-full shrink-0 transition-all duration-300
              bg-dsi-contrast-background 
              text-dsi-background
              border-r-3 border-dsi-outline
              ${isOpen ? "w-[50%]" : "w-[5%]"}
            `}
          >
            {isOpen && (
              <img
                src={isDark ? "/Standard_Generate_Logo_and_DSI.svg" : "/BlackWhite_Generate_Logo_and_DSI.svg"}
                className="
                  absolute top-dsi-pad left-dsi-pad 
                  h-12 w-auto 
                  object-contain"
                alt="DSI Logo"
              />
            )}

            <button
              onClick={() => setIsOpen(!isOpen)}
              className="
                absolute top-dsi-pad right-dsi-pad p-dsi-pad 
                text-dsi-background 
                hover:text-dsi-selected"
            >
              {isOpen ? <PanelRightOpen className="icon" /> : <PanelRightClose className="icon" />}
            </button>

            {/* NAVIGATION */}
            {isOpen && collapsedWidthPx && (
              <nav 
                className="
                  absolute left-10 right-0 
                  flex-grow py-dsi-pad 
                  overflow-y-auto 
                  overflow-x-hidden no-scrollbar"
                style={{ top: collapsedWidthPx }}
              >
                <div className="px-dsi-pad">
                  
                  {/* --- CONDITIONAL RENDERING --- */}
                  {activeSubmission ? (
                    
                    /* === DRILL-DOWN MODE === */
                    <>
                      <button 
                        onClick={navigateBack}
                        className="w-full flex items-center gap-3 py-2 text-dsi-background hover:text-dsi-selected mb-2 border-b-3 border-dsi-outline/20 pb-4"
                      >
                        <ArrowLeftToLine className="icon shrink-0" />
                        <span className="text-sm tracking-wider font-bold truncate">Back to {previousMenu}</span>
                      </button>
                      
                      <ul className="ml-3 pl-dsi-pad flex flex-col gap-1">
                        {[
                          { name: "Summary", icon: FolderKanban },
                          { name: "Referral Actions", icon: UserStar },
                          { name: "Model Versions", icon: FileStack },
                          { name: "Audit Log", icon: Shield }
                        ].map((item) => (
                          <li key={item.name}>
                            <button
                              onClick={() => setActiveMenu(item.name)}
                              className={`flex items-center gap-3 w-full text-left py-2 px-2 rounded text-sm ${
                                activeMenu === item.name 
                                  ? "text-dsi-contrast-background bg-dsi-background font-semibold" 
                                  : "text-dsi-background hover:text-dsi-selected"
                              }`}
                            >
                              <item.icon className="icon shrink-0" />
                              <span className="truncate">{item.name}</span>
                            </button>
                          </li>
                        ))}
                      </ul>
                    </>

                  ) : (

                    /* === TOP LEVEL MODE */
                    <>
                      <button 
                        onClick={() => setIsSubmissionsExpanded(!isSubmissionsExpanded)}
                        className="w-full flex items-center justify-between py-2 text-dsi-background hover:text-dsi-selected"
                      >
                        <div className="flex items-center gap-3">
                          <Inbox className="icon shrink-0" />
                          <span className="text-sm tracking-wider">Submissions</span>
                        </div>
                      </button>
                      
                      {isSubmissionsExpanded && (
                        <ul className="ml-3 pl-dsi-pad border-l-3 border-dsi-outline/20 mt-2 flex flex-col gap-1">
                          {[
                            { name: "Referral Pipeline", icon: UserStar },
                            { name: "Full Pipeline", icon: Rows4 },
                            { name: "Performance Metrics", icon: Bot }
                          ].map((item) => (
                            <li key={item.name}>
                              <button
                                onClick={() => setActiveMenu(item.name)}
                                className={`flex items-center gap-3 w-full text-left py-2 px-2 rounded text-sm ${
                                  activeMenu === item.name 
                                    ? "text-dsi-contrast-background bg-dsi-background font-semibold" 
                                    : "text-dsi-background hover:text-dsi-selected"
                                }`}
                              >
                                <item.icon className="icon shrink-0" />
                                <span className="truncate">{item.name}</span>
                              </button>
                            </li>
                          ))}
                        </ul>
                      )}
                    </>

                  )}
                </div>
              </nav>
            )}

            {/* BOTTOM ICONS */}
            {isOpen && collapsedWidthPx && (
              <>
                <div
                  className="absolute left-dsi-pad right-dsi-pad border-t-3 border-dsi-outline"
                  style={{ bottom: collapsedWidthPx }}
                />
                <SidebarIconBtn icon={CircleUserRound} className="left-dsi-pad" style={{ bottom: collapsedWidthPx / 2 - 20 }} />
                <SidebarIconBtn icon={Bug} className="right-dsi-pad" style={{ bottom: collapsedWidthPx / 2 - 20 }} />
              </>
            )}
          </aside>

          {/* CONTENT AREA */}
          <main 
            className="flex-1 h-full bg-dsi-background text-dsi-contrast-background overflow-hidden flex flex-col"
            style={{ 
              // Broadcasts your exact math globally to all child components!
              '--cw': collapsedWidthPx ? `${collapsedWidthPx}px` : '80px' 
            } as React.CSSProperties}
          >

            {/* TITLE BAR */}
            <div
              className="border-b-3 border-dsi-outline flex items-center justify-between px-dsi-main shrink-0"
              style={{ height: 'var(--cw)' }}
            >
 
              <h1 className="font-inter text-2xl tracking-wide flex items-center gap-4">
                <span className="flex items-center gap-4">
                  Submissions 
                  <span className="opacity-50 font-light">/</span> 
                  
                  {/* Base Menu (or Previous Menu if drilled down) */}
                  {activeSubmission ? previousMenu : activeMenu}
                </span>
                
                {/* Deep Dive Breadcrumbs - STOPS AT ENTITY NAME NOW */}
                {activeSubmission && (
                  <span className="flex items-center gap-4">
                    <span className="opacity-50 font-light">/</span>
                    <span className="font-bold">{activeSubmission.entity_name}</span>
                  </span>
                )}
              </h1>

              <button onClick={() => setIsDark(!isDark)} className="p-dsi-pad text-dsi-contrast-background hover:text-dsi-selected transition-colors">
                {isDark ? <LightbulbOff className="icon" /> : <Lightbulb className="icon" />}
              </button>
            </div>

            {/* THE DYNAMIC CANVAS AREA */}
            {/* We hand this entire space over to page.tsx to render whatever it wants */}
            <div className="relative flex-1 overflow-hidden">
              {children}
            </div>

          </main>

        </div>
      </body>
    </html>
  );
}