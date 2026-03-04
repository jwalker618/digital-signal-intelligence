"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, TrendingUp, ShieldCheck, DollarSign } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
const DECISION_COLORS = { 'APPROVE': '#10b981', 'REFER': '#f59e0b', 'DECLINE': '#ef4444' };

export default function PortfolioAnalytics() {
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/v1/portfolio-analytics");
        if (res.ok) {
          const json = await res.json();
          setData(json);
        }
      } catch (error) {
        console.error("Failed to fetch analytics", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  if (isLoading || !data) {
    return <div className="flex h-full min-h-[500px] items-center justify-center"><Loader2 className="animate-spin text-blue-500 w-10 h-10" /></div>;
  }

  return (
    <div className="flex flex-col gap-6 h-full min-h-[600px] overflow-y-auto pr-2">
      
      {/* Top KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-slate-900 border-slate-800 text-white">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium text-slate-400">Total Pipeline Premium</CardTitle>
            <DollarSign className="w-4 h-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-mono text-slate-100">${data.kpis.total_premium.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-900 border-slate-800 text-white">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium text-slate-400">Active Submissions</CardTitle>
            <TrendingUp className="w-4 h-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-mono text-slate-100">{data.kpis.total_submissions}</div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900 border-slate-800 text-white">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium text-slate-400">Straight-Through Processing</CardTitle>
            <ShieldCheck className="w-4 h-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-mono text-slate-100">{data.kpis.approval_rate.toFixed(1)}%</div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-grow">
        
        {/* Exposure by Coverage */}
        <Card className="bg-slate-900 border-slate-800 text-white flex flex-col">
          <CardHeader>
            <CardTitle className="text-lg">Premium Exposure by Line of Business</CardTitle>
          </CardHeader>
          <CardContent className="flex-grow min-h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.coverages} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <XAxis type="number" tickFormatter={(value) => `$${value / 1000}k`} stroke="#475569" />
                <YAxis dataKey="name" type="category" width={100} stroke="#475569" />
                <Tooltip cursor={{ fill: '#1e293b' }} contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f8fafc' }} formatter={(value: number) => `$${value.toLocaleString()}`} />
                <Bar dataKey="premium" fill="#3b82f6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* AI Decision Breakdown */}
        <Card className="bg-slate-900 border-slate-800 text-white flex flex-col">
          <CardHeader>
            <CardTitle className="text-lg">AI Decision Matrix</CardTitle>
          </CardHeader>
          <CardContent className="flex-grow min-h-[300px] flex items-center justify-center relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={data.decisions} cx="50%" cy="50%" innerRadius={80} outerRadius={120} paddingAngle={5} dataKey="value" stroke="none">
                  {data.decisions.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={DECISION_COLORS[entry.name as keyof typeof DECISION_COLORS] || COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f8fafc' }} />
              </PieChart>
            </ResponsiveContainer>
            {/* Custom Legend */}
            <div className="absolute bottom-4 flex gap-4 text-sm">
              {data.decisions.map((entry: any, idx: number) => (
                <div key={idx} className="flex items-center gap-2 text-slate-300">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: DECISION_COLORS[entry.name as keyof typeof DECISION_COLORS] || COLORS[idx % COLORS.length] }}></div>
                  {entry.name} ({entry.value})
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}