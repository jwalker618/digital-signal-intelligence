"use client";

import { useState, useRef, useEffect } from "react";
import { IBM_Plex_Sans, Inter } from "next/font/google";
import {
  PanelRightClose, PanelRightOpen, Lightbulb, LightbulbOff, Bug, CircleUserRound, ArrowLeftToLine, MoreVertical,
  Inbox, FileStack, Shield, FolderKanban, UserStar, Rows4, Bot, TrendingUpDown, Globe, Calculator, ChartNoAxesGantt, FlaskConical, Orbit,
  Building2, FileText, Network, Layers, FileCheck, Clock, RefreshCw, LayoutDashboard, ChevronDown, ChevronRight,
  BookKey, Scale,
} from "lucide-react";

import { useDsiStore } from "@/store/dsiStore";
import { UserProvider } from "@/context/UserContext";
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

// Helper component updated to drop absolute positioning for easier Flexbox usage
const SidebarIconBtn = ({ icon: Icon, onClick, className = "", style }: { icon: any, onClick?: () => void, className?: string, style?: any }) => (
  <button onClick={onClick} className={`text-dsi-background hover:text-dsi-selected transition-colors ${className}`} style={style}>
    <Icon className="icon" />
  </button>
);

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isDark, setIsDark] = useState(false);
  
  const [isSubmissionsExpanded, setIsSubmissionsExpanded] = useState(true);
  const { activeMenu, setActiveMenu, daysFilter, setDaysFilter, previousMenu, activeSubmission, navigateBack, activeCategory, setActiveCategory, expandedCategories, toggleCategory } = useDsiStore();

  const sidebarRef = useRef<HTMLDivElement>(null);
  const [collapsedWidthPx, setCollapsedWidthPx] = useState<number | null>(null);

  // Measure sidebar width perfectly based on the parent DOM
  useEffect(() => {
    if (!sidebarRef.current || !sidebarRef.current.parentElement) return;

    const measure = () => {
      // Get the true pixel width of the whole screen/parent container
      const parentWidth = sidebarRef.current?.parentElement?.getBoundingClientRect().width;
      
      // Mathematically lock the collapsed width to exactly 5% of the usable screen.
      if (parentWidth) {
        setCollapsedWidthPx(parentWidth * 0.05);
      }
    };

    const observer = new ResizeObserver(measure);
    if (sidebarRef.current?.parentElement) {
      observer.observe(sidebarRef.current.parentElement);
    }

    measure();

    return () => observer.disconnect();
  }, []); 

  useEffect(() => {
    const html = document.documentElement;
    if (isDark) html.classList.add("dark");
    else html.classList.remove("dark");
  }, [isDark]);

  return (
    <html lang="en" suppressHydrationWarning> 
      <body className={`${ibmPlex.variable} ${inter.variable} font-ibm h-screen w-screen overflow-hidden`}>
        <UserProvider>
        <div className="relative h-full w-full">

          {/* SIDEBAR — overlays content when expanded */}
          <aside
            ref={sidebarRef}
            className={`
              absolute top-0 left-0 h-full z-30 shrink-0 transition-all duration-300
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
                absolute top-dsi-pad 
                right-dsi-pad p-dsi-pad 
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
                  py-dsi-pad 
                  overflow-y-auto 
                  overflow-x-hidden no-scrollbar"
                style={{ top: collapsedWidthPx, bottom: collapsedWidthPx }} // Added bottom constraint so it doesn't overlap icons
              >
                <div className="px-dsi-pad">
                  
                  {/* --- CONDITIONAL RENDERING --- */}
                  {activeSubmission ? (
                    
                    /* === DRILL-DOWN MODE === */
                    <>
                      <button
                        onClick={navigateBack}
                        className="w-full flex items-center gap-3 py-2
                          text-dsi-background
                          hover:text-dsi-selected
                          mb-2"
                      >
                        <ArrowLeftToLine className="icon shrink-0" />
                        <span className="text-sm tracking-wider truncate">Back to {previousMenu}</span>
                      </button>

                      <ul className="ml-3 pl-dsi-pad flex flex-col gap-1">
                        {/* SUMMARY — top-level, not nested */}
                        <li>
                          <button
                            onClick={() => { setActiveMenu("Summary"); setActiveCategory("Summary"); }}
                            className={`flex items-center gap-3 w-full text-left py-2 px-2 rounded text-sm ${
                              activeMenu === "Summary"
                                ? "text-dsi-contrast-background bg-dsi-background font-semibold"
                                : "text-dsi-background hover:text-dsi-selected"
                            }`}
                          >
                            <BookKey className="icon shrink-0" />
                            <span className="truncate font-semibold tracking-wider normal-case">Summary</span>
                          </button>
                        </li>

                        {/* GROUPED CATEGORIES */}
                        {[
                          {
                            category: "Commercial Terms",
                            icon: Building2,
                            tabs: [
                              { name: "Terms Overview", icon: FileText },
                              { name: "Premium Assembly", icon: Calculator },
                              { name: "Distribution", icon: Network },
                            ],
                          },
                          {
                            category: "Risk Terms",
                            icon: Scale,
                            tabs: [
                              { name: "Deductible Structure", icon: Layers },
                              { name: "Coverage Terms", icon: FileCheck },
                              { name: "SIR & Waiting Periods", icon: Clock },
                              { name: "Aggregate & Reinstatement", icon: RefreshCw },
                            ],
                          },
                          {
                            category: "Technical Assessment",
                            icon: ChartNoAxesGantt,
                            tabs: [
                              { name: "Pricing Anatomy", icon: Calculator },
                              { name: "Risk Assessment", icon: ChartNoAxesGantt },
                              { name: "Loss Assessment", icon: TrendingUpDown },
                              { name: "Exposure Assessment", icon: Globe },
                              { name: "Scenarios", icon: FlaskConical },
                              { name: "Referral Actions", icon: UserStar },
                              { name: "Model Versions", icon: FileStack },
                            ],
                          },
                        ].map((group) => (
                          <li key={group.category}>
                            {/* Category header */}
                            <button
                              onClick={() => toggleCategory(group.category)}
                              className={`flex items-center justify-between gap-3 w-full text-left py-2 px-2 rounded text-sm mt-1 ${
                                activeCategory === group.category
                                  ? "text-dsi-selected"
                                  : "text-dsi-background hover:text-dsi-selected"
                              }`}
                            >
                              <div className="flex items-center gap-3">
                                <group.icon className="icon shrink-0" />
                                <span className="truncate font-semibold tracking-wider normal-case">{group.category}</span>
                              </div>
                              {expandedCategories[group.category] ? (
                                <ChevronDown className="w-3 h-3 shrink-0 opacity-50" />
                              ) : (
                                <ChevronRight className="w-3 h-3 shrink-0 opacity-50" />
                              )}
                            </button>

                            {/* Category tabs */}
                            {expandedCategories[group.category] && (
                              <ul className="ml-3 pl-2 border-l border-dsi-outline/20 flex flex-col gap-0.5 mt-0.5">
                                {group.tabs.map((tab) => (
                                  <li key={tab.name}>
                                    <button
                                      onClick={() => {
                                        setActiveMenu(tab.name);
                                        setActiveCategory(group.category);
                                      }}
                                      className={`flex items-center gap-3 w-full text-left py-1.5 px-2 rounded text-sm ${
                                        activeMenu === tab.name
                                          ? "text-dsi-contrast-background bg-dsi-background font-semibold"
                                          : "text-dsi-background hover:text-dsi-selected"
                                      }`}
                                    >
                                      <tab.icon className="icon shrink-0" />
                                      <span className="truncate">{tab.name}</span>
                                    </button>
                                  </li>
                                ))}
                              </ul>
                            )}
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
                                onClick={() => {
                                  setActiveMenu(item.name)
                                  setIsOpen(false)}
                                }
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

                      {/* WORLD ENGINE — top-level item */}
                      <button
                        onClick={() => {
                          setActiveMenu("World Engine");
                          setIsOpen(false);
                        }}
                        className={`w-full flex items-center gap-3 py-2 mt-4 ${
                          activeMenu === "World Engine"
                            ? "text-dsi-contrast-background bg-dsi-background font-semibold px-2 rounded"
                            : "text-dsi-background hover:text-dsi-selected"
                        }`}
                      >
                        <Orbit className="icon shrink-0" />
                        <span className="text-sm tracking-wider">World Engine</span>
                      </button>
                    </>

                  )}
                </div>
              </nav>
            )}

            {/* BOTTOM ICONS (Now using Flexbox for easy layout!) */}
            {isOpen && collapsedWidthPx && (
              <div 
                className="
                  absolute 
                  left-dsi-pad 
                  right-dsi-pad 
                  border-t-3 border-dsi-outline 
                  flex items-center 
                  justify-between"
                style={{ bottom: 0, height: collapsedWidthPx }}
              >
                {/* Left Side: User Icon */}
                <div className="flex items-center gap-6">
                  <SidebarIconBtn icon={CircleUserRound} />
                </div>
                
                {/* Right Side: Theme Toggle */}
                <div className="flex items-center gap-6">
                  <SidebarIconBtn icon={Bug} />
                  <SidebarIconBtn 
                    icon={isDark ? LightbulbOff : Lightbulb} 
                    onClick={() => setIsDark(!isDark)} 
                  />  
                </div> 
              </div>
            )}
          </aside>

          {/* CONTENT AREA — fixed width, positioned after collapsed sidebar */}
          <main
            className="absolute top-0 right-0 h-full bg-dsi-background text-dsi-contrast-background overflow-hidden flex flex-col transition-none"
            style={{
              left: collapsedWidthPx ? `${collapsedWidthPx}px` : '5%',
              '--cw': collapsedWidthPx ? `${collapsedWidthPx}px` : '80px'
            } as React.CSSProperties}
          >

            {/* TITLE BAR */}
            <div
              className="
                border-b-3 border-dsi-outline 
                flex items-center 
                justify-between 
                px-dsi-main
                whitespace-nowrap border-collapse
                shrink-0"
              style={{ height: 'var(--cw)' }}
            >
              <h1 className="
                font-inter 
                text-2xl 
                tracking-wide 
                flex 
                items-center 
                gap-4">
                <span className="flex items-center gap-4">
                  <span className="opacity-50 font-light">/</span> 
                  {activeSubmission ? previousMenu : activeMenu}
                </span>
                
                {activeSubmission && (
                  <span className="flex items-center gap-4">
                    <span className="opacity-50 font-light">/</span>
                    <span className="font-bold">{activeSubmission.entity_name}</span>
                    <span className="opacity-50 font-light">/</span>
                    <span className="">{activeMenu}</span>
                  </span>
                )}
              </h1>

              {/* DYNAMIC CONTEXT ACTIONS & QUICK ACTION SLOTS */}
              <div className="
                flex items-center 
                gap-2
                px-dsi-main
                ">
                
                {/* 1. Optional Quick Action Slot */}
                {useDsiStore(state => state.pageQuickAction)}

                {/* 2. Optional Ellipsis Menu Trigger */}
                {useDsiStore(state => state.hasPageActions) && (
                  <button 
                    onClick={() => useDsiStore.getState().setPageActionsOpen(true)} 
                    className="p-1.5 rounded text-dsi-contrast-background hover:bg-dsi-outline/10 hover:text-dsi-selected transition-colors"
                    title="Page Actions"
                  >
                    <MoreVertical className="icon" />
                  </button>
                )}
                
              </div>
            </div>

            {/* THE DYNAMIC CANVAS AREA */}
            <div className="relative flex-1 overflow-hidden">
              {children}
            </div>

          </main>

        </div>
        </UserProvider>
      </body>
    </html>
  );
}