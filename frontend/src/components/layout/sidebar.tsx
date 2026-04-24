"use client";

/**
 * Sidebar — the app shell's left navigation.
 *
 * Two modes, driven by whether there's an active submission:
 *   • Top-level: Submissions expander, World Engine, Admin expander
 *     (System Health / Configs / Users & Roles / Audit Log / Loss
 *     Register / Recalibration).
 *   • Drill-down: Summary leaf + three named categories (Commercial,
 *     Risk Terms, Technical Assessment) each with its own tab list.
 *
 * Width + measurement stays in layout.tsx (the main area reads the same
 * collapsedWidthPx for its left offset); the sidebar only renders.
 */

import { useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  ArrowLeftToLine,
  BookKey,
  Bug,
  Inbox,
  Lightbulb,
  LightbulbOff,
  Orbit,
  PanelRightClose,
  PanelRightOpen,
  Wrench,
} from "lucide-react";

import { useDsiStore } from "@/store/dsiStore";
import { useAuthStore } from "@/store/authStore";
import { useThemeStore } from "@/store/themeStore";

import { NavGroup, NavItem, SidebarIconBtn } from "./nav";
import {
  ADMIN_CHILDREN,
  DRILL_DOWN_CATEGORIES,
  SUBMISSIONS_CHILDREN,
} from "./navConfig";
import UserMenu from "./userMenu";

interface SidebarProps {
  isOpen: boolean;
  onToggleOpen: () => void;
  /** Bottom-row height — matches the main area's title bar height. */
  collapsedWidthPx: number | null;
  sidebarRef: React.Ref<HTMLElement>;
}

export default function Sidebar({
  isOpen,
  onToggleOpen,
  collapsedWidthPx,
  sidebarRef,
}: SidebarProps) {
  const router = useRouter();
  const pathname = usePathname();

  const isDark = useThemeStore((s) => s.isDark);
  const toggleDark = useThemeStore((s) => s.toggleDark);

  const {
    activeMenu,
    setActiveMenu,
    activeSubmission,
    previousMenu,
    navigateBack,
    activeCategory,
    setActiveCategory,
    expandedCategories,
    toggleCategory,
    clearSubmissionContext,
  } = useDsiStore();

  const hasPermission = useAuthStore((s) => s.hasPermission);
  const canViewSubmissions = hasPermission("assessment:read");
  const canViewWorldEngine = hasPermission("world_engine:view");
  const canViewAnyAdmin = ADMIN_CHILDREN.some((i) => hasPermission(i.permission));

  const [isSubmissionsExpanded, setIsSubmissionsExpanded] = useState(true);
  const [isAdminExpanded, setIsAdminExpanded] = useState(false);

  return (
    <aside
      ref={sidebarRef}
      className={`
        absolute top-0 left-0 h-full z-1000 shrink-0 transition-all duration-300
        bg-generate-contrast-background
        text-generate-background
        border-r-3 border-generate-outline
        ${isOpen ? "w-[50%]" : "w-[5%]"}
      `}
    >
      {isOpen && (
        <img
          src={
            isDark
              ? "/Standard_Generate_Logo_and_DSI.svg"
              : "/BlackWhite_Generate_Logo_and_DSI.svg"
          }
          className="absolute top-generate-pad left-generate-pad h-12 w-auto object-contain"
          alt="DSI Logo"
        />
      )}

      <button
        onClick={onToggleOpen}
        className="absolute top-generate-pad right-generate-pad p-generate-pad text-generate-background hover:text-generate-selected"
      >
        {isOpen ? (
          <PanelRightOpen className="icon" />
        ) : (
          <PanelRightClose className="icon" />
        )}
      </button>

      {/* NAVIGATION */}
      {isOpen && (
        <nav
          className="absolute left-generate-indent right-0 py-generate-pad overflow-y-auto overflow-x-hidden no-scrollbar"
          style={{
            top: collapsedWidthPx ?? 64,
            bottom: collapsedWidthPx ?? 64,
          }}
        >
          <div className="px-generate-pad">
            {activeSubmission ? (
              /* ═══ DRILL-DOWN MODE ═══ */
              <>
                <button
                  onClick={navigateBack}
                  className="w-full flex items-center gap-3 py-2 text-generate-background hover:text-generate-selected mb-2"
                >
                  <ArrowLeftToLine className="icon shrink-0" />
                  <span className="text-sm tracking-wider truncate">
                    Back to {previousMenu}
                  </span>
                </button>

                <ul className="ml-3 pl-generate-pad flex flex-col gap-1">
                  <li>
                    <NavItem
                      icon={BookKey}
                      label="Summary"
                      isActive={activeMenu === "Summary"}
                      onClick={() => {
                        setActiveMenu("Summary");
                        setActiveCategory("Summary");
                      }}
                    />
                  </li>

                  {DRILL_DOWN_CATEGORIES.map((group) => (
                    <NavGroup
                      key={group.category}
                      icon={group.icon}
                      label={group.category}
                      isActive={activeCategory === group.category}
                      isExpanded={!!expandedCategories[group.category]}
                      onToggle={() => toggleCategory(group.category)}
                    >
                      {group.tabs.map((tab) => (
                        <li key={tab.name}>
                          <NavItem
                            icon={tab.icon}
                            label={tab.name}
                            isActive={activeMenu === tab.name}
                            onClick={() => {
                              setActiveMenu(tab.name);
                              setActiveCategory(group.category);
                            }}
                          />
                        </li>
                      ))}
                    </NavGroup>
                  ))}
                </ul>
              </>
            ) : (
              /* ═══ TOP-LEVEL MODE ═══ */
              <>
                {canViewSubmissions && (
                  <>
                    <button
                      onClick={() =>
                        setIsSubmissionsExpanded(!isSubmissionsExpanded)
                      }
                      className="w-full flex items-center justify-between py-2 text-generate-background hover:text-generate-selected"
                    >
                      <div className="flex items-center gap-3">
                        <Inbox className="icon shrink-0" />
                        <span className="text-sm tracking-wider">
                          Submissions
                        </span>
                      </div>
                    </button>

                    {isSubmissionsExpanded && (
                      <ul className="ml-3 pl-generate-pad border-l-3 border-generate-outline/20 mt-2 flex flex-col gap-1">
                        {SUBMISSIONS_CHILDREN.map((item) => (
                          <li key={item.name}>
                            <NavItem
                              icon={item.icon}
                              label={item.name}
                              isActive={activeMenu === item.name}
                              onClick={() => {
                                clearSubmissionContext();
                                setActiveMenu(item.name);
                                onToggleOpen();
                                router.push("/");
                              }}
                            />
                          </li>
                        ))}
                      </ul>
                    )}
                  </>
                )}

                {canViewWorldEngine && (
                  <div className="mt-4">
                    <NavItem
                      icon={Orbit}
                      label="World Engine"
                      isActive={!!pathname?.startsWith("/world-engine")}
                      onClick={() => {
                        clearSubmissionContext();
                        setActiveMenu("World Engine");
                        onToggleOpen();
                        router.push("/world-engine");
                      }}
                    />
                  </div>
                )}

                {canViewAnyAdmin && (
                  <div className="mt-4">
                    <button
                      onClick={() => setIsAdminExpanded(!isAdminExpanded)}
                      className="w-full flex items-center justify-between py-2 text-generate-background hover:text-generate-selected"
                    >
                      <div className="flex items-center gap-3">
                        <Wrench className="icon shrink-0" />
                        <span className="text-sm tracking-wider">Admin</span>
                      </div>
                    </button>

                    {isAdminExpanded && (
                      <ul className="ml-3 pl-generate-pad border-l-3 border-generate-outline/20 mt-2 flex flex-col gap-1">
                        {ADMIN_CHILDREN.filter((item) =>
                          hasPermission(item.permission),
                        ).map((item) => (
                          <li key={item.name}>
                            <NavItem
                              icon={item.icon}
                              label={item.name}
                              isActive={
                                pathname === item.href ||
                                (item.href !== "/admin" &&
                                  !!pathname?.startsWith(item.href + "/"))
                              }
                              onClick={() => {
                                clearSubmissionContext();
                                setActiveMenu(item.name);
                                onToggleOpen();
                                router.push(item.href);
                              }}
                            />
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </nav>
      )}

      {/* BOTTOM ICONS */}
      {isOpen && (
        <div
          className="absolute left-generate-pad right-generate-pad border-t-3 border-generate-outline flex items-center justify-between"
          style={{ bottom: 0, height: collapsedWidthPx ?? 64 }}
        >
          <UserMenu />

          <div className="flex items-center gap-6">
            <SidebarIconBtn icon={Bug} />
            <SidebarIconBtn
              icon={isDark ? LightbulbOff : Lightbulb}
              onClick={toggleDark}
            />
          </div>
        </div>
      )}
    </aside>
  );
}
