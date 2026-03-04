"use client";

import { useState } from "react";
import { IBM_Plex_Sans, Inter } from "next/font/google";
import { ThemeProvider } from "@/components/ThemeProvider";
import { useTheme } from "next-themes";
import { useDsiStore } from "@/store/dsiStore";
import { 
  Menu, UserCircle, Bug, Search, Filter, 
  Sun, Moon, ChevronRight, ChevronLeft, Inbox, List, BarChart3, ShieldAlert
} from "lucide-react";
import "./globals.css";
import Image from "development/assets/Standard_Generate_logo_and_DSI.svg"; // You will use this for your SVGs

const ibmPlex = IBM_Plex_Sans({ 
  weight: ['400', '500', '600', '700'],
  subsets: ['latin'],
  variable: '--font-ibm'
});

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter'
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  
  // Navigation State
  const [isSubmissionsExpanded, setIsSubmissionsExpanded] = useState(true);
  const { activeMenu, setActiveMenu } = useDsiStore();

  const ThemeToggle = () => {
    const { theme, setTheme } = useTheme();
    return (
      <button onClick={() => setTheme(theme === "dark" ? "light" : "dark")} className="p-2 hover:bg-dsi-sub-bg/20 rounded-full transition-colors text-dsi-main-text">
        {theme === "dark" ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
      </button>
    );
  };

  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${ibmPlex.variable} ${inter.variable} font-sans bg-dsi-main-bg flex h-screen overflow-hidden transition-colors duration-300`}>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
          
          {/* ================= SIDEBAR ================= */}
          {/* Background is mapped to #0B3954 (Dark) / #7A766F (Light) */}
          {/* Right border is mapped to #39D3BA (Dark) / #FFFFFF (Light) */}
          <aside className={`bg-dsi-sidebar-bg flex flex-col transition-all duration-300 ease-in-out border-r border-dsi-outline relative ${isSidebarOpen ? 'w-1/3 max-w-[320px] min-w-[280px]' : 'w-16'}`}>
            
            {/* TOP ROW: Logo and Collapse/Expand Button */}
            <div className="h-20 flex items-center justify-between px-4">
              
              {/* LOGO PLACEHOLDER (Only visible when expanded) */}
              <div className={`overflow-hidden transition-opacity duration-300 ${isSidebarOpen ? 'opacity-100' : 'opacity-0 w-0'}`}>
                {/* TO UPDATE THE LOGO:
                  1. Place your standard and black/white SVGs in the `frontend/public` folder.
                  2. Use the next-themes `useTheme()` hook to check if theme === 'dark'.
                  3. Render: <Image src={theme === 'dark' ? '/Standard_Generate_Logo_and_DSI.svg' : '/BlackWhite_Generate_Logo_and_DSI.svg'} alt="DSI Logo" width={140} height={40} />
                */}
                <div className="h-8 w-32 border border-dashed border-dsi-sidebar-text/50 flex items-center justify-center text-xs text-dsi-sidebar-text rounded">
                  [ SVG Logo ]
                </div>
              </div>

              {/* COLLAPSE / EXPAND BUTTON */}
              {/* Aligned to the far right of the padding container */}
              <button 
                onClick={() => setIsSidebarOpen(!isSidebarOpen)} 
                className="text-dsi-sidebar-text hover:text-dsi-sidebar-active transition-colors p-1 flex-shrink-0"
              >
                {isSidebarOpen ? <ChevronLeft className="w-6 h-6" /> : <ChevronRight className="w-6 h-6" />}
              </button>
            </div>

            {/* MIDDLE ROW: Navigation Hierarchy */}
            {/* Only visible when expanded */}
            <nav className={`flex-grow py-4 overflow-y-auto overflow-x-hidden transition-opacity duration-300 ${isSidebarOpen ? 'opacity-100' : 'opacity-0'}`}>
              {isSidebarOpen && (
                <div className="px-4">
                  {/* Parent Item */}
                  <button 
                    onClick={() => setIsSubmissionsExpanded(!isSubmissionsExpanded)}
                    className="w-full flex items-center justify-between py-2 text-dsi-sidebar-text hover:text-dsi-sidebar-active transition-colors"
                  >
                    <span className="font-semibold uppercase tracking-wider text-sm">Submissions</span>
                  </button>
                  
                  {/* Children Items (Indented) */}
                  {isSubmissionsExpanded && (
                    <ul className="ml-2 pl-4 border-l-2 border-dsi-sidebar-text/20 mt-2 flex flex-col gap-2">
                      {[
                        { name: "Referral Pipeline", icon: ShieldAlert },
                        { name: "Full Pipeline", icon: List },
                        { name: "Performance Metrics", icon: BarChart3 }
                      ].map((item) => (
                        <li key={item.name}>
                          <button
                            onClick={() => setActiveMenu(item.name)}
                            className={`flex items-center gap-3 w-full text-left py-1.5 transition-colors text-sm ${
                              activeMenu === item.name 
                                ? "text-dsi-sidebar-active font-medium" 
                                : "text-dsi-sidebar-text hover:text-dsi-sidebar-active"
                            }`}
                          >
                            <item.icon className="w-4 h-4" />
                            {item.name}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </nav>

            {/* BOTTOM ROW: User, Bug, and Separator Line */}
            {/* Only visible when expanded to satisfy "only an expand button visible" when minimized */}
            <div className={`px-4 pb-6 transition-opacity duration-300 ${isSidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
              {/* Separator Line */}
              {/* Because it is inside a px-4 container, w-full perfectly aligns its edges with the icons below */}
              <div className="h-[1px] w-full bg-dsi-sidebar-text mb-4 opacity-50" />
              
              {/* Icons Container */}
              <div className="flex items-center justify-between text-dsi-sidebar-text">
                <button className="hover:text-dsi-sidebar-active transition-colors outline-none">
                  <UserCircle className="w-7 h-7" />
                </button>
                <button className="hover:text-dsi-sidebar-active transition-colors outline-none">
                  <Bug className="w-6 h-6" />
                </button>
              </div>
            </div>
          </aside>







          {/* ================= MAIN CONTENT AREA ================= */}
          <main className="flex-grow flex flex-col h-full overflow-hidden">
            
            {/* Top Bar */}
            <header className="h-20 flex items-center justify-between px-8 text-dsi-main-text shrink-0">
              
              <div className="flex items-center gap-4">
                {/* Main Section Title (Inter Font) */}
                <h1 className="font-inter text-2xl font-semibold text-dsi-outline">
                  Submissions <span className="text-dsi-main-text font-normal opacity-50 px-2">/</span> {activeMenu}
                </h1>
              </div>

              {/* Top Bar Actions */}
              <div className="flex items-center gap-6">
                <div className="text-sm font-medium opacity-80 hidden md:block">
                  Including all submissions from 25th February 2026
                </div>
                <div className="flex gap-2">
                  <button className="p-2 hover:bg-dsi-sub-bg/20 rounded-full transition-colors"><Filter className="w-5 h-5" /></button>
                  <button className="p-2 hover:bg-dsi-sub-bg/20 rounded-full transition-colors"><Search className="w-5 h-5" /></button>
                  <ThemeToggle />
                </div>
              </div>
            </header>

            {/* Main Sub-section (The Canvas) */}
            <div className="flex-grow px-8 pb-8 overflow-auto bg-dsi-main-bg">
              <div className="bg-dsi-sub-bg text-dsi-sub-text min-h-full rounded-xl border border-dsi-outline/30 shadow-xl p-6">
                {children}
              </div>
            </div>

          </main>

        </ThemeProvider>
      </body>
    </html>
  );
}