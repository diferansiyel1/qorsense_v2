"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
    LayoutDashboard,
    Activity,
    CalendarClock,
    Database,
    FlaskConical,
    FileText,
    Settings
} from "lucide-react";

// Separator Component
const Separator = ({ title }: { title?: string }) => (
    <div className="px-3 py-2 mt-4 mb-1">
        {title ? (
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{title}</h3>
        ) : (
            <div className="h-px bg-slate-gray/30" />
        )}
    </div>
);

const navGroups = [
    {
        title: "Platform",
        items: [
            {
                title: "Dashboard",
                href: "/",
                icon: LayoutDashboard,
            },
            {
                title: "Sensors",
                href: "/sensor-analysis", // Kept original link, renamed title to Sensors per logic
                icon: Activity,
            },
        ]
    },
    {
        title: "Operations",
        items: [
            {
                title: "Maintenance",
                href: "/maintenance",
                icon: CalendarClock,
            },
            {
                title: "Data Sources",
                href: "/data-sources",
                icon: Database,
            },
            {
                title: "Simulation Lab",
                href: "/simulation",
                icon: FlaskConical,
            },
        ]
    },
    {
        title: "Management",
        items: [
            {
                title: "Reports Archive",
                href: "/reports",
                icon: FileText,
            },
            {
                title: "Settings",
                href: "/settings",
                icon: Settings,
            },
        ]
    }
];

export function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className="flex w-64 flex-col bg-[#111a22] p-4 text-white h-screen fixed left-0 top-0 border-r border-slate-gray/50 overflow-y-auto">
            <div className="flex-grow">
                {/* Brand / Logo Section */}
                <div className="flex items-center justify-center py-6 mb-2">
                    <div className="relative w-48 h-20">
                        <Image
                            src="/logo.png"
                            alt="QorSense Logo"
                            fill
                            className="object-contain"
                            priority
                        />
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex flex-col gap-1">
                    {navGroups.map((group, groupIndex) => (
                        <div key={groupIndex}>
                            {/* Logic for separators: Show separator between groups, or logic based on index */}
                            {groupIndex > 0 && <Separator title={group.title} />}

                            {groupIndex === 0 && <div className="mb-2" />}


                            {group.items.map((item) => {
                                const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
                                return (
                                    <Link
                                        key={item.href}
                                        href={item.href}
                                        className={cn(
                                            "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group relative overflow-hidden",
                                            isActive
                                                ? "bg-slate-gray/20 text-[#00ADB5] shadow-[0_0_15px_-3px_rgba(0,173,181,0.3)] border border-[#00ADB5]/20"
                                                : "hover:bg-slate-gray/30 text-gray-400 hover:text-white"
                                        )}
                                    >
                                        {/* Glow effect helper for active state */}
                                        {isActive && (
                                            <div className="absolute inset-0 bg-[#00ADB5]/5 pointer-events-none" />
                                        )}

                                        <item.icon
                                            className={cn(
                                                "w-5 h-5 transition-colors relative z-10",
                                                isActive ? "text-[#00ADB5] drop-shadow-[0_0_8px_rgba(0,173,181,0.5)]" : "text-gray-400 group-hover:text-white"
                                            )}
                                        />
                                        <p className={cn(
                                            "text-sm font-medium leading-normal transition-colors relative z-10",
                                            isActive ? "text-[#00ADB5]" : "text-gray-400 group-hover:text-white"
                                        )}>
                                            {item.title}
                                        </p>
                                    </Link>
                                );
                            })}
                        </div>
                    ))}
                </nav>
            </div>

            {/* User Footer */}
            <div className="border-t border-slate-gray/50 pt-4 mt-4 bg-[#111a22]">
                <div className="flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-slate-gray/50 transition-colors cursor-pointer">
                    <div
                        className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 ring-2 ring-slate-gray"
                        style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuAP2X7ema6KvBnOjwm6HMoL5ZtHOJm-G57mySRhKlNaF_-GDd_KVwbrPXdHnFb5ETJWUf5Sd_puLS4_eLpoySHMEtcB560CRazXtRlv8NyW2Z0c1JLBGyRw1XL2CfPIlK-Y3Q3kG2H5w5U9MP8h46udSvCmz2Gvftw9Dn2TeWknJ0p_6nuGf-SYqGP3LUuNFlOY_Rtowu9s01za2gmBcm_zXA-xDC4MldGgJlccQGvnO2qVhrnk0AiY3wrtSHuYf6QJ3ctBbVlLtwKO")' }}
                    />
                    <div className="flex flex-col">
                        <h1 className="text-white text-sm font-semibold leading-normal">John Doe</h1>
                        <p className="text-[#92adc9] text-xs font-medium leading-normal">System Admin</p>
                    </div>
                </div>
            </div>
        </aside>
    );
}
