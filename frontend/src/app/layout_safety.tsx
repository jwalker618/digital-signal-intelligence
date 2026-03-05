"use client";

import { useState, useRef, useEffect } from "react";
import { IBM_Plex_Sans, Inter } from "next/font/google";
import { 
  PanelRightClose, PanelRightOpen, Lightbulb, LightbulbOff, Bug, CircleUserRound,  
  Menu, Search, Filter, Inbox, List, BarChart3, ShieldAlert, Calendar
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
  const [isOpen, setIsOpen] = useState(true);
  const [isDark, setIsDark] = useState(false);
  
  const [isSubmissionsExpanded, setIsSubmissionsExpanded] = useState(true);
  const { activeMenu, setActiveMenu, daysFilter, setDaysFilter } = useDsiStore();

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
                  overflow-x-hidden"
                style={{ top: collapsedWidthPx }}
              >
                <div className="px-dsi-pad">
                  <button 
                    onClick={() => setIsSubmissionsExpanded(!isSubmissionsExpanded)}
                    className="w-full flex items-center justify-between py-2 text-dsi-background hover:text-dsi-selected"
                  >
                    <div className="flex items-center gap-3">
                      <Inbox className="icon" />
                      <span className="text-sm tracking-wider">Submissions</span>
                    </div>
                  </button>
                  
                  {isSubmissionsExpanded && (
                    <ul className="ml-3 pl-dsi-pad border-l-3 border-dsi-outline/20 mt-2 flex flex-col gap-1">
                      {[
                        { name: "Referral Pipeline", icon: ShieldAlert },
                        { name: "Full Pipeline", icon: List },
                        { name: "Performance Metrics", icon: BarChart3 }
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
                            <item.icon className="icon" />
                            {item.name}
                          </button>
                        </li>
                      ))}
                    </ul>
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
          <main className="
            flex-1 h-full 
            bg-dsi-background 
            text-dsi-contrast-background 
            overflow-hidden flex flex-col"
          >

            {/* TITLE BAR */}
            <div
              className="
                border-b-3 border-dsi-outline shrink-0
                flex items-center justify-between px-dsi-main "
              style={{
                height: collapsedWidthPx ? `${collapsedWidthPx}px` : "auto",
                minHeight: collapsedWidthPx ? `${collapsedWidthPx}px` : "auto",
                maxHeight: collapsedWidthPx ? `${collapsedWidthPx}px` : "auto",
              }}
            >
              <h1 className="font-inter text-2xl tracking-wide">
                Submissions <span>/</span> {activeMenu}
              </h1>

              <button onClick={() => setIsDark(!isDark)} className="p-dsi-pad text-dsi-contrast-background hover:text-dsi-selected">
                {isDark ? <LightbulbOff className="icon" /> : <Lightbulb className="icon" />}
              </button>
            </div>

            {/* ANALYSIS SECTION */}
            <div className="relative flex-1 overflow-hidden">

              <div
                className="
                  absolute left-dsi-gap right-dsi-gap 
                  overflow-auto"
                style={{
                  top: collapsedWidthPx ? `${collapsedWidthPx}px` : "0px",
                  bottom: collapsedWidthPx ? `${collapsedWidthPx}px` : "0px",
                }}
              >
                <div className="
                  bg-dsi-analysis 
                  text-dsi-contrast-analysis 
                  min-h-full 
                  p-dsi-pad">
                   {children}
                </div>
              </div>

              {/* Bottom context area */}
              <div
                className="
                  absolute bottom-0 left-dsi-gap right-dsi-gap
                  overflow-auto 
                  text-dsi-contrast-background"
                style={{ 
                  height: collapsedWidthPx ? `${collapsedWidthPx}px` : "0px" 
                }}
              >

                {/* Interactive Date Filter */}
                <div className="pt-dsi-pad flex items-center gap-2 relative">
                  <Calendar className="icon" />
                  <select 
                    value={daysFilter} 
                    onChange={(e) => setDaysFilter(Number(e.target.value))}
                    className="icon"
                  >
                    <option value={7}>Last 7 Days</option>
                    <option value={30}>Last 30 Days</option>
                    <option value={90}>Last 90 Days</option>
                    <option value={365}>Last 1 Year</option>
                  </select>
                  
                  {/* Dynamic Description */}
                  <p className="font-medium text-sm tracking-wide">
                    Showing submissions updated within the last <span className="font-bold">{daysFilter} days</span> (or status = DRAFT).
                  </p>

                </div>
              </div>

            </div>

          </main>
        </div>
      </body>
    </html>
  );
}