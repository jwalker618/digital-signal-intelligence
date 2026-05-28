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
  Briefcase,
  Bug,
  Inbox,
  Lightbulb,
  LightbulbOff,
  Orbit,
  PanelRightClose,
  PanelRightOpen,
  User,
  Wrench,
} from "lucide-react";

import { useDsiStore } from "@/store/dsiStore";
import { useAuthStore } from "@/store/authStore";
import { useThemeStore } from "@/store/themeStore";

import { NavGroup, NavItem, SidebarIconBtn } from "./nav";
import {
  ADMIN_CHILDREN,
  DRILL_DOWN_CATEGORIES,
  PORTAL_BROKER_CHILDREN,
  PORTAL_CLIENT_CHILDREN,
  SUBMISSIONS_CHILDREN,
} from "./navConfig";
import UserMenu from "./userMenu";
import { isPortalPath } from "@/lib/portalPaths";

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
  const userRole = useAuthStore((s) => s.user?.role ?? null);
  const canViewSubmissions = hasPermission("assessment:read");
  const canViewWorldEngine = hasPermission("world_engine:view");
  const canViewAnyAdmin = ADMIN_CHILDREN.some((i) => hasPermission(i.permission));

  // v8 Phase 8: portal users see a tailored nav. The role drives which
  // children render; per-leaf permission still applies for safety.
  const isBroker = userRole === "BROKER";
  const isClient = userRole === "CLIENT";
  const isPortalUser = isBroker || isClient;
  const portalChildren = isBroker
    ? PORTAL_BROKER_CHILDREN
    : isClient
    ? PORTAL_CLIENT_CHILDREN
    : [];
  const visiblePortalChildren = portalChildren.filter((i) =>
    hasPermission(i.permission),
  );

  const [isSubmissionsExpanded, setIsSubmissionsExpanded] = useState(true);
  const [isAdminExpanded, setIsAdminExpanded] = useState(false);
  const [isPortalExpanded, setIsPortalExpanded] = useState(true);

  return (
    <aside
      ref={sidebarRef}
      className={`
        absolute top-0 left-0 h-full z-1000 shrink-0 transition-all duration-300
        bg-generate-dark-background
        text-generate-text-placeholder
        border-r-3 border-generate-text-outline
        ${isOpen ? "w-[50%]" : "w-[5%]"}
      `}
    >
      {isOpen && (
        <img
        alt="DSI Logo"  
        src={
            isDark
              ? "/Standard_Generate_Logo_and_Product.svg"
              : "/BlackWhite_Generate_Logo_and_Product.svg"
          }
          className="absolute top-generate-pad left-generate-pad h-12 w-auto object-contain"
        />
      )}

      <button
        onClick={onToggleOpen}
        className={`absolute top-generate-pad p-generate-pad ${
                isOpen ? "right-1.5 " : "right-generate-pad "
              }`}
        >
        {isOpen ? (
          <PanelRightOpen className="generate-app-icon" />
        ) : (
          <PanelRightClose className="generate-app-icon" />
        )}
      </button>

      {/* NAVIGATION */}
      {isOpen && (
        <nav
          className="
            absolute left-generate-indent right-1.5 
            overflow-y-auto overflow-x-hidden no-scrollbar
            pt-12 gap-2"
          style={{
            top: collapsedWidthPx ?? 64,
            bottom: collapsedWidthPx ?? 64,
          }}
        >
          <div className="px-generate-pad">
            {activeSubmission && !isPortalPath(pathname) ? (
              /* ═══ DRILL-DOWN MODE (carrier paths only) ═══
                 Portal paths use top-level mode even when a portal
                 page has a notion of "active submission" -- the
                 carrier drill-down chrome (Back to Referrals, etc.)
                 doesn't apply to the portal surface. */
              <>
                
                <button
                  onClick={navigateBack}
                  className="w-full flex group items-center gap-1.5 pl-generate-pad pt-3 pb-3 border-b-1 border-generate-text-outline"
                >
                  <ArrowLeftToLine className="generate-app-icon group-hover:text-generate-text-input group-hover:font-bold" />
                  <span className="group-hover:text-generate-text-input group-hover:font-bold">
                    Back to {previousMenu}
                  </span>
                </button>


                <ul className="flex flex-col">
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
                {/* v8 Phase 8: portal nav -- shown when the user is BROKER
                    or CLIENT. Sits above carrier-side sections. */}
                {isPortalUser && visiblePortalChildren.length > 0 && (
                  <ul>
                    <NavGroup
                      icon={isBroker ? Briefcase : User}
                      label={isBroker ? "Broker Portal" : "Client Portal"}
                      isExpanded={isPortalExpanded}
                      onToggle={() => setIsPortalExpanded(!isPortalExpanded)}
                    >
                      {visiblePortalChildren.map((item) => (
                        <li key={item.name}>
                          <NavItem
                            icon={item.icon}
                            label={item.name}
                            isActive={
                              pathname === item.href ||
                              // Don't let a parent href like "/broker"
                              // claim active state when a deeper page
                              // (e.g. /broker/carriers) is the actual match.
                              (item.href !== "/broker" && item.href !== "/client"
                                && !!pathname?.startsWith(item.href + "/"))
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
                    </NavGroup>
                  </ul>
                )}

                {canViewSubmissions && (
                  <ul>
                    <NavGroup
                      icon={Inbox}
                      label="Submissions"
                      isExpanded={isSubmissionsExpanded}
                      onToggle={() =>
                        setIsSubmissionsExpanded(!isSubmissionsExpanded)
                      }
                    >
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
                    </NavGroup>
                  </ul>
                )}

                {canViewWorldEngine && (
                  <div>
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
                  <ul>
                    <NavGroup
                      icon={Wrench}
                      label="Admin"
                      isExpanded={isAdminExpanded}
                      onToggle={() => setIsAdminExpanded(!isAdminExpanded)}
                    >
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
                    </NavGroup>
                  </ul>
                )}
              </>
            )}
          </div>
        </nav>
      )}

      {/* BOTTOM ICONS */}
      {isOpen && (
        <div
          className="
            absolute left-generate-pad right-generate-pad 
            pl-generate-pad pr-generate-pad
            border-t-3 border-generate-text-outline
            flex items-center justify-between"
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
